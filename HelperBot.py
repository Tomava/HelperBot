import discord
from discord.ext import commands
import asyncio
import random
from dotenv import load_dotenv
import json
import time
from image_downloader import download_image
from HelperBotConstants import *
import HelperBotFunctions
import Reminder

HelperBotFunctions.make_dirs()
description = ""
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix=COMMAND_PREFIX, description=description, intents=intents)
load_dotenv(PATH_TO_DISCORD + os.sep + "HelperBoyToken.env")
token = os.getenv('DISCORD_TOKEN')
reminder_task_started = False
reminder = Reminder.Reminder(bot)


# TODO: Make reminder class that has self.bot and list_of_reminders as attributes
# TODO: Use scheduler on reminders
# TODO: Add weekday to reminders
# TODO: def start()


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
        await reminder.start()


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


@bot.group(aliases=["reminder"], pass_context=True)
async def remindme(ctx):
    if ctx.invoked_subcommand is None:
        print("No subcommand")


@remindme.command(aliases=["remove"], pass_context=True)
async def delete(ctx, index: int):
    await reminder.delete(ctx, index)


@remindme.command(aliases=["list"], pass_context=True)
async def list_reminders(ctx):
    await reminder.list_reminders(ctx)


@remindme.command(pass_context=True)
async def date(ctx, reminder_date: str, reminder_time: str, message_text: str = "", *args):
    await reminder.date(ctx, reminder_date, reminder_time, message_text, *args)


@remindme.command(aliases=['time'], pass_context=True)
async def delta_time(ctx, time_amount: int, time_measure: str, message_text: str = "", *args):
    await reminder.delta_time(ctx, time_amount, time_measure, message_text, *args)


bot.run(token)