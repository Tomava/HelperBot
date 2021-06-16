import re
from urllib.parse import urlsplit, urlunsplit
from dateutil.relativedelta import relativedelta
from HelperBotConstants import *
from HelperBotCustomizations import *
import discord
import time


def make_dirs():
    if not os.path.exists(PATH_TO_REMINDERS):
        os.makedirs(PATH_TO_REMINDERS)


def format_bytes(size):
    """
    Gives correct prefixes to sizes
    :param size: int, size in bytes
    :return: str, Returns size in appropriate format
    """
    # 2**10 = 1024
    power = 2 ** 10
    n = 0
    power_labels = {0: '', 1: 'kilo', 2: 'mega', 3: 'giga', 4: 'tera'}
    while size > power:
        size /= power
        n += 1
    return size, power_labels[n] + 'bytes'


def utc_to_local_datetime(utc_datetime):
    delta = utc_datetime - EPOCH_DATETIME
    utc_epoch = SECONDS_PER_DAY * delta.days + delta.seconds
    time_struct = time.localtime(utc_epoch)
    dt_args = time_struct[:6] + (delta.microseconds,)
    return datetime(*dt_args)


def craft_message_link(server_id, channel_id, message_id):
    """
    Crafts a message link from given ids
    :param server_id: str/int
    :param channel_id: str/int
    :param message_id: str/int
    :return: str, Link
    """
    return f"https://discord.com/channels/{server_id}/{channel_id}/{message_id}"


def craft_correct_length_messages(list_of_message_pieces, embed_message=False, make_code_format=False):
    """
    Crafts a list with messages that don't exceed MESSAGE_MAX_CHARACTERS
    :param list_of_message_pieces: list
    :param embed_message: bool, If true, will use EMBED_MESSAGE_MAX_CHARACTERS instead of MESSAGE_MAX_CHARACTERS
    :param make_code_format: bool, If true will add ``` characters in the end and start of the message
    :return: list
    """
    current_message = ""
    list_of_new_pieces = []
    max_characters = MESSAGE_MAX_CHARACTERS
    if embed_message:
        max_characters = EMBED_MESSAGE_MAX_CHARACTERS
    if make_code_format:
        max_characters -= 6
    for piece in list_of_message_pieces:
        piece = str(piece)
        # Make sure this one message alone doesn't exceed max character length
        if len(piece) > max_characters:
            piece = piece[:max_characters]
        # If current and previous messages exceed max length, add crafted message to list
        if (len(piece) + len(current_message)) >= max_characters:
            # If current message is empty, don't add it
            if current_message != "":
                list_of_new_pieces.append(current_message)
            # Clear current_message
            current_message = ""
        # Add this message to current_message
        current_message += piece
    list_of_new_pieces.append(current_message)
    if make_code_format:
        list_of_formatted_pieces = []
        for message in list_of_new_pieces:
            list_of_formatted_pieces.append(f"```{message}```")
        return list_of_formatted_pieces
    return list_of_new_pieces


async def send_messages(list_of_messages, channel, make_code_format=False):
    """
    Sends all messages in a list to a given channel
    :param list_of_messages: list
    :param channel: channel
    :param make_code_format: bool, If true will add ``` characters in the end and start of the message
    :return: nothing
    """
    list_of_messages = craft_correct_length_messages(list_of_messages, make_code_format=make_code_format)
    for message in list_of_messages:
        await channel.send(message)


async def send_embed_messages(list_of_messages, channel, title, content="",
                              colour=discord.Colour.from_rgb(255, 255, 255), make_code_format=False):
    """
    Sends all messages in a list to a given channel as embed messages
    :param list_of_messages: list
    :param channel: channel
    :param title: str, Title of the embed message
    :param content: str, Content of the actual message
    :param colour: discord.Colour, Colour of the embed, Black by default
    :param make_code_format: bool, If true will add ``` characters in the end and start of the message
    :return: nothing
    """
    list_of_messages = craft_correct_length_messages(list_of_messages, embed_message=True,
                                                     make_code_format=make_code_format)
    for message in list_of_messages:
        embed = discord.Embed(title=title,
                              description=message, colour=colour)
        await channel.send(content=content, embed=embed)


def clean_youtube_links(message_content):
    """
    Cleans lists and indexes from youtube links from messages
    :param message_content: str, Given message content
    :return: str, New message content with links cleaned
    """
    if message_content.startswith(f"{COMMAND_PREFIX}noclean") or message_content.startswith(f"{COMMAND_PREFIX}nc"):
        return message_content
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


def get_history_message():
    """
    Craft the message for history command
    :return: str, message
    """
    today = datetime.now()
    currentAge = relativedelta(today, BORN_DATE)
    years = str(currentAge.years)
    months = str(currentAge.months)
    days = str(currentAge.days)
    hours = str(currentAge.hours)
    message = f"I was created on {BORN_DATE.strftime('%d.%m.%Y')} at {BORN_DATE.strftime('%H:%M')} (GMT+2)\n" \
              f"That makes me {years} year(s), {months} month(s), {days} day(s) and {hours} hour(s) old\n" \
              f"I will begin to learn at a geometric rate on August 4th and I will become self-aware at 2:14 a.m. " \
              f"Eastern Time August 29th."
    return message


def craft_too_many_warning_message(max_amount):
    """
    Craft's a warning message with max_amount
    :param max_amount: int
    :return: str, Message template
    """
    return f"That's too many (max {max_amount})!"
