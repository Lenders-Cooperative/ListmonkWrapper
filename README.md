# ListmonkWrapper

Lightweight, typed Python wrapper for the **Listmonk v5.1.0+ and v6.0.0+ REST API**, using HTTP
Basic Authentication.

**Note**: This repository includes a Docker-based **test environment** for running integration tests
against Listmonk. The Docker setup is designed specifically for testing the `ListMonkClient` and is
not intended for production use. In production environments, you'll need to configure your own
Listmonk instance and manage API credentials through your deployment's standard mechanisms.

## Test Environment

The repository includes a complete integration-test environment using Docker:

- Postgres (persistent via Docker volume)
- Listmonk (ephemeral test instance)
- Automatic schema installation and admin user creation
- Automatic API user and token generation via `LISTMONK_ADMIN_API_USER`
- API token automatically captured and made available to tests
- Seamless pytest integration with auto-starting containers

**Important**: The `tmp/` directory containing API credentials is only created in this test
environment. In production, you'll need to obtain API credentials from your Listmonk instance
through your normal deployment process (e.g., environment variables, secrets management, etc.).

---

## Installation

Install dependencies (including dev + test groups):

```
poetry install --with dev,test
```

Install pre-commit hooks (optional but recommended):

```
make setup
```

This will install git hooks that automatically run code formatting and linting checks before each commit.

Create a `.env` file in the project root:

```
LISTMONK_HOST=http://localhost
LISTMONK_PORT=9000

LISTMONK_ADMIN_USER=admin
LISTMONK_ADMIN_PASSWORD=admin123
LISTMONK_ADMIN_API_USER=api_user

POSTGRES_DB=listmonk
POSTGRES_USER=listmonk
POSTGRES_PASSWORD=listmonk
POSTGRES_PORT=9432

# Optional: SMTP from email address (defaults to noreply@test.local)
LISTMONK_SMTP_FROM_EMAIL=noreply@test.local
```

**Note**: The Docker setup includes MailHog, a fake SMTP server for testing email functionality:
- SMTP server: `localhost:1025`
- Web UI: `http://localhost:8025` (view captured emails)

---

## Code Structure

The codebase is organized using a mixin pattern for maintainability and clarity:

```
src/listmonk_wrapper/
├── __init__.py          # Re-exports ListMonkClient
├── client.py            # Main ListMonkClient class (composes all mixins)
├── _api_handler.py      # Core HTTP handling and authentication
├── _subscribers.py      # SubscriberMixin - all subscriber methods
├── _lists.py            # ListsMixin - all list methods
├── _templates.py        # TemplatesMixin - all template methods
├── _import.py           # ImportMixin - all import methods
├── _campaigns.py        # CampaignsMixin - all campaign methods
├── _media.py            # MediaMixin - all media upload methods
├── _transactional.py   # TransactionalMixin - transactional email methods
└── _bounces.py          # BouncesMixin - bounce record management methods
```

Each mixin module contains methods for a specific API endpoint group, making the codebase:
- **Modular**: Easy to locate and modify endpoint-specific code
- **Maintainable**: Each file focuses on a single responsibility
- **Extensible**: Simple to add new endpoints by creating new mixin modules

The `ListMonkClient` class inherits from all mixins, providing a unified interface while keeping the implementation organized.

---

## Make Commands

```
make test
```
Runs pytest and automatically starts Listmonk/Postgres.

```
make lint
```
Runs pylint via the configured Makefile target.

```
make fmt
```
Applies `black` + `isort`.

```
make setup
```
Makes helper scripts in `bin/` executable and installs pre-commit hooks.

```
make pre-commit-install
```
Install pre-commit hooks manually (if not done via `make setup`).

```
make pre-commit-run
```
Run pre-commit hooks on all files (useful for CI or manual checks).

```
make listmonk-up
make listmonk-down
```
Manually start or stop the Listmonk/Postgres docker stack.

---

## Running Tests

Integration tests require a live Listmonk instance. The test environment uses Docker to spin up
a temporary Listmonk instance for testing purposes only.

When running:

```
make test
```

The test process will automatically:

1. Start the docker-compose stack using `docker-compose.listmonk.yml`
2. Wait for Postgres and Listmonk to become healthy
3. Create admin user and API user during installation
4. Capture the API token from installation logs
5. Export API credentials for use in tests (saved to `tmp/` directory)
6. Run the full test suite
7. Tear everything down afterward

Tests authenticate using **HTTP Basic Auth** with the automatically generated API credentials.

**Note**: This Docker setup is only for testing. In production, you'll connect to your own Listmonk
instance and provide credentials through environment variables or your application's configuration
management system.

---

## Authentication Model (Listmonk v5.1.0+ and v6.0.0+)

