#
# Created on Wed Dec 22 2021
#
# Copyright (c) 2021 Lenders Cooperative, a division of Summit Technology Group, Inc.
#

import json

import requests
from requests.auth import HTTPBasicAuth


class APIHandler:
    REQUEST_TIMEOUT = 30

    def __init__(self, host, username, password, headers):
        self._host = host
        self._username = username
        self.__password = password
        self._headers = headers

    @property
    def host(self):
        return self._host

    @property
    def username(self):
        return self._username

    def send_request(self, method, url, payload=None, headers=None, params=None):
        if headers is None:
            headers = self._headers

        response = requests.request(
            method,
            f"{self.host}{url}",
            headers=headers,
            timeout=self.REQUEST_TIMEOUT,
            data=payload,
            params=params,
            auth=HTTPBasicAuth(self._username, self.__password),
        )
        response.raise_for_status()
        return response.json()


class ListMonkClient:
    HEADERS = {
        "Content-Type": "application/json",
    }
    DEFAULT_LIST = [1]

    def __init__(self, host, port, username, password):
        self._api_handler = APIHandler(
            f"{host}:{port}",
            username,
            password,
            self.HEADERS,
        )

    def get_campaigns(self):
        return self._api_handler.send_request("GET", "/api/campaigns")

    def get_subscriber_info(self, user_id):
        url = f"/api/subscribers/{user_id}"
        return self._api_handler.send_request("GET", url)

    def query_subscribers(self, attributes={}, page=10, per_page="all", **kwargs):
        url = "/api/subscribers"
        params = {"page": page, "per_page": per_page, **kwargs}

        if bool(attributes):
            query_str = ""
            for x, y in attributes.items():
                query_str += f"subscribers.attribs->>{x}='{y}' AND"
            params["query"] = query_str

        return self._api_handler.send_request("GET", url, params=params)

    def create_campaign(self, name, subject, body, from_email, content_type="html", lists=[1], template_id=1):
        payload = json.dumps(
            {
                "name": name,
                "subject": subject,
                "body": body,
                "from_email": from_email,
                "content_type": content_type,
                "lists": lists,
                "template_id": template_id,
            }
        )
        return self._api_handler.send_request("POST", "/api/campaigns", payload=payload)

    def update_campaign(self, name, subject, body, from_email, campaign_id, content_type="html", lists=[1], template_id=None):
        url = f"/api/campaigns/{campaign_id}"
        data = {
            "name": name,
            "subject": subject,
            "body": body,
            "from_email": from_email,
            "content_type": content_type,
            "lists": lists,
        }
        
        if template_id:
            data["template_id"] = template_id

        payload = json.dumps(data)
        return self._api_handler.send_request("PUT", url, payload=payload)

    def create_template(self, name, body, content_type="html"):
        payload = json.dumps({"name": name, "body": body, "content_type": content_type})
        return self._api_handler.send_request("POST", "/api/templates", payload=payload)

    def update_template(self, name, body, template_id, content_type="html"):
        url = f"/api/templates/{template_id}"
        payload = json.dumps({"name": name, "body": body, "content_type": content_type})
        return self._api_handler.send_request("PUT", url, payload=payload)

    def update_campaign_lists(self, campaign_id, lists):
        url = f"/api/campaigns/{campaign_id}"
        payload = json.dumps({"lists": lists})
        return self._api_handler.send_request("PUT", url, payload=payload)

    def create_list(self, name, list_type, optin):
        payload = json.dumps({"name": name, "type": list_type, "optin": optin})
        return self._api_handler.send_request("POST", "/api/lists", payload=payload)

    def create_subscriber(self, email, name, attribs={}, lists=[]):
        payload = json.dumps({"email": email, "name": name, "attribs": attribs, "lists": lists})
        return self._api_handler.send_request("POST", "/api/subscribers", payload=payload)

    def update_subscriber(self, user_id, email, name, attribs={}, lists=[]):
        url = f"/api/subscribers/{user_id}"
        payload = json.dumps({"email": email, "name": name, "attribs": attribs, "lists": lists})
        return self._api_handler.send_request("PUT", url, payload=payload)

    def delete_subscriber(self, user_id):
        url = f"/api/subscribers/{user_id}"
        return self._api_handler.send_request("DELETE", url)

    def add_subscriber_to_list(self, user_id, email, username, list_id):
        response = self.get_subscriber_info(user_id)
        current_lists = response.get("data", {}).get("lists", [])
        current_list_ids = [l["id"] for l in current_lists] + [list_id]
        updated_lists = list(set(current_list_ids))
        return self.update_subscriber(user_id, email, username, lists=updated_lists)

    def remove_subscriber_from_list(self, user_id, email, username, list_id):
        response = self.get_subscriber_info(user_id)
        current_lists = response.get("data", {}).get("lists", [])
        updated_lists = list(set(l["id"] for l in current_lists if l["id"] != list_id))
        return self.update_subscriber(user_id, email, username, lists=updated_lists)

    def run_campaign(self, campaign_id):
        url = f"/api/campaigns/{campaign_id}/status"
        payload = json.dumps({"status": "running"})
        return self._api_handler.send_request("PUT", url, payload=payload)
