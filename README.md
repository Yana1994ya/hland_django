# Hollyday Land back-office and API

Django back-office and API for the educational Flutter "Hollyday Land" application
available at:

https://github.com/Yana1994ya/Hollyday_Land

This django is connected to the database, and allows the applications managers
to manage the content application users see, ban users, delete comments and change filters.

To run this application, ensure
`hland/settings.py` file is present and has the following entries:

```python
from .base_settings import *

DEBUG = True

SECRET_KEY = "Some secret password"

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "{dbname}",
        "USER": "{dbuser}",
        "PASSWORD": "{dbpassword}",
        "HOST": "{dbhost}",
        "PORT": "{dbport}",
    }
}

ASSETS = {
    "bucket": "{bucket}",
    "prefix": "{prefix}",
    "config": {
        "region_name": "{region}",
        "aws_access_key_id": "{access_key_id}",
        "aws_secret_access_key": "{secret_access_key}",
    },
}
```

(This file is not saved to avoid publishing secrets to public
repositories.)

After the file exists, you can type:

`python manage.py runserver`

To run the project locally, or setup a docker image to deploy it.