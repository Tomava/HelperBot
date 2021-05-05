import discord
import logging
from discord.ext import commands
import asyncio
import random
from dotenv import load_dotenv
import json
import time
from image_downloader import download_image

from HelperBotConstants import *
import HelperBotFunctions
import HelperBotReminderOrganizer
from HelperBotCustomizations import *

logging.basicConfig(level=logging.INFO)
HelperBotFunctions.make_dirs()
description = ""
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix=COMMAND_PREFIX, description=description, intents=intents)
load_dotenv(PATH_TO_TOKEN)
token = os.getenv('DISCORD_TOKEN')
reminder = HelperBotReminderOrganizer.ReminderOrganizer(bot)


# TODO: Use scheduler on reminders


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    await bot.change_presence(activity=discord.Game(name='!reminder_help'))
    if not reminder.get_started():
        await reminder.start()


@bot.event
async def on_command_error(ctx, error):
    if hasattr(ctx.command, 'on_error'):
        print("Error:", error)
    elif isinstance(error, commands.errors.UserInputError):
        await ctx.channel.send("Looks like your message wasn't formatted correctly.\n"
                               "Type !reminder help to get correct formats")
    else:
        print("Error:", error)
        raise error


@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id != bot.user.id:
        msg = await bot.get_guild(payload.guild_id).get_channel(payload.channel_id).fetch_message(payload.message_id)
        await msg.add_reaction(payload.emoji)


@bot.event
async def on_raw_reaction_remove(payload):
    if payload.user_id != bot.user.id:
        msg = await bot.get_guild(payload.guild_id).get_channel(payload.channel_id).fetch_message(payload.message_id)
        await msg.remove_reaction(payload.emoji, bot.user)


@bot.listen()
async def on_message(message):
    # Don't react to own messages
    if message.author.id == bot.user.id:
        return
    message_content = message.content
    new_message_content = HelperBotFunctions.clean_youtube_links(message_content)
    # If message was changed, send new one and remove old
    if new_message_content != message_content:
        # Remove message
        await message.delete()
        # Send new message
        await message.channel.send(new_message_content)
    # Respond to a tag
    if bot.user.mentioned_in(message):
        await HelperBotFunctions.send_messages([f"{message.author.mention}\n",
                                                random.choice(LIST_OF_RESPONSES_TO_TAGS)], message.channel)


@bot.command(aliases=["remove"], description="Deletes given amount of messages")
async def delete(ctx, how_many: int):
    message = ctx.message
    private = False
    if str(message.channel.type) == "private":
        private = True
    if not private and (message.channel.name == "general"):
        await message.channel.send("Deleting messages on channel 'general' is disabled.")
        return
    # Make sure there's not too many
    if how_many > MAXIMUM_REMOVED_MESSAGES:
        await message.channel.send(f"That's too many! {MAXIMUM_REMOVED_MESSAGES} is the limit")
        return
    try:
        # Get confirmation
        await HelperBotFunctions.send_messages(["Confirm deletion of ", how_many, " messages (y/n)"], message.channel)

        def check(m):
            return m.author == message.author and (str(m.content).lower() == "y" or str(m.content).lower() == "yes")

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


@bot.group(name="reminder", aliases=["remindme"], pass_context=True)
async def remindme(ctx):
    if ctx.invoked_subcommand is None:
        await reminder.reminder_help(ctx, "Your message wasn't formatted correctly\n")


@remindme.command(name="help", pass_context=True, description="Help for reminders")
async def reminder_help(ctx):
    await reminder.reminder_help(ctx)


@remindme.command(name="remove", aliases=["delete"], pass_context=True, description="Deletes reminder at given index")
async def delete(ctx, index: int):
    await reminder.delete(ctx, index)


@remindme.command(name="list", pass_context=True, description="Lists all reminders")
async def list_reminders(ctx):
    await reminder.list_reminders(ctx)


@remindme.command(name="date", aliases=["on", "at"], pass_context=True, description="Reminds at a given date and time")
async def date(ctx, reminder_date: str, reminder_time: str, message_text: str = "", *args):
    await reminder.date(ctx, reminder_date, reminder_time, message_text, *args)


@remindme.command(name="time",  aliases=["in"], pass_context=True, description="Reminds in a given amount amount of "
                                                                               "[Time Measures]")
async def delta_time(ctx, time_amount: int, time_measure: str, message_text: str = "", *args):
    message_command = " ".join([COMMAND_PREFIX + str(ctx.command), str(time_amount), time_measure])
    await reminder.delta_time(ctx.message, message_command, True, time_amount, time_measure, message_text, *args)


