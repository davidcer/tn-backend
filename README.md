# Install TN Backend Challenge repo on your computer

## Installation
Clone the repo from github [https://github.com/davidcer/tn-backend](https://github.com/davidcer/tn-backend)

## Create a virtual enviroment
```bash
python3 -m venv/bin/activate
```
(Python3 requirement is assumed)

## Install project requirements 
```bash
pip install -r requirements.txt
```

## Set-up env
From .env.example you have the structure of the database string. Postgres is assumed. you can change your desired driver if needed.

## Migrate
```bash
source venv/bin/activate
python3 mgigrate.py
```
This migration is relevant to set table structure and to set-up costs of operations


## Start backend flask application.
Flask Backend Application can be run on dev mod as
```bash
flask run --no-debugger
```
running on prod would require to set-up properly a WSGI as gunicorn.

## Create users by curl

```python
import requests
import json

url = "http://127.0.0.1:5000/create_user"

payload = json.dumps({
  "email": "youremail",
  "password": "yourpassword"
})
headers = {
  'Content-Type': 'application/json'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)

```

## To hit endpoints, authenticate firs on /token endpoint


# Pendings task - (this is an ongoing process)

* Adding message response to log in 
* Push tests to repo
* When Calc return input (comma sepparated values) by the opeartor used
* Expose logger ouput 
* Hashing user password
* cath 400 and 500 (not cached)
* improving exception handling