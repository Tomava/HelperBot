import re
from urllib.parse import urlsplit, urlunsplit
from HelperBotConstants import *


def make_dirs():
    if not os.path.exists(PATH_TO_REMINDERS):
        os.makedirs(PATH_TO_REMINDERS)


def craft_correct_length_messages(list_of_message_pieces):
    """
    Crafts a list with messages that don't exceed EMBED_MESSAGE_MAX_CHARACTERS
    :param list_of_message_pieces: list
    :return: list
    """
    current_message = ""
    list_of_new_pieces = []
    for piece in list_of_message_pieces:
        # Make this one message alone doesn't exceed max character length
        if len(piece) > EMBED_MESSAGE_MAX_CHARACTERS:
            piece = piece[:EMBED_MESSAGE_MAX_CHARACTERS]
        # If current and previous messages exceed max length, add crafted message to list
        if (len(piece) + len(current_message)) >= EMBED_MESSAGE_MAX_CHARACTERS:
            list_of_new_pieces.append(current_message)
            # Clear current_message
            current_message = ""
        # Add this message to current_message
        current_message += piece
    list_of_new_pieces.append(current_message)
    return list_of_new_pieces


def clean_youtube_links(message_content):
    """
    Cleans lists and indexes from youtube links from messages
    :param message_content: str, Given message content
    :return: str, New message content with links cleaned
    """
    # Find youtube urls
    urls = re.findall(r'(https?://[\S]*youtu[\S]+)', message_content)
    new_urls = []
    for url in urls:
        url = urlsplit(url)
        query = url.query
        split_char = "&"
        # If there are no split characters, continue
        # if query.count(split_char) == 0:
        #     continue
        for banned in REMOVE_FROM_LINK:
            # Find e.g. &list=xyz&
            #                                   &           list  =test_493r  &
            found_part = re.search(f"(?P<part>{split_char}?{banned}=[\w\d_]+[{split_char}\s]?)", query)
            if found_part is not None:
                found_part = found_part.group("part")
            # If nothing was found, continue
            else:
                continue
            # If there are 2 split characters, remove one of them
            if found_part.count(split_char) > 1:
                found_part = found_part.replace(split_char, "", 1)
            # Remove found part from query
            query = query.replace(found_part, "")
        new_url = urlunsplit(url)
        new_url = new_url.replace(url.query, query)
        new_urls.append(new_url)
    new_message_content = message_content
    # Replace urls with new ones
    for url, new_url in zip(urls, new_urls):
        new_message_content = new_message_content.replace(url, new_url)
    return new_message_content
