from datetime import datetime
import os

from dotenv import load_dotenv
import requests


load_dotenv()
hub_username = os.getenv('DOCKER_HUB_USERNAME')
hub_password = os.getenv('DOCKER_HUB_PASSWORD')
repository = os.getenv('REPOSITORY')
delete_older_than_in_days = int(os.getenv('DELETE_OLDER_THAN_IN_DAYS'))

hub_endpoints = {
    'login': 'https://hub.docker.com/v2/users/login/',
    'list_tags': 'https://hub.docker.com/v2/repositories/' + repository + '/tags',
    'delete_tag': 'https://hub.docker.com/v2/repositories/' + repository + '/tags/{tag}'
}


def get_auth_token(username, password):
    params = {'username': username, 'password': password}
    response = requests.post(hub_endpoints['login'], data=params)
    response.raise_for_status()

    return response.json()['token']


def build_headers(auth_token):
    return {
        'authorization': 'Bearer ' + auth_token,
        'content-type': 'application/json'
    }


def get_tags(auth_token, page_url=None):
    headers = build_headers(auth_token=auth_token)
    if page_url:
        url = page_url
    else:
        url = hub_endpoints['list_tags'] + '?page_size=100'

    r = requests.get(url, headers=headers)
    r.raise_for_status()

    return r.json()


def delete_tag(auth_token, tag):
    """Delete a tag from Docker Hub."""
    headers = build_headers(auth_token=auth_token)
    r = requests.delete(hub_endpoints['delete_tag'].format(tag=tag), headers=headers)

    r.raise_for_status()
    print('Deleted tag {}'.format(tag))


def process_tags(auth_token, next_page_url=None):
    """Get tags from Docker Hub and check for tags older tags to be deleted."""
    tags_response = get_tags(auth_token, page_url=next_page_url)

    # Process all the results
    if tags_response['results']:
        for tag_entry in tags_response['results']:
            # print('Tag name: ', tag_entry['name'], 'last_updated:', tag_entry['last_updated'])
            only_date = tag_entry['last_updated'][:10]
            datetime_object = datetime.strptime(only_date, '%Y-%m-%d')
            datetime_delta = datetime.now() - datetime_object
            if datetime_delta.days > delete_older_than_in_days:
                delete_tag(auth_token=auth_token, tag=tag_entry['name'])

    # Check if there are more pages to process.
    if tags_response['next']:
        process_tags(auth_token=auth_token, next_page_url=tags_response['next'])


# Main app begins

print(
    'Going to process docker Hub repository {} and delete all tags older than {} days.'.format(
        repository,
        delete_older_than_in_days
    )
)

auth_token = get_auth_token(hub_username, hub_password)
process_tags(auth_token=auth_token)




