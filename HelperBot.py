import discord
from discord.ext import commands
import asyncio
from datetime import datetime
import dateutil.parser
import random
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
import json
import time
from image_downloader import download_image
from bot_config import *

COMMAND_PREFIX = "!"

make_dirs()
list_of_reminders = get_reminders()
reminder_amounts = get_reminder_amounts()
description = ""
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix=COMMAND_PREFIX, description=description, intents=intents)
load_dotenv(path_to_discord + os.sep + "HelperBoyToken.env")
token = os.getenv('DISCORD_TOKEN')
reminder_task_started = False


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    await bot.change_presence(activity=discord.Game(name='!help'))
    global reminder_task_started
    if not reminder_task_started:
        reminder_task_started = True
        await reminder_function()


@bot.event
async def on_command_error(ctx, error):
    if hasattr(ctx.command, 'on_error'):
        print("Error:", error)
    elif isinstance(error, commands.errors.UserInputError):
        await ctx.channel.send("Looks like your message wasn't formatted correctly.\nType !help to get correct formats")
    else:
        print("Error:", error)
        raise error


@bot.command(aliases=["remove"])
async def delete(ctx, how_many: int):
    message = ctx.message
    private = False
    if str(message.channel.type) == "private":
        private = True
    if not private and (message.channel.name == "general"):
        await message.channel.send("Deleting messages on channel 'general' is disabled.")
        return
    try:
        # Get confirmation
        await message.channel.send("Confirm deletion of " + str(how_many) + " messages (y/n)")

        def check(m):
            return m.author == message.author and str(m.content).lower().startswith("y")

        await bot.wait_for('message', check=check, timeout=10.0)
        # Add 2 to account for confirmation message and 1 to account for initial message
        how_many += 3
        # Purge limit is 120 so split into chunks
        how_many_120s = int(how_many / 120)
        how_many_ones = how_many - how_many_120s * 120
        if not private:
            for i in range(how_many_120s):
                await message.channel.purge(limit=120)
            await message.channel.purge(limit=how_many_ones)
        else:
            async for chat_message in message.channel.history(limit=how_many):
                if chat_message.author.id == bot.user.id:
                    await chat_message.delete()
    except asyncio.TimeoutError:
        return await message.channel.send('Sorry, you took too long.')
    await message.channel.send('!remove')


def get_valid_date(reminder_date, reminder_time):
    """
    Parses a date from date and time
    :param reminder_date: str, Date
    :param reminder_time: str, Time
    :return: Datetime timestamp, wanted date and time, None if incorrectly formatted
    """
    if reminder_date == "tomorrow":
        reminder_date = datetime.today() + relativedelta(days=1)
    elif reminder_date == "today":
        reminder_date = datetime.today().date()
    reminder_date_and_time = f"{reminder_date} {reminder_time.replace('.', ':')}"
    try:
        iso_date = dateutil.parser.parse(reminder_date_and_time)
    except dateutil.parser._parser.ParserError:
        raise commands.errors.UserInputError
    real_date = datetime.timestamp(datetime.fromisoformat(str(iso_date)))
    return real_date


def get_date_with_delta(time_amount, time_measure):
    """
    Gets a time with given parameters
    :param time_amount: int, Amount of time_measures
    :param time_measure: str, E.g. seconds, mins
    :return: Datetime timestamp
    """
    now = datetime.now()
    # Verify that valid time measure is used
    for time_name in list_of_time_measures:
        if time_measure in list_of_time_measures.get(time_name):
            correct_time_measure = time_name
    if correct_time_measure is None:
        return
    try:
        time_measure_to_use = {correct_time_measure: time_amount}
        notify_time = datetime.timestamp(now + relativedelta(**time_measure_to_use))
    except OSError:
        return
    return notify_time


def get_reminder_message_format(reminder):
    """
    Returns all useful info from a given reminder
    :param reminder: dict
    :return: str, str, int, int, str, str, str
    """
    time_to_remind = str(reminder.get("reminder_readable"))
    message_time = str(reminder.get("now_readable"))
    user_to_mention = str(f"<@{reminder.get('user_id')}>")
    user_id = int(reminder.get('user_id'))
    server_to_mention = int(reminder.get('server_id'))
    channel_to_mention = int(reminder.get('channel_id'))
    message_text = str(reminder.get('message_text'))
    message_command = str(reminder.get('message_commands'))
    return time_to_remind, user_to_mention, server_to_mention, channel_to_mention, message_text, message_command, \
           message_time, user_id


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


async def make_reminder(message, message_command, message_text, timestamp):
    """
    Makes a reminder with a given message and date
    :param message: MessageType
    :param message_command: str, '!reminder date/time'
    :param message_text: str
    :param timestamp: Datetime timestamp
    :return: nothing
    """
    user_id = str(message.author.id)
    timestamp_str = str(timestamp)
    if user_id not in list_of_reminders:
        list_of_reminders[user_id] = {}
    # Check that user doesn't have too many reminder already
    elif len(list_of_reminders.get(user_id)) > MAXIMUM_REMINDERS:
        return await message.channel.send("There are already too many reminders")
    # Make sure the same time doesn't exist multiple times
    while timestamp_str in list_of_reminders.get(user_id):
        timestamp += 0.00001
        timestamp_str = str(timestamp)
    server_id = message.guild.id
    channel_id = message.channel.id
    message_id = message.id
    now = datetime.now().timestamp()
    now_readable_time = datetime.fromtimestamp(now).replace(microsecond=0)
    reminder_readable_time = datetime.fromtimestamp(timestamp).replace(microsecond=0)
    list_of_reminders.get(user_id)[timestamp_str] = {"reminder_timestamp": str(timestamp),
                                                     "reminder_readable": str(reminder_readable_time),
                                                     "now_timestamp": str(now),
                                                     "now_readable": str(now_readable_time), "user_id": str(user_id),
                                                     "message_id": str(message_id), "channel_id": str(channel_id),
                                                     "server_id": str(server_id), "raw_message": str(message.content),
                                                     "message_commands": str(message_command),
                                                     "message_text": str(message_text)}
    with open(path_to_reminders + os.sep + f"{user_id}.json", "w", encoding='utf-8') as reminder_file:
        json.dump(list_of_reminders.get(user_id), reminder_file, indent=2, ensure_ascii=False)
    await message.channel.send(f"I will remind you on {reminder_readable_time}")


