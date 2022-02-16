#!/usr/bin/env python3
import argparse
from datetime import datetime
import os
import sys
import math
import re

import requests

default_page_size = 100

parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description="Delete old Docker Image tags in Docker Hub",
    epilog="""
    Usage example:

    main.py \\
        --username=example \\
        --password=secret \\
        --repository=example/project1 \\
        --older-in-days=10
    """
)
parser.add_argument("--username", default=os.environ.get("DOCKER_HUB_USERNAME"))
parser.add_argument("--password", default=os.environ.get("DOCKER_HUB_PASSWORD"))
parser.add_argument("--repository", default=os.environ.get("REPOSITORY"))
parser.add_argument(
    "--older-in-days",
    type=int,
    default=os.environ.get("DELETE_OLDER_THAN_IN_DAYS", 30),
    help="Delete tags older than X in days (default 30 days)"
)
parser.add_argument(
    "--exclude-tags",
    default=os.environ.get("EXCLUDE_TAGS", ""),
    help="Tags to never delete, support regex syntax (default: '')"
)

args = parser.parse_args()
if (
    (not args.username) or
    (not args.password) or
    (not args.repository)
):
    sys.exit(parser.print_usage())

hub_endpoints = {
    "login": "https://hub.docker.com/v2/users/login/",
    "list_tags": "https://hub.docker.com/v2/repositories/" + args.repository + "/tags",
    "delete_tag": "https://hub.docker.com/v2/repositories/"
    + args.repository
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
    if (not re.match(args.exclude_tags, tag)):
        headers = build_headers(auth_token=auth_token)
        r = requests.delete(hub_endpoints["delete_tag"].format(tag=tag), headers=headers)

        r.raise_for_status()
        print("Deleted tag {} that is {} days old.".format(tag, days_old))
    else:
        print("Skip deleted tag {} that is {} days old.".format(tag, days_old))


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


if __name__ == "__main__":
    print(
        "Going to process docker Hub repository {} and delete all tags older than {} days.".format(
            args.repository, args.older_in_days
        )
    )

    auth_token = get_auth_token(args.username, args.password)

    tags_response = get_tags(auth_token)
    total_items = int(tags_response["count"])
    total_pages = math.ceil(total_items / default_page_size)

    current_page = total_pages
    while current_page > 0:
        tags_response = get_tags(auth_token=auth_token, page=current_page)
        if tags_response["results"]:
            delete_tags_older_than(
                tags=tags_response["results"],
                days_old=args.older_in_days
            )
        print("Page {} processed!".format(current_page))
        current_page = current_page - 1
