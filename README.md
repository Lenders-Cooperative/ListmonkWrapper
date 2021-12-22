# ListmonkWrapper


Light Python wrapper for listmonk.app


* PyPI: <https://pypi.org/project/listmonk-wrapper/>
* Free software: BSD-3-Clause


## Testing
* Must have local listmonk container running (TODO: add docker container in repo for testing purposes)
* `poetry install -E dev -E test`
* `poetry run pytest`

## Usage
* `pip install listmonk-wrapper`
```
    from listmonk_wrapper import ListMonkClient

    client = ListMonkClient(host="http://localhost", port=9000, username="password", password="password")
    my_campaigns = client.get_campaigns()
```
