# Youtube API wrapup

This file helps you simplify the process of getting comments of various Youtube videos or channels.
It will get the Views, Comment count, Video likes, Video dislikes, Comment replies of each comment, Comment likes of each comment,and the Comment Text of each comment.
First you need to set up your Youtube API according to the documentation and then replace the `client_secret.json` name with the name of your file for the client_secret.
The function `get_authenticated_service` will set up a pickle file to prevent authentication each time you will run your script after the first time.
Example code is provided in the `runme.py` file.
Slightly modified it can serve your specific purpose.
More information can also be found [here](https://developers.google.com/youtube/v3/quickstart/python).

## Minimal Requirements

```
- Python 3.6
- google api python client
- google-auth-oauthlib
```
The packages can usually be installed from PyPi with the `pip install 'packagename'` or your system according command.
The easier way is just to run `pip install -r requirements.txt` to get all the requirements.
You can install the google api python client with `pip install --upgrade google-api-python-client` and `pip install google-auth-oauthlib`.

