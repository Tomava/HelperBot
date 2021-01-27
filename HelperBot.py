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

make_dirs()
description = ""
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='!', description=description, intents=intents)
load_dotenv(path_to_discord + os.sep + "HelperBoyToken.env")
token = os.getenv('DISCORD_TOKEN')


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    await bot.change_presence(activity=discord.Game(name='!help'))


@bot.event
async def on_command_error(ctx, error):
    if hasattr(ctx.command, 'on_error'):
        return
    if isinstance(error, commands.errors.UserInputError):
        await ctx.channel.send("Looks like your message wasn't formatted correctly.\nType !help to get correct formats")


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
    :return: Datetime, wanted date and time, None if incorrectly formatted
    """
    if reminder_date == "tomorrow":
        reminder_date = datetime.today() + relativedelta(days=1)
    elif reminder_date == "today":
        reminder_date = datetime.today().date()
    reminder_date = f"{reminder_date} {reminder_time.replace('.', ':')}"
    real_date = dateutil.parser.parse(reminder_date)
    return real_date


def get_date(time_amount, time_measure):
    """
    Gets a time with given parameters
    :param time_amount: int, Amount of time_measures
    :param time_measure: str, E.g. seconds, mins
    :return: Datetime
    """
    now = datetime.now().timestamp()
    # Verify that valid time measure is used
    for time in list_of_time_measures:
        if time_measure in list_of_time_measures.get(time):
            correct_time_measure = time
    if correct_time_measure is None:
        return
    elif correct_time_measure == "seconds":
        notify_time = datetime.timestamp(datetime.fromtimestamp(now) + relativedelta(seconds=time_amount))
    elif correct_time_measure == "minutes":
        notify_time = datetime.timestamp(datetime.fromtimestamp(now) + relativedelta(minutes=time_amount))
    elif correct_time_measure == "hours":
        notify_time = datetime.timestamp(datetime.fromtimestamp(now) + relativedelta(hours=time_amount))
    elif correct_time_measure == "days":
        notify_time = datetime.timestamp(datetime.fromtimestamp(now) + relativedelta(days=time_amount))
    elif correct_time_measure == "weeks":
        notify_time = datetime.timestamp(datetime.fromtimestamp(now) + relativedelta(weeks=time_amount))
    elif correct_time_measure == "months":
        notify_time = datetime.timestamp(datetime.fromtimestamp(now) + relativedelta(months=time_amount))
    elif correct_time_measure == "years":
        notify_time = datetime.timestamp(datetime.fromtimestamp(now) + relativedelta(years=time_amount))
    return notify_time


@bot.group(aliases=["reminder"], pass_context=True)
async def remindme(ctx):
    print(ctx.invoked_subcommand)
    if ctx.invoked_subcommand is None:
        print("NOT OK")


@remindme.command(aliases=["remove"], pass_context=True)
async def delete(ctx):
    print("delete")


@remindme.command(pass_context=True)
async def list(ctx):
    print("list")


@remindme.command(pass_context=True)
async def date(ctx, reminder_date: str, reminder_time: str = "12:00"):
    reminder_date = get_valid_date(reminder_date, reminder_time)
    message = ctx.message
    if reminder_date is None:
        await message.channel.send(incorrect_reminder_format)
    print(reminder_date)


@remindme.command(pass_context=True)
async def time(ctx, time_amount: int, time_measure: str):
    reminder_date = get_date(time_amount, time_measure)
    print(reminder_date)


bot.run(token)
