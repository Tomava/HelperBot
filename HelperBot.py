import discord
import logging
from discord.ext import commands
import asyncio
import typing
import random
from dotenv import load_dotenv
import json
import time

from HelperBotConstants import *
import HelperBotFunctions
import HelperBotReminderOrganizer
from HelperBotCustomizations import *

logging.basicConfig(level=logging.INFO)
HelperBotFunctions.make_dirs()
# This will show in !help
description = ""
intents = discord.Intents.all()
intents.members = True
bot = commands.Bot(command_prefix=COMMAND_PREFIX, description=description, intents=intents, case_insensitive=True,
                   activity=discord.Game(name=f'{COMMAND_PREFIX}help'))
load_dotenv(PATH_TO_TOKEN)
token = os.getenv('DISCORD_TOKEN')
reminder = HelperBotReminderOrganizer.ReminderOrganizer(bot)


# TODO: Use scheduler on reminders
# TODO: Add requirements.txt


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    if not reminder.get_started():
        await reminder.start()


@bot.event
async def on_command_error(ctx, error):
    if hasattr(ctx.command, 'on_error'):
        print("Error:", error)
    # Wrong format
    elif isinstance(error, commands.errors.UserInputError):
        await HelperBotFunctions.send_messages(["Looks like your message wasn't formatted correctly.\n"
                                                f"Type {COMMAND_PREFIX}help to get correct formats."], ctx.channel)
    # Command not found
    elif isinstance(error, commands.errors.CommandNotFound):
        await HelperBotFunctions.send_messages([f"That's not a valid command.\nType "
                                                f"{COMMAND_PREFIX}help to get correct formats."], ctx.channel)
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
        await HelperBotFunctions.send_messages([new_message_content], message.channel)
    # Respond to a tag
    if bot.user.mentioned_in(message):
        await HelperBotFunctions.send_messages([f"{message.author.mention}\n",
                                                random.choice(LIST_OF_RESPONSES_TO_TAGS)], message.channel)


@bot.group(name="admin", pass_context=True, case_insensitive=True)
async def admin(ctx):
    roles = ctx.message.author.roles
    role_names = [role.name for role in roles]
    if "Admin" not in role_names:
        return await HelperBotFunctions.send_messages(["You're not an admin!"], ctx.message.channel)
    if ctx.invoked_subcommand is None:
        await admin_help(ctx)


@bot.group(name="reminder", aliases=["remindme"], pass_context=True, case_insensitive=True)
async def remindme(ctx):
    if ctx.invoked_subcommand is None:
        await reminder.reminder_help(ctx, "Your message wasn't formatted correctly\n")


@bot.command(aliases=["remove"], description="Deletes given amount of messages")
async def delete(ctx, how_many: int):
    message = ctx.message
    private = False
    if str(message.channel.type) == "private":
        private = True
    if not private and (message.channel.name == "general"):
        await HelperBotFunctions.send_messages(["Deleting messages on channel 'general' is disabled."], message.channel)
        return
    # Make sure there's not too many
    if how_many > MAXIMUM_REMOVED_MESSAGES:
        await HelperBotFunctions.send_messages(
            [HelperBotFunctions.craft_too_many_warning_message(MAXIMUM_REMOVED_MESSAGES)], message.channel)
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
        return await HelperBotFunctions.send_messages(['Sorry, you took too long.'], message.channel)


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


@remindme.command(name="time", aliases=["in"], pass_context=True, description="Reminds in a given amount amount of "
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
    await HelperBotFunctions.send_messages([message], ctx.message.channel)


@bot.command(name="roll", description="Roll a roulette")
async def roll(ctx):
    index = random.randint(0, (len(LIST_OF_ROLLS) - 1))
    await HelperBotFunctions.send_messages([LIST_OF_ROLLS[index]], ctx.message.channel)


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
        return await HelperBotFunctions.send_messages(
            [HelperBotFunctions.craft_too_many_warning_message(MAXIMUM_RANDOM_MESSAGES)], channel)
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
        created_readable = HelperBotFunctions.utc_to_local_datetime(datetime.fromisoformat(str(message.created_at))) \
            .replace(microsecond=0)
        content = message.content
        message_to_send = f"**{author} at {created_readable}:**\n{content}\n"
        list_of_messages.append(message_to_send)
    # Get a random colour
    random_colour = discord.Colour.from_rgb(r=random.randint(0, 255), g=random.randint(0, 255),
                                            b=random.randint(0, 255))
    message_link = HelperBotFunctions.craft_message_link(ctx.message.guild.id, channel.id, ctx.message.id)
    await HelperBotFunctions.send_embed_messages(list_of_messages, channel, "Random convo", message_link, random_colour)


@admin.command(name="help", pass_context=True, description="Help for admin")
async def admin_help(ctx):
    await HelperBotFunctions.send_messages([ADMIN_HELP], ctx.message.channel, make_code_format=True)


@admin.command(name="count", pass_context=True, description="Count to x with about a second between messages. "
                                                            "Use !count stop to stop counting")
async def count(ctx, how_many: int):
    if how_many > MAXIMUM_COUNT:
        return await HelperBotFunctions.send_messages(
            [HelperBotFunctions.craft_too_many_warning_message(MAXIMUM_COUNT)], ctx.message.channel)
    for i in range(1, how_many + 1):
        await HelperBotFunctions.send_messages([f"{i}"], ctx.message.channel)
        await asyncio.sleep(1)


# TODO: This
@admin.command(name="archive", pass_context=True, description="Create an archive of this server, if argument \"True\" "
                                                              "is given also downloads all attachment files")
async def archive(ctx, download_attachments: typing.Optional[bool]):
    message = ctx.message
    guild = message.guild
    path_to_guild = PATH_TO_ARCHIVES + os.sep + f"{guild.id}_{guild.name}" + os.sep + \
                    f"{datetime.strftime(datetime.today(),'%Y-%m-%d_%H%M%S')}"
    if not os.path.exists(path_to_guild):
        os.makedirs(path_to_guild)
    # Create empty file
    if not os.path.isfile(PATH_TO_ATTACHMENT_ARCHIVE_LOG):
        with open(PATH_TO_ATTACHMENT_ARCHIVE_LOG, "w", encoding=ENCODING) as file:
            pass
    if download_attachments:
        await message.channel.send("Archiving server with attachments. This might take a while")
    else:
        await message.channel.send("Archiving server. This might take a while")
    sent_message = await message.channel.send("Archiving")
    channels = message.guild.text_channels
    message_amount = 0
    all_attachments = {}
    for channel in channels:
        if channel not in all_attachments:
            all_attachments[channel] = []
        await sent_message.edit(content=f"Archiving '{channel.name}'")
        channel_data = {}
        messages = await channel.history(limit=10, oldest_first=True).flatten()
        for message_to_archive in messages:
            message_amount += 1
            embeds = []
            # Get info from each embed
            for embed in message_to_archive.embeds:
                current_embed = {"title": embed.title, "description": embed.description, "embed_url": embed.url,
                                 "image_url": embed.image.url, "fields": []}
                # There can be multiple fields in one embed
                for field in embed.fields:
                    current_embed.get("fields").append({field.name: field.value})
                # Remove empty fields
                for item in current_embed:
                    if str(current_embed.get(item)) == "Embed.Empty":
                        current_embed[item] = ""
                embeds.append(current_embed)
            pinned = message_to_archive.pinned
            reactions = message_to_archive.reactions
            attachments = []
            for attachment in message_to_archive.attachments:
                attachments.append({"attachment_id": attachment.id, "attachment_url": attachment.url,
                                    "filename": attachment.filename, "size": attachment.size,
                                    "type": attachment.content_type})
                all_attachments.get(channel).append({"attachment": attachment, "attachment_id": attachment.id,
                                                    "attachment_url": attachment.url, "filename": attachment.filename,
                                                    "size": attachment.size, "type": attachment.content_type})
            created = datetime.timestamp(message_to_archive.created_at)
            if message_to_archive.edited_at is not None:
                edited = datetime.timestamp(message_to_archive.edited_at)
            else:
                edited = ""
            author = message_to_archive.author.name
            message_id = message_to_archive.id
            # Add all data to channel data by message id
            channel_data[message_id] = {
                'message_id': str(message_id),
                'created_utc': created,
                'edited': edited,
                'created_readable': str(HelperBotFunctions.utc_to_local_datetime(message_to_archive.created_at)),
                'author': author,
                'content': message_to_archive.content,
                'embeds': embeds,
                'reactions': str(reactions),
                'attachments': attachments,
                'pinned': pinned,
                'raw': str(message_to_archive)
            }
        # Write channel's json
        with open(path_to_guild + os.sep + f"{channel.id}_{channel.name}.json", "w", encoding=ENCODING) as file:
            json.dump(channel_data, file, indent=2, ensure_ascii=False)

    # Downloading attachments
    attachment_sizes = 0
    failed_to_download = 0
    already_downloaded = []
    downloaded_attachment_ids = []
    attachment_ids = []
    with open(PATH_TO_ATTACHMENT_ARCHIVE_LOG, "r", encoding=ENCODING) as file:
        for line in file.readlines():
            attachment_ids.append(line.strip())
    if download_attachments:
        for channel in all_attachments:
            await sent_message.edit(content=f"Downloading attachments for '{channel.name}'")
            folder_path = PATH_TO_ARCHIVES + os.sep + f"{guild.id}_{guild.name}" + os.sep + "attachments" + \
                          os.sep + f"{channel.id}_{channel.name}"
            for attachment in all_attachments.get(channel):
                attachment_id = attachment.get("attachment_id")
                # Check if attachment has already been downloaded
                if str(attachment_id) in attachment_ids:
                    already_downloaded.append(attachment_id)
                    continue
                if not os.path.exists(folder_path):
                    os.makedirs(folder_path)
                attachment_filename = attachment.get("filename")
                extension = f".{attachment_filename.split('.')[-1]}"
                if attachment_filename.count(".") == 0:
                    extension = ""
                file_path = folder_path + os.sep + str(attachment_id) + extension
                try:
                    await attachment.get("attachment").save(file_path)
                    downloaded_attachment_ids.append(f"{attachment_id}\n")
                    attachment_sizes += attachment.get("size")
                except:
                    failed_to_download += 1
        # Append to file
        with open(PATH_TO_ATTACHMENT_ARCHIVE_LOG, "a", encoding=ENCODING) as file:
            file.writelines(downloaded_attachment_ids)

    await sent_message.delete()
    message_to_send = f"Archiving of {message_amount} messages"
    if download_attachments:
        formatted_size, power_label = HelperBotFunctions.format_bytes(attachment_sizes)
        message_to_send += f" and {len(downloaded_attachment_ids)} attachments completed with a total size of " \
                           f"{formatted_size:.2f} {power_label} ({len(already_downloaded)} were already downloaded)"
        if failed_to_download != 0:
            message_to_send += f" [{failed_to_download} attachments failed to download]"
    await message.channel.send(message_to_send)

bot.run(token)
