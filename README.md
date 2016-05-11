This is project is three pieces that can work together, or be
used separately:

1. A program that runs to pull tweets of a certain search into a database.
2. A program that takes a (1) target image, (2) collection of source images
3. A Django app that manages the regular production of (2) based on (1) with some help from Celery

But you can use just (1) and (2) alone if you want.

Installation
------------


Running manually
----------------



Running the Django App and setting up a server
----------------------------------------------
edit the file local_settings.py:

SOCIAL_AUTH_TWITTER_KEY = '<twitter key>'
SOCIAL_AUTH_TWITTER_SECRET = '<twitter secret>'
