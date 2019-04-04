from datetime import datetime
import os
import math

from dotenv import load_dotenv
import requests


load_dotenv()
hub_username = os.getenv("DOCKER_HUB_USERNAME")
hub_password = os.getenv("DOCKER_HUB_PASSWORD")
repository = os.getenv("REPOSITORY")
delete_older_than_in_days = int(os.getenv("DELETE_OLDER_THAN_IN_DAYS"))
default_page_size = int(os.getenv("DEFAULT_PAGE_SIZE"))

hub_endpoints = {
    "login": "https://hub.docker.com/v2/users/login/",
    "list_tags": "https://hub.docker.com/v2/repositories/" + repository + "/tags",
    "delete_tag": "https://hub.docker.com/v2/repositories/"
    + repository
    + "/tags/{tag}",
}


def get_auth_token(username, password):
    params = {"username": username, "password": password}
    response = requests.post(hub_endpoints["login"], data=params)
    response.raise_for_status()

    return response.json()["token"]


def build_headers(auth_token):
    return {"authorization": "Bearer " + auth_token, "content-type": "application/json"}


def get_tags(auth_token, page_size=default_page_size, page=1):
    """Get tags from Docker Hub for page and with page_size."""
    headers = build_headers(auth_token=auth_token)
    url = hub_endpoints["list_tags"] + "?page_size={}&page={}".format(page_size, page)

    r = requests.get(url, headers=headers)
    r.raise_for_status()

    return r.json()


def delete_tag(auth_token, tag, days_old):
    """Delete a tag from Docker Hub."""
    headers = build_headers(auth_token=auth_token)
    r = requests.delete(hub_endpoints["delete_tag"].format(tag=tag), headers=headers)

    r.raise_for_status()
    print("Deleted tag {} that is {} days old.".format(tag, days_old))


def delete_tags_older_than(tags, days_old):
    """Process tags older tags to be deleted."""

    # Process all the results
    if tags:
        for tag_entry in tags:
            # print('Tag name: ', tag_entry['name'], 'last_updated:', tag_entry['last_updated'])
            only_date = tag_entry["last_updated"][:10]
            datetime_object = datetime.strptime(only_date, "%Y-%m-%d")
            datetime_delta = datetime.now() - datetime_object
            if datetime_delta.days > days_old:
                delete_tag(
                    auth_token=auth_token,
                    tag=tag_entry["name"],
                    days_old=datetime_delta.days,
                )


# Main app begins

print(
    "Going to process docker Hub repository {} and delete all tags older than {} days.".format(
        repository, delete_older_than_in_days
    )
)

auth_token = get_auth_token(hub_username, hub_password)

tags_response = get_tags(auth_token)
total_items = int(tags_response["count"])
total_pages = math.ceil(total_items / default_page_size)

current_page = total_pages
while current_page > 0:
    tags_response = get_tags(auth_token=auth_token, page=current_page)
    if tags_response["results"]:
        delete_tags_older_than(
            tags=tags_response["results"], days_old=delete_older_than_in_days
        )
    print("Page {} processed!".format(current_page))
    current_page = current_page - 1