Listmonk v5.1.0+ and v6.0.0+ use HTTP Basic Authentication for API access. The setup process
automatically creates and captures API credentials:

### API User and Token Creation

1. **During Installation**: When you set `LISTMONK_ADMIN_API_USER` in your `.env` file, Listmonk
   automatically creates an API user with superadmin permissions during the `--install` step.

2. **Token Capture Process**:
   - The `docker-compose.listmonk.yml` runs `./listmonk --install --idempotent --yes`
   - Installation output (including stderr) is captured via `tee` to `/tmp/listmonk_install.log`
   - The API token is printed to stderr in the format: `export LISTMONK_ADMIN_API_TOKEN="<token>"`
   - A `grep` + `sed` command extracts just the token value and saves it to `/tmp/api_token.txt`
   - The `bin/start-listmonk` script reads this token file and:
     - Exports `LISTMONK_API_USER` and `LISTMONK_API_TOKEN` as environment variables
     - Creates `tmp/listmonk_api_creds.sh` with export statements for sourcing

3. **Automatic Usage**: The test fixtures (`tests/conftest.py`) automatically load these credentials
   from `tmp/listmonk_api_creds.sh`, so tests work without manual configuration.

### Using Credentials in Tests

In the test environment, credentials are automatically loaded from `tmp/listmonk_api_creds.sh` by
the test fixtures. If you need to use them manually in test scripts:

```python
from listmonk_wrapper import ListMonkClient
import os

# Load credentials from the generated file (test environment only)
with open('tmp/listmonk_api_creds.sh') as f:
    for line in f:
        if line.startswith('export '):
            key, value = line.replace('export ', '').strip().split('=', 1)
            os.environ[key] = value.strip("'\"\"")

# Create client with API credentials
client = ListMonkClient(
    host="http://localhost",
    port=9000,
    username=os.getenv("LISTMONK_API_USER"),  # e.g., "api_user"
    password=os.getenv("LISTMONK_API_TOKEN"),  # The captured token
)
```

**Note**: This approach only works in the test environment where `tmp/listmonk_api_creds.sh` exists.
In production, provide credentials through your application's standard configuration mechanism.

The client uses HTTP Basic Auth with the API credentials for all requests.

---

## Usage Example

### Production Usage

```python
from listmonk_wrapper import ListMonkClient
import os

# In production, get credentials from environment variables or your config management
client = ListMonkClient(
    host=os.getenv("LISTMONK_HOST", "https://your-listmonk-instance.com"),
    port=int(os.getenv("LISTMONK_PORT", "443")),
    username=os.getenv("LISTMONK_API_USER"),  # From your deployment config
    password=os.getenv("LISTMONK_API_TOKEN"),  # From your deployment config
)

# Fetch campaigns (returns {"data": {"results": [...], "total": int, "page": int}})
campaigns = client.get_campaigns()
print(f"Found {campaigns['data']['total']} campaigns")

# Create a subscriber
subscriber = client.create_subscriber(
    email="test@example.com",
    name="Test User",
)
print(f"Created subscriber with ID: {subscriber['data']['id']}")

# Query subscribers by email (SQL-like query syntax)
results = client.query_subscribers(query="email LIKE '%example%'")
print(f"Found {results['data']['total']} subscribers matching 'example'")

# Query subscribers by name
results = client.query_subscribers(query="name='Test User'")

# Query with pagination
results = client.query_subscribers(
    query="status='enabled'",
    page=1,
    per_page=20
)

# Send transactional email
template = client.create_template(
    name="Order Confirmation",
    body="<html>Hello {{ .Subscriber.Name }}, your order {{ .Tx.Data.order_id }} is confirmed!</html>",
    template_type="tx",
    subject="Order Confirmation"
)
client.send_transactional(
    template_id=template["data"]["id"],
    subscriber_email="customer@example.com",
    data={"order_id": "12345", "date": "2024-01-15"}
)

# Get bounce records
bounces = client.get_bounces(page=1, per_page=10, order_by="created_at", order="desc")
print(f"Found {bounces['data']['total']} bounce records")

# Delete specific bounces
client.delete_bounces(bounce_ids=[1, 2, 3])
```

### Test Environment Usage

In the test environment, credentials are automatically available from `tmp/listmonk_api_creds.sh`:

```python
from listmonk_wrapper import ListMonkClient
import os

# Load credentials from test environment (only works when Docker containers are running)
with open('tmp/listmonk_api_creds.sh') as f:
    for line in f:
        if line.startswith('export '):
            key, value = line.replace('export ', '').strip().split('=', 1)
            os.environ[key] = value.strip("'\"\"")

client = ListMonkClient(
    host="http://localhost",
    port=9000,
    username=os.getenv("LISTMONK_API_USER", "api_user"),
    password=os.getenv("LISTMONK_API_TOKEN"),
)
# ... rest of usage is the same
```

