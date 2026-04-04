"""
Tests for campaign-related API endpoints.

This module covers all campaign operations:
- Creating campaigns
- Retrieving campaigns
- Updating campaigns
- Running campaigns
"""

import time

import pytest
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

    # Track created resources for cleanup
    list_id = sid = tid = campaign_id = None

    try:
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
        template_body = '<html><body>{{ template "content" . }}</body></html>'
        try:
            template = client.create_template(f"Flow Template {timestamp}", template_body)
            tid = template["data"]["id"]
        except requests.HTTPError:
            pass

        # 4. Create campaign (omit template_id when template creation failed)
        campaign_kwargs = dict(
            name=f"Flow Campaign {timestamp}",
            subject="Flow Subject",
            body="<p>Flow Body</p>",
            from_email="noreply@test.com",
            lists=[list_id],
        )
        if tid is not None:
            campaign_kwargs["template_id"] = tid
        campaign = client.create_campaign(**campaign_kwargs)
        campaign_id = campaign["data"]["id"]

        # 5. Fetch all campaigns
        campaigns = client.get_campaigns()
        assert any(c["id"] == campaign_id for c in campaigns["data"]["results"])

        # 6. Run campaign
        run_res = client.run_campaign(campaign_id)
        assert "message" in run_res or "data" in run_res
    finally:
        # Cleanup all created resources
        for delete_fn, resource_id in [
            (client.delete_subscriber, sid),
            (client.delete_campaign, campaign_id),
            (client.delete_list, list_id),
        ]:
            if resource_id is not None:
                try:
                    delete_fn(resource_id)
                except Exception:
                    pass
        if tid is not None:
            try:
                client.delete_template(tid)
            except Exception:
                pass


def test_campaign_attribs_v6(client, listmonk_version_tuple):
    """Test campaign JSON attribs support in v6.0.0+."""
    if listmonk_version_tuple < (6, 0, 0):
        pytest.skip("Campaign attribs require Listmonk v6.0.0+")

    timestamp = int(time.time())
    campaign_id = list_id = None

    try:
        created_list = client.create_list(
            name=f"Attribs List {timestamp}", list_type="private", optin="single"
        )
        list_id = created_list["data"]["id"]

        attribs = {"source": "tests", "counter": 1}
        campaign = client.create_campaign(
            name=f"Attribs Campaign {timestamp}",
            subject="Attribs Subject",
            body="<p>Attribs Body</p>",
            from_email="noreply@test.com",
            lists=[list_id],
            attribs=attribs,
        )
        campaign_id = campaign["data"]["id"]

        if "attribs" in campaign["data"]:
            assert campaign["data"]["attribs"] == attribs
        else:
            campaigns = client.get_campaigns()
            match = next((c for c in campaigns["data"]["results"] if c["id"] == campaign_id), None)
            assert match is not None
            assert match.get("attribs") == attribs
    finally:
        for delete_fn, rid in [(client.delete_campaign, campaign_id), (client.delete_list, list_id)]:
            if rid is not None:
                try:
                    delete_fn(rid)
                except Exception:
                    pass


def test_delete_campaigns_v6(client, listmonk_version_tuple):
    """Test bulk campaign deletion in v6.0.0+."""
    if listmonk_version_tuple < (6, 0, 0):
        pytest.skip("Bulk campaign deletion requires Listmonk v6.0.0+")

    timestamp = int(time.time())
    list_id = None
    campaign_ids = []

    try:
        created_list = client.create_list(
            name=f"Delete Campaigns List {timestamp}", list_type="private", optin="single"
        )
        list_id = created_list["data"]["id"]

        for i in range(2):
            campaign = client.create_campaign(
                name=f"Delete Campaign {timestamp}-{i}",
                subject="Delete Subject",
                body="<p>Delete Body</p>",
                from_email="noreply@test.com",
                lists=[list_id],
            )
            campaign_ids.append(campaign["data"]["id"])

        result = client.delete_campaigns(campaign_ids=campaign_ids)
        assert "data" in result or "message" in result

        campaigns = client.get_campaigns()
        remaining = {c["id"] for c in campaigns["data"]["results"]}
        assert not any(cid in remaining for cid in campaign_ids)
    finally:
        for cid in campaign_ids:
            try:
                client.delete_campaign(cid)
            except Exception:
                pass
        if list_id is not None:
            try:
                client.delete_list(list_id)
            except Exception:
                pass