@remindme.command(name="timemeasures", pass_context=True, description="List of valid time measures")
async def time_measures(ctx):
    message = "Time measures\n\n"
    max_width = len(max(LIST_OF_TIME_MEASURES.keys(), key=lambda k: len(LIST_OF_TIME_MEASURES.get(k)))) + 1
    for key in LIST_OF_TIME_MEASURES:
        message += f"{key + ':':<{max_width}}\t {', '.join(LIST_OF_TIME_MEASURES.get(key))}\n"
    message += f"\n{'date:':<{max_width}}\t today, tommorrow"
    await HelperBotFunctions.send_messages([message], ctx.message.channel, make_code_format=True)


@remindme.command(name="add_interval", aliases=["interval", "every"], pass_context=True,
                  description="Adds an interval of every x [Time Measure] to a reminder")
async def add_interval(ctx, index: int, interval: int, time_measure: str):
    this_reminder = await reminder.get_reminder(ctx.message, index)
    await reminder.add_interval(ctx.message, this_reminder, interval, time_measure)


@remindme.command(name="remove_interval", pass_context=True, description="Removes an interval from a reminder")
async def remove_interval(ctx, index: int):
    this_reminder = await reminder.get_reminder(ctx.message, index)
    await reminder.remove_interval(ctx.message, this_reminder)


@bot.command(name="noclean", aliases=["nc"], description="Don't clean youtube link")
async def noclean(ctx):
    return False


@bot.command(name="answer", description="I will try to answer you question")
async def answer(ctx):
    await HelperBotFunctions.send_messages([random.choice(LIST_OF_RESPONSES_TO_QUESTIONS)], ctx.message.channel)


@bot.command(name="history", description="Learn about my history")
async def history(ctx):
    message = HelperBotFunctions.get_history_message()
    await ctx.message.channel.send(message)


@bot.command(name="roll", description="Roll a roulette")
async def roll(ctx):
    index = random.randint(0, (len(LIST_OF_ROLLS) - 1))
    await ctx.channel.send(LIST_OF_ROLLS[index])


@bot.command(name="game", description="Notify others to play with you")
async def game(ctx, *game_name):
    message = ctx.message
    message_sender = message.author.nick
    # If author has no nickname, use their username instead
    if message_sender is None:
        message_sender = message.author.name
    if len(game_name) == 0:
        message_to_send = f"@everyone\n{message_sender} wants to game with you"
    else:
        message_to_send = f"@everyone\n{message_sender} wants to play {' '.join(game_name)} with you"
    await HelperBotFunctions.send_messages([message_to_send], message.channel)


@bot.command(name="random", description="Get x amount of random messages from current channel's history")
async def random_messages(ctx, how_many: int):
    channel = ctx.message.channel
    # Too many messages
    if how_many > MAXIMUM_RANDOM_MESSAGES:
        return await channel.send(f"That's too many (max {MAXIMUM_RANDOM_MESSAGES})!")
    channel_created = channel.created_at.timestamp()
    latest = channel.last_message.created_at.timestamp()
    # Get a random time between the channel creation and latest message
    # (Much quicker than fetching all messages)
    time_to_fetch = random.uniform(channel_created, latest)
    time_to_fetch = datetime.fromtimestamp(time_to_fetch)
    messages_after = await channel.history(after=time_to_fetch, limit=2 * how_many,
                                           oldest_first=True).flatten()
    messages_before = await channel.history(before=time_to_fetch, limit=2 * how_many,
                                            oldest_first=True).flatten()
    # Add messages to a list
    all_messages = []
    all_messages.extend(messages_before)
    all_messages.extend(messages_after)
    # If there are less than how_many messages in the channel
    if len(all_messages) <= how_many:
        starting_index = 0
    else:
        # Randomize a starting index (must have how_many amount of messages after it)
        starting_index = random.randint(0, len(all_messages) - how_many - 1)
    list_of_messages = []
    for message in all_messages[starting_index:starting_index + how_many]:
        author = message.author.name
        created_readable = HelperBotFunctions.utc_to_local_datetime(datetime.fromisoformat(str(message.created_at)))\
            .replace(microsecond=0)
        content = message.content
        message_to_send = f"**{author} at {created_readable}:**\n{content}\n"
        list_of_messages.append(message_to_send)
    # Get a random colour
    random_colour = discord.Colour.from_rgb(r=random.randint(0, 255), g=random.randint(0, 255),
                                            b=random.randint(0, 255))
    message_link = HelperBotFunctions.craft_message_link(ctx.message.guild.id, channel.id, ctx.message.id)
    await HelperBotFunctions.send_embed_messages(list_of_messages, channel, "Random convo", message_link, random_colour)


@bot.group(name="admin", pass_context=True)
async def admin(ctx):
    roles = ctx.message.author.roles
    role_names = [role.name for role in roles]
    if "Admin" not in role_names:
        return await ctx.message.channel.send("You're not an admin!")
    if ctx.invoked_subcommand is None:
        await admin_help(ctx)


@admin.command(name="help", pass_context=True, description="Help for admin")
async def admin_help(ctx):
    await HelperBotFunctions.send_messages([ADMIN_HELP], ctx.message.channel, make_code_format=True)


bot.run(token)
