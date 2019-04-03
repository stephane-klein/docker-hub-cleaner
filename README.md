# Docker Hub Cleaner

This is a script to delete old docker image tags in [Docker Hub](https://cloud.docker.com) that are not used anymore.

This script was built to solve the case where images are being built on every dependency change
but we are only using them for CI purposes, so they become outdated quite fast.


## How to install

```
pipenv install
```


## How to use

Copy the **.env.dist** to **.env** and fill the variables with your values.

```
$ python main.py
```