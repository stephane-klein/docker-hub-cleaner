#!/usr/bin/env python3
import argparse
from datetime import datetime
import os
import sys
import math
import re

import requests

default_page_size = 100


def get_auth_token(username, password):
    params = {"username": username, "password": password}
    response = requests.post("https://hub.docker.com/v2/users/login/", data=params)
    response.raise_for_status()

    return response.json()["token"]


def build_headers(auth_token):
    return {"authorization": "Bearer " + auth_token, "content-type": "application/json"}


def get_repos(username, auth_token):
    r = requests.get(
        "https://hub.docker.com/v2/repositories/{}/?page_size=10000".format(username),
        headers=build_headers(auth_token=auth_token)
    )
    r.raise_for_status()

    return [
        '{}/{}'.format(row['namespace'], row['name'])
        for row in r.json()['results']
    ]


def get_tags(repository, auth_token, page_size=default_page_size, page=1):
    """Get tags from Docker Hub for page and with page_size."""
    r = requests.get(
        "https://hub.docker.com/v2/repositories/{}/tags?page_size={}&page={}".format(repository, page_size, page),
        headers=build_headers(auth_token=auth_token)
    )
    r.raise_for_status()

    return r.json()


def delete_tag(repository, auth_token, tag, days_old, exclude_tags):
    """Delete a tag from Docker Hub."""
    if (not re.match(exclude_tags, tag)):
        r = requests.delete(
            "https://hub.docker.com/v2/repositories/{}/tags/{}".format(repository, tag),
            headers=build_headers(auth_token=auth_token)
        )

        r.raise_for_status()
        print("Deleted tag {} that is {} days old.".format(tag, days_old))
    else:
        print("Skip deleted tag {} that is {} days old.".format(tag, days_old))


def delete_tags_older_than(repository, tags, days_old, exclude_tags):
    """Process tags older tags to be deleted."""

    # Process all the results
    if tags:
        for tag_entry in tags:
            only_date = tag_entry["last_updated"][:10]
            datetime_object = datetime.strptime(only_date, "%Y-%m-%d")
            datetime_delta = datetime.now() - datetime_object
            if datetime_delta.days > days_old:
                delete_tag(
                    repository,
                    auth_token=auth_token,
                    tag=tag_entry["name"],
                    days_old=datetime_delta.days,
                    exclude_tags=exclude_tags
                )


if __name__ == "__main__":
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

        main.py \\
            --username=example \\
            --password=secret \\
            --repository=example/project1,example/project2 \\
            --older-in-days=10 \\
            --exclude-tags="(develop|prod)"

        main.py \\
            --username=example \\
            --password=secret \\
            --older-in-days=10 \\
            --exclude-tags="(develop|prod)"
        """
    )
    parser.add_argument("--username", default=os.environ.get("DOCKER_HUB_USERNAME"))
    parser.add_argument("--password", default=os.environ.get("DOCKER_HUB_PASSWORD"))
    parser.add_argument(
        "--repository",
        default=os.environ.get("REPOSITORY"),
        help="Repository to clean, this parameter can contain several repository separated by comma. If empty, the script clean all repositories. The syntax is username/imagename (default '')"
    )
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
        (not args.password)
    ):
        sys.exit(parser.print_usage())

    auth_token = get_auth_token(args.username, args.password)

    if args.repository:
        repos_list = args.repository.split(",")
    else:
        repos_list = get_repos(args.username, auth_token)

    for repos in repos_list:
        print(
            "Going to process docker Hub repository {} and delete all tags older than {} days.".format(
                repos, args.older_in_days
            )
        )

        tags_response = get_tags(repos, auth_token)
        total_items = int(tags_response["count"])
        total_pages = math.ceil(total_items / default_page_size)

        current_page = total_pages
        while current_page > 0:
            tags_response = get_tags(repos, auth_token=auth_token, page=current_page)
            if tags_response["results"]:
                delete_tags_older_than(
                    repos,
                    tags=tags_response["results"],
                    days_old=args.older_in_days,
                    exclude_tags=args.exclude_tags
                )
            print("Page {} processed!".format(current_page))
            current_page = current_page - 1
