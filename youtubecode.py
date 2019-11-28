import os
import csv
import pickle
import google.oauth2.credentials
import re

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


def get_authenticated_service(
    CLIENT_SECRETS_FILE, SCOPES, API_SERVICE_NAME, API_VERSION
):
    """connects with the youtube API and saves the confirmation steps into a pickle object at the first time.
    If that object already exists, try to get the init information from it
    
    Returns:
        build: API service Object
    """
    credentials = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            credentials = pickle.load(token)
    #  Check if the credentials are invalid or do not exist
    if not credentials or not credentials.valid:
        # Check if the credentials have expired
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE, SCOPES
            )
            credentials = flow.run_console()

        # Save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(credentials, token)

    return build(API_SERVICE_NAME, API_VERSION, credentials=credentials)


def get_all_video_comments(service, videolist, filename, **kwargs):
    """Returns the comments from all the input videos
    
    Args:
        service (API service): Service object
        videolist (list): List of Lists with the informations of the video
        filename (str): Name of the file to write to
    """
    write_to_csv([], filename)
    final_result = []
    print(f"~~ Getting all {len(videolist)} videos. ~~")
    # gets the data for each video in the list and saves it into a csv
    for a_name, video_id, title in videolist:
        print(f"{a_name}: {title}", end=" ")
        comments, replys, like_count = get_video_comments(
            service, part="snippet", videoId=video_id, textFormat="plainText"
        )
        # also gets the statistics for the video
        stats = get_video_statistics(service, video_id)
        final_result=[
                (
                    a_name,
                    video_id,
                    title,
                    stats["viewCount"],
                    stats["commentCount"],
                    stats["likeCount"],
                    stats["dislikeCount"],
                    replys[i],
                    like_count[i],
                    comment.replace("\n", " "),
                )
                for i, comment in enumerate(comments)
            ]
        write_to_csv(final_result, filename, mode="a", header=False)


def get_video_comments(service, **kwargs):
    """Gets all the top level comments from the video
    
    Args:
        service (API service): Service object
    
    Returns:
        tuple: Tuple with lists with all the top level comments
    """
    comments = []
    replys = []
    like_counts = []
    results = service.commentThreads().list(**kwargs).execute()

    # loop over all comments and appends the statistics for them to a list
    while results:
        for item in results["items"]:
            # clc is the group with all comment related data
            clc = item["snippet"]["topLevelComment"]["snippet"]
            comment = clc["textDisplay"]
            reply = item["snippet"]["totalReplyCount"]
            like_count = clc["likeCount"]
            comments.append(comment)
            replys.append(reply)
            like_counts.append(like_count)

        if "nextPageToken" in results:
            kwargs["pageToken"] = results["nextPageToken"]
            results = service.commentThreads().list(**kwargs).execute()
        else:
            break

    return (comments, replys, like_counts)


def channel_to_comment(service, channel_props, filename, max_vids=50):
    """Gets all the properties from the top most n videos of a list of channels.
    
    Args:
        service (API service): Service object
        channel_props (list): List of lists with channelname and channelid.
        filename (str): Name of the file to write to.
        max_vids (int, optional): Top most viewed videos to get. Defaults to 50.
    """
    # first generate only the header of the file
    write_to_csv([], filename)
    comment_store = []
    # iterate over each channel
    for c_number, channel in enumerate(channel_props):
        ch_name, ch_id = channel
        print(f"~~ Getting {c_number+1}. Channel: {ch_name} ~~")
        videos = get_streamer_videos(service, ch_id, max_ids=max_vids)
        # iterate over each fetched video
        for number, video in enumerate(videos):
            v_title = video["snippet"]["title"]
            v_id = video["id"]["videoId"]
            print(f" -Processing: #{number+1}: {v_title}", end=" ")
            # try to get all comments, if the video was locked there will be an error
            # additionally if there are no more requests there will be also an error
            try:
                comments, replys, like_count = get_video_comments(
                    service, part="snippet", videoId=v_id, textFormat="plainText"
                )
                stats = get_video_statistics(service, v_id)
                # store various properties in the list to writer later to csv
                comment_store = [
                    (
                        ch_name,
                        v_id,
                        v_title,
                        stats["viewCount"],
                        stats["commentCount"],
                        stats["likeCount"],
                        stats["dislikeCount"],
                        replys[i],
                        like_count[i],
                        comment.replace("\n", " "),
                    )
                    for i, comment in enumerate(comments)
                ]
                write_to_csv(comment_store, filename, mode="a", header=False)
            except:
                print(
                    "Ups! There was an error. Check the video and / or your request amounts"
                )
    # print("~~ Almost done, writing file ~~")
    # write_to_csv(comment_store, filename)
    print("~~ Done, enjoy! ~~")


def get_video_statistics(service, v_id):
    """Gets the stats (view, comment, like, dislike) of a video.
    
    Args:
        service (API service): Servive object
        v_id (str): Id of the video.
    
    Returns:
        json: data of the video
    """
    properties = service.videos().list(id=v_id, part="statistics").execute()
    data = properties["items"][0]["statistics"]
    print(
        f"~ Statistics: views|comments: {data['viewCount']}|{data['commentCount']} || likes|dislikes: {data['likeCount']}|{data['dislikeCount']}"
    )
    return data


def get_streamer_videos(service, streamer_id, max_ids=50):
    """Get a fixed amount of videos sorted by the most likes
    
    Args:
        service (API service): Service object
        streamer_id (str): Id of the channel
        max_ids (int, optional): Maximum amount of video objects to return. Defaults to 50.
    
    Returns:
        dict: information of each video
    """
    videos = []
    pageToken = None

    # get the most max_ids viewed videos from the current channel
    while pageToken != False and len(videos) <= max_ids:
        resultVideos = get_videos(service, streamer_id, 50, pageToken)
        videos.extend(resultVideos["items"])
        pageToken = resultVideos.get("nextPageToken", False)

    # since one batch returns 50 videos, reduce it to the max len
    cut = max_ids
    if len(videos) < max_ids:
        cut = len(videos)
    return videos[:max_ids]


def get_videos(service, channelId, maxResults, pageToken):
    """Gets the nth videos from one page
    
    Args:
        service (API service): Service object
        channelId (str): id of the youtuber
        maxResults (int): max results one token return (values are 0-50)
        pageToken (token): pageToken object for multiple runs

    Returns:
        dict: information of each video
    """
    # serach all the videos from the channel sorted by viewcount
    # here also some properties like min/max date or another type of order could be used
    result = (
        service.search()
        .list(
            part="snippet",
            channelId=channelId,
            pageToken=pageToken,
            order="viewCount",
            safeSearch="none",
            type="video",
            maxResults=maxResults,
        )
        .execute()
    )
    return result


def write_to_csv(comments, filename, mode="w", header=True):
    """Writes all the comment data to a csv file for later evaluation
    
    Args:
        comments (list): List of all the scraped data
        filename (str): Name for the file
    """
    with open(f"{filename}.csv", mode, encoding="utf-8", newline="") as comments_file:
        comments_writer = csv.writer(
            comments_file, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL
        )
        # if this is the first line write the header into it
        if header:
            comments_writer.writerow(
                [
                    "Stramer",
                    "Video_id",
                    "Title",
                    "Views",
                    "Comment_count",
                    "Video_likes",
                    "Video_dislikes",
                    "Comment_replies",
                    "Comment_likes",
                    "Comment",
                ]
            )
        for row in comments:
            comments_writer.writerow(list(row))


def clean_str(string):
    return re.sub(r"\s+", " ", string.encode("ascii", "ignore")).strip()