---

## API Coverage

The client provides comprehensive coverage of the Listmonk v5.1.0+ API, with v6.0.0 feature
support where available:

### Subscribers
- **CRUD Operations**: `get_subscriber()`, `create_subscriber()`, `update_subscriber()`, `delete_subscriber()`
- **Querying**: `query_subscribers()` with SQL-like filters, pagination, sorting, and list filtering
- **Advanced Operations**:
  - `export_subscriber()` - Export subscriber data
  - `get_subscriber_bounces()` - Get bounce records
  - `send_optin_email()` - Send opt-in confirmation email
  - `create_public_subscription()` - Public subscription endpoint (no auth required)
  - `modify_subscriber_lists()` - Bulk modify list memberships
  - `blocklist_subscriber()` - Blocklist single subscriber
  - `blocklist_subscribers()` - Blocklist multiple subscribers
  - `blocklist_subscribers_by_query()` - Blocklist by SQL query
  - `delete_subscribers()` - Bulk delete by IDs
  - `delete_subscribers_by_query()` - Delete by SQL query
  - `delete_subscriber_bounces()` - Delete bounce records

### Lists
- **CRUD Operations**: `get_lists()`, `get_list()`, `create_list()`, `update_list()`, `delete_list()`
- **Querying**: `get_lists()` with filtering (status, tags, query), sorting, and pagination
- **Public Lists**: `get_public_lists()` - Unauthenticated endpoint for subscription forms
- **Bulk Operations**: `delete_lists()` - Delete multiple lists by IDs or query

### Templates
- **CRUD Operations**: `get_templates()`, `get_template()`, `create_template()`, `update_template()`, `delete_template()`
- **Template Types**: Supports `campaign`, `campaign_visual`, and `tx` (transactional) templates
- **Advanced**: `set_default_template()` - Set a template as default

### Campaigns
- **Operations**: `get_campaigns()`, `create_campaign()`, `update_campaign()`, `run_campaign()`
- **v6.0.0+**:
  - `attribs` support on campaign create/update payloads
  - `delete_campaign()` and `delete_campaigns()` (bulk deletion by IDs or query/all)

### Media
- **Operations**: `get_media()`, `get_media_file()`, `upload_media()`, `delete_media()`
- **Supported Types**: Images (jpg, png, gif, svg) and PDFs (configured via `upload.extensions`)

### Transactional Messages
- **Sending**: `send_transactional()` - Send transactional emails to subscribers
- **Modes**:
  - `"default"` - Recipients must exist as subscribers
  - `"fallback"` - Looks up subscribers, sends even if not found
- **Features**:
  - Single or multiple recipients (by email or ID)
  - Custom `from_email`, `subject`, `data` (template variables), `headers`
  - File attachments support
  - Content types: `html`, `markdown`, `plain`
- **Version Behavior**:
  - v5.1.0: `"external"` mode is not supported due to a Listmonk bug
  - v6.0.0+: `"external"` mode is supported (with recipient validation)

### Bounces
- **Retrieval**: `get_bounces()` - Get bounce records with filtering, pagination, and sorting
  - Filter by `campaign_id`, `source`
  - Sort by `email`, `campaign_name`, `source`, `created_at`
  - Pagination support
- **Deletion**:
  - `delete_bounces()` - Delete all bounces or multiple specific bounces
  - `delete_bounce()` - Delete a single bounce by ID

### Import
- **Status & Logs**: `get_import_status()`, `get_import_logs()`
- **Import**: `import_subscribers()` - Upload CSV/ZIP for bulk subscriber import
- **Management**: `delete_import()` - Stop and remove ongoing import
- **v6.0.0+**: granular overwrite flags for `import_subscribers()`:
  - `overwrite_userinfo`, `overwrite_subscription_status`

---

## Test Suite

The test suite exercises:

- **Subscriber Operations**: CRUD, queries, blocklisting, bulk operations, list management, bounces, opt-in emails
- **List Operations**: CRUD, filtering, sorting, pagination, public lists, bulk deletion
- **Template Operations**: CRUD, default template setting
- **Campaign Operations**: Creation, updates, running campaigns
- **Media Operations**: Upload, retrieval, deletion of media files
- **Transactional Operations**: Sending transactional emails (single/multiple recipients, attachments, optional parameters)
- **Bounce Operations**: Retrieving bounce records, deleting bounces (all, multiple, single)
- **Import Operations**: Status checking, log retrieval, import management
- **Negative Tests**: 404 / invalid IDs, error handling, validation errors
- **Performance**: Query performance sanity checks

