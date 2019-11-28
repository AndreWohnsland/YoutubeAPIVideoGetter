import os

from youtubecode import channel_to_comment, get_all_video_comments, get_authenticated_service

# different channels and their id
channel_props = [
    ["DrapsTV", "UCea5cMUa9xNU0kUtbRcTkqA"],
    ["Machine Love Us", "UCPb2L7gy8Rbr56JfoHrBEHQ"],
    ["Dev Ed", "UClb90NQQcskPUGDIXsQEz5Q"]
]
# externalId in the HTML got the channel id if there is only a user 

# different videos, their id as well as the channel name
videolist = [
    ["Dev Ed", "9ODGKI_VAmE", "I React To Viewers Projects!"],
    ["Dev Ed", "cHdBzrb2ubs", "Things I Wish I Knew About Programming"],
]


if __name__ == "__main__":
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    service = get_authenticated_service(
        "client_secret.json",
        ['https://www.googleapis.com/auth/youtube.force-ssl'],
        'youtube',
        'v3'
    )
    # channel_to_comment(service, channel_props, "Filename", max_vids=50)
    get_all_video_comments(service, videolist, "singlevideos", part='snippet', textFormat='plainText')