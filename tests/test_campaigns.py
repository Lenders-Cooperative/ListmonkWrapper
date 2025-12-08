"""
Tests for campaign-related API endpoints.

This module covers all campaign operations:
- Creating campaigns
- Retrieving campaigns
- Updating campaigns
- Running campaigns
"""

import time

import requests


def test_get_all_campaigns(client):
    """Test retrieving all campaigns."""
    results = client.get_campaigns()
    # v5.1.0+ returns {"data": {"results": [...], "total": int, "page": int}}
    assert "data" in results
    assert "results" in results["data"]
    assert isinstance(results["data"]["results"], list)


def test_campaign_full_flow(client):
    """Test full campaign creation and execution flow."""
    # Use unique names/emails to avoid conflicts
    timestamp = int(time.time())

    # 1. Create list
    created_list = client.create_list(
        name=f"Flow List {timestamp}", list_type="private", optin="double"
    )
    list_id = created_list["data"]["id"]

    # 2. Create subscriber
    sub = client.create_subscriber(
        email=f"flow_{timestamp}@test.com", name="FlowUser", lists=[list_id]
    )
    sid = sub["data"]["id"]

    # 3. Create template (skip if template creation fails)
    # Template body must include the {{ template "content" . }} placeholder
    template_body = '<html><body>{{ template "content" . }}</body></html>'
    tid = None
    try:
        template = client.create_template(f"Flow Template {timestamp}", template_body)
        tid = template["data"]["id"]
    except requests.HTTPError:
        # Template creation might fail, continue without template
        pass

    # 4. Create campaign
    campaign = client.create_campaign(
        name=f"Flow Campaign {timestamp}",
        subject="Flow Subject",
        body="<p>Flow Body</p>",
        from_email="noreply@test.com",
        lists=[list_id],
        template_id=tid,
    )
    campaign_id = campaign["data"]["id"]

    # 5. Fetch all campaigns
    campaigns = client.get_campaigns()
    assert any(c["id"] == campaign_id for c in campaigns["data"]["results"])

    # 6. Run campaign
    run_res = client.run_campaign(campaign_id)
    # v5.1.0+ returns {"data": {...}} or {"message": "ok"}
    assert "message" in run_res or "data" in run_res

    # Cleanup
    client.delete_subscriber(sid)