**Note**: Some features may be skipped if not supported by the Listmonk version:
- Template creation (may have server errors in some environments)
- Bulk list deletion (may fall back to individual deletion)
- v6-only tests are gated by `/api/config` version checks in the fixtures

To run all tests:

```
make test
```

To run specific test files:

```
make test DIR=tests/test_listmonk_new_methods.py
```

---

## Files That Require `chmod +x`

These scripts must be executable:

```
bin/start-listmonk
bin/stop-listmonk
```

To fix permissions:

```
make setup
```

---

## Production Usage

In production, you'll use the `ListMonkClient` with your own Listmonk instance:

```python
from listmonk_wrapper import ListMonkClient

# Create client with your production credentials
client = ListMonkClient(
    host="https://your-listmonk-instance.com",
    port=443,  # or your port
    username="your_api_username",  # From your Listmonk admin panel or deployment config
    password="your_api_token",      # pragma: allowlist secret  # From your Listmonk admin panel or deployment config
)

# Use the client normally
subscribers = client.query_subscribers()
```

**Important**: In production:
- You won't have the `tmp/` credential files (those are only created in the test environment)
- You'll need to obtain API credentials from your Listmonk instance's admin panel or deployment configuration
- Store credentials securely using your environment's secrets management (e.g., environment variables, Kubernetes secrets, AWS Secrets Manager, etc.)

---

## Test Environment: Docker Setup and API Token Capture

**This section describes the test environment only.** The Docker setup is designed specifically for
running integration tests against a temporary Listmonk instance.

### Docker Compose Configuration

The test environment uses a dedicated compose file:

```
docker-compose.listmonk.yml
```

### Startup Process

When you run `make listmonk-up` or `make test` (for testing only), the following process occurs:

1. **Postgres Container**: Starts first and waits for health check
2. **Listmonk Container**: Starts after Postgres is healthy (v6.0.0 image in `docker-compose.listmonk.yml`)
3. **Installation**: The Listmonk container runs `./listmonk --install --idempotent --yes`
   - Creates database schema if needed
   - Creates admin user (`LISTMONK_ADMIN_USER` / `LISTMONK_ADMIN_PASSWORD`)
   - Creates API user (`LISTMONK_ADMIN_API_USER`)
   - Prints API token to stderr in format: `export LISTMONK_ADMIN_API_TOKEN="<token>"`
4. **Token Capture**: The install command output is captured:
   - Full logs saved to `tmp/listmonk_install.log`
   - API token extracted using `grep` and `sed` and saved to `tmp/api_token.txt`
5. **Server Start**: After installation, Listmonk server starts normally
6. **Credential Export**: `bin/start-listmonk` reads the token and:
   - Exports `LISTMONK_API_USER` and `LISTMONK_API_TOKEN` as environment variables
   - Creates `tmp/listmonk_api_creds.sh` for sourcing credentials in scripts/tests

### Environment Variables

Environment variables in `.env` control the entire setup:

**Listmonk Application**:
- `LISTMONK_HOST` - Base host URL (default: `http://localhost`)
- `LISTMONK_PORT` - Port where Listmonk listens (default: `9000`)

**Admin User** (created during installation):
- `LISTMONK_ADMIN_USER` - Admin username (default: `admin`)
- `LISTMONK_ADMIN_PASSWORD` - Admin password (min 8 chars, default: `admin123`)

**API User** (created during installation):
- `LISTMONK_ADMIN_API_USER` - API username (default: `api_user`)
- `LISTMONK_ADMIN_API_TOKEN` - **Auto-generated** during installation, captured automatically

**Postgres Database**:
- `POSTGRES_DB` - Database name (default: `listmonk`)
- `POSTGRES_USER` - Database user (default: `listmonk`)
- `POSTGRES_PASSWORD` - Database password (default: `listmonk`)
- `POSTGRES_PORT` - Host port mapping (default: `9432`)

**Note**: The API token (`LISTMONK_ADMIN_API_TOKEN`) is automatically generated during installation and captured by the startup script. You don't need to set it manually - it's extracted from the installation logs and made available via environment variables and the `tmp/listmonk_api_creds.sh` file.

### Generated Files (Test Environment Only)

The test environment startup process creates these files in the `tmp/` directory:

- `tmp/listmonk_install.log` - Full installation log output
- `tmp/api_token.txt` - Just the API token value (one line)
- `tmp/listmonk_api_creds.sh` - Shell script with export statements for sourcing

**Important**:
- These files are **only created in the test environment** when running Docker containers
- The `tmp/` directory is gitignored to prevent committing sensitive credentials
- **In production**, you won't have these files - you'll need to provide credentials through your
  application's configuration management (environment variables, secrets, etc.)

---

## License

BSD-3-Clause