async def reminder_function():
    """
    Checks reminders every 10 seconds and send reminders
    :return: nothing
    """
    global reminder_task_started
    reminder_task_started = True
    while True:
        now = datetime.now().timestamp()
        if len(list_of_reminders) < 1:
            await asyncio.sleep(10)
            continue
        for user_id in list_of_reminders:
            first_reminder = float(sorted(list_of_reminders.get(user_id))[0])
            if now >= first_reminder:
                reminder = list_of_reminders.get(user_id).get(str(first_reminder))
                time_to_remind, user_to_mention, server_to_mention, channel_to_mention, message_text, message_command, \
                *_ = get_reminder_message_format(reminder)
                embed = discord.Embed(title=(time_to_remind), description=(message_command + "\n" + message_text))
                await bot.get_guild(server_to_mention).get_channel(channel_to_mention).send(content=user_to_mention,
                                                                                            embed=embed)
                list_of_reminders.get(user_id).pop(str(first_reminder))
                with open(path_to_reminders + os.sep + f"{user_id}.json", "w", encoding='utf-8') as reminder_file:
                    json.dump(list_of_reminders.get(user_id), reminder_file, indent=2, ensure_ascii=False)
            else:
                await asyncio.sleep(10)


@bot.group(aliases=["reminder"], pass_context=True)
async def remindme(ctx):
    if ctx.invoked_subcommand is None:
        print("No subcommand")


@remindme.command(aliases=["remove"], pass_context=True)
async def delete(ctx, index: int):
    message = ctx.message
    user_id = str(message.author.id)
    reminder_time = str(sorted(list_of_reminders.get(user_id))[index])
    reminder = list_of_reminders.get(user_id).get(reminder_time)
    *_, message_text, message_command, message_time, _ = get_reminder_message_format(reminder)
    message_to_send = f"```\n{index} : {message_time}:\n{message_command}\n{message_text}\n```"
    try:
        # Get confirmation. Sleep so that own message doesn't count as reply
        embed = discord.Embed(title="Confirm deletion of (y/n)",
                              description=message_to_send)
        await message.channel.send(content=f"<@{user_id}>", embed=embed)

        def check(m):
            return m.author == message.author

        confirmation = await bot.wait_for('message', check=check, timeout=10.0)
    except asyncio.TimeoutError:
        return await message.channel.send('Sorry, you took too long.')
    if str(confirmation.content).lower().startswith("y"):
        list_of_reminders.get(user_id).pop(reminder_time)
        with open(path_to_reminders + os.sep + f"{user_id}.json", "w", encoding='utf-8') as reminder_file:
            json.dump(list_of_reminders.get(user_id), reminder_file, indent=2, ensure_ascii=False)
        embed = discord.Embed(title=("Deleted"),
                              description=(message_to_send))
        await message.channel.send(content=f"<@{user_id}>", embed=embed)


@remindme.command(pass_context=True)
async def list(ctx):
    message = ctx.message
    author_id = message.author.id
    messages_to_send = []
    if str(author_id) not in list_of_reminders:
        await message.channel.send("You don't have any reminders")
        return
    for index, reminder_time in enumerate(sorted(list_of_reminders.get(str(author_id)))):
        reminder = list_of_reminders.get(str(author_id)).get(reminder_time)
        time_to_remind, user_to_mention, server_to_mention, channel_to_mention, message_text, message_command, \
        message_time, user_id = get_reminder_message_format(reminder)
        current_message = f"```\n{index} : {message_time} -> {time_to_remind}:\n{message_command}\n{message_text}" \
                          f"\n```"
        messages_to_send.append(current_message)
    list_of_valid_messages = craft_correct_length_messages(messages_to_send)
    for valid_message in list_of_valid_messages:
        embed = discord.Embed(title="List of reminders", description=(valid_message))
        await message.channel.send(content=f"<@{user_id}>", embed=embed)


@remindme.command(pass_context=True)
async def date(ctx, reminder_date: str, reminder_time: str, message_text: str = "", *args):
    reminder_timestamp = get_valid_date(reminder_date, reminder_time)
    message = ctx.message
    # Return if date is incorrect
    if reminder_timestamp is None:
        return await message.channel.send(INCORRECT_REMINDER_FORMAT)
    message_command = " ".join([COMMAND_PREFIX + str(ctx.command), reminder_date, reminder_time])
    await make_reminder(message, message_command, f"{message_text} {' '.join(args)}", reminder_timestamp)


@remindme.command(aliases=['time'], pass_context=True)
async def delta_time(ctx, time_amount: int, time_measure: str, message_text: str = "", *args):
    message = ctx.message
    reminder_timestamp = get_date_with_delta(time_amount, time_measure)
    message_command = " ".join([COMMAND_PREFIX + str(ctx.command), str(time_amount), time_measure])
    if reminder_timestamp is None:
        return await message.channel.send(INCORRECT_REMINDER_FORMAT)
    await make_reminder(message, message_command, f"{message_text} {' '.join(args)}", reminder_timestamp)


bot.run(token)
