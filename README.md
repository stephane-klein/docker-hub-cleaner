# Docker Hub Cleaner

This is a script to delete old docker image tags in [Docker Hub](https://cloud.docker.com) that are not used anymore and
delete inactive and untagged docker images.

This script was built to solve the case where images are being built on every dependency change
but we are only using them for CI purposes, so they become outdated quite fast.


## How to install

```
pipenv install
```


## How to use

```
$ pipenv run ./main.py  --help
Loading .env environment variables...
usage: main.py [-h] [--username USERNAME] [--password PASSWORD]
               [--repository REPOSITORY] [--older-in-days OLDER_IN_DAYS]
               [--exclude-tags EXCLUDE_TAGS] [--not-clean-inactive-images]
               [--progress]

Delete old Docker Image tags in Docker Hub

optional arguments:
  -h, --help            show this help message and exit
  --username USERNAME
  --password PASSWORD
  --repository REPOSITORY
                        Repository to clean, this parameter can contain
                        several repository separated by comma. If empty, the
                        script clean all repositories. The syntax is
                        username/imagename (default '')
  --older-in-days OLDER_IN_DAYS
                        Delete tags older than X in days (default 30 days)
  --exclude-tags EXCLUDE_TAGS
                        Tags to never delete, support regex syntax (default:
                        '')
  --not-clean-inactive-images
  --progress

        Usage example:

        main.py \
            --username=example \
            --password=secret \
            --repository=example/project1 \
            --older-in-days=10

        main.py \
            --username=example \
            --password=secret \
            --repository=example/project1,example/project2 \
            --older-in-days=10 \
            --exclude-tags="(develop|prod)"

        main.py \
            --username=example \
            --password=secret \
            --older-in-days=10 \
            --exclude-tags="(develop|prod)"
```


```
$ pipenv run ./main.py \
    --username=example \
    --password=secret \
    --repository=example/project1 \
    --older-in-days=10 \
    --exclude-tags="(develop|prod)"
Going to process docker Hub repository example/project1 and delete all tags older than 10 days.
Deleted tag ba4640839e7bc4743762ce39d72da71e0771d801 that is 439 days old.
Deleted tag 4d6607c4496e8f49e261963f3e81f1d6eb62464d that is 439 days old.
Deleted tag 624fc0cbea81dec054925c8caea256b056d60fca that is 439 days old.
Deleted tag e90e6013ccd223819528301b6624fd672b5c1149 that is 439 days old.
Deleted tag fb0dcce0dae2b360f1aa71195616dcf21cfeb17c that is 441 days old.
Deleted tag a3f91747b04b2bf30d300cb7facb1092e26154ae that is 441 days old.
Deleted tag bda8debe6fa6491e05ac406c05322fbad59303c7 that is 442 days old.
Deleted tag 2500d7292516c45c0db4ed7ede46e933c431be43 that is 442 days old.
...
```
