import discord
from discord.ext import commands
import asyncio
from datetime import datetime
from dateutil.relativedelta import relativedelta
import dateutil.parser
import json
from HelperBotConstants import *
import HelperBotFunctions


def get_date_with_delta(time_amount, time_measure):
    """
    Gets a time with given parameters
    :param time_amount: int, Amount of time_measures
    :param time_measure: str, E.g. seconds, mins
    :return: Datetime timestamp, None if invalid parameters
    """
    now = datetime.now()
    correct_time_measure = None
    # Verify that valid time measure is used
    for time_name in LIST_OF_TIME_MEASURES:
        if time_measure in LIST_OF_TIME_MEASURES.get(time_name):
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
    :return: time_to_remind, user_to_mention, server_id, channel_id, message_text, message_command, message_time,
    user_id, message_id, raw_message
    """
    time_to_remind = str(reminder.get("reminder_readable"))
    message_time = str(reminder.get("now_readable"))
    user_to_mention = str(f"<@{reminder.get('user_id')}>")
    user_id = int(reminder.get('user_id'))
    server_id = int(reminder.get('server_id'))
    channel_id = int(reminder.get('channel_id'))
    message_text = str(reminder.get('message_text'))
    message_command = str(reminder.get('message_commands'))
    message_id = str(reminder.get('message_id'))
    raw_message = str(reminder.get('raw_message'))
    interval = str(reminder.get('interval'))
    return time_to_remind, user_to_mention, server_id, channel_id, message_text, message_command, \
           message_time, user_id, message_id, raw_message, interval


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


def get_reminders():
    """
    Returns reminders as dictionary
    :return: dict
    """
    list_of_reminders = {}
    if len(os.listdir(PATH_TO_REMINDERS)) < 1:
        return {}
    for reminder_file_name in os.listdir(PATH_TO_REMINDERS):
        with open(PATH_TO_REMINDERS + os.sep + reminder_file_name, "r", encoding='utf-8') as reminder_file:
            # file name - .json
            list_of_reminders[reminder_file_name[:-5]] = dict(json.load(reminder_file))
    return list_of_reminders


class ReminderOrganizer:

    def __init__(self, bot):
        self.__bot = bot
        self.__list_of_reminders = get_reminders()
        self.__reminder_task_started = False

    async def start(self):
        # If it has already been started, return
        if self.__reminder_task_started:
            return
        self.__reminder_task_started = True
        await self.reminder_function()

    def get_started(self):
        return self.__reminder_task_started

    def get_list_of_reminders(self):
        return self.__list_of_reminders

    async def get_reminder(self, ctx, index):
        """
        Gets reminder
        :param ctx: Context, Context where the message was sent to
        :param index: int, Index of the reminder
        :return: dict, Reminder
        """
        user_id = str(ctx.message.author.id)
        if user_id not in self.__list_of_reminders:
            await ctx.message.channel.send("You don't have any reminders!")
            return None
        try:
            reminder_time = str(sorted(self.__list_of_reminders.get(user_id))[index])
        except IndexError:
            await ctx.message.channel.send("You don't have that many reminders!")
            return None
        return self.__list_of_reminders.get(user_id).get(reminder_time)

    def get_reminder_text(self, reminder, index):
        """
        Gets reminder as text
        :param reminder: dict, Reminder
        :param index: int, Index of the reminder
        :return: str, Reminder as text
        """
        if reminder is None:
            return ""
        time_to_remind, user_to_mention, server_id, channel_id, message_text, message_command, \
        message_time, user_id, message_id, raw_message, interval = get_reminder_message_format(reminder)
        link = HelperBotFunctions.craft_message_link(server_id, channel_id, message_id)
        current_message = f"{index} : {message_time} -> {time_to_remind} (Interval: {interval})\n{link}\n" \
                          f"{message_command}\n{message_text}\n"
        return current_message

    def write_reminders_to_disk(self, user_id):
        """
        Writes a given users reminders to disk
        :param user_id: str
        :return: nothing
        """
        with open(PATH_TO_REMINDERS + os.sep + f"{user_id}.json", "w", encoding='utf-8') as reminder_file:
            json.dump(self.__list_of_reminders.get(user_id), reminder_file, indent=2, ensure_ascii=False)

    async def reminder_help(self, ctx, incorrect_format=""):
        message = ctx.message
        await HelperBotFunctions.send_messages([incorrect_format, REMINDER_HELP], message.channel, make_code_format=True)

    async def delete(self, ctx, index: int):
        message = ctx.message
        user_id = str(message.author.id)
        reminder = await self.get_reminder(ctx, index)
        reminder_time = str(reminder.get("reminder_timestamp"))
        if reminder is None:
            return
        message_to_send = self.get_reminder_text(reminder, index)
        try:
            # Get confirmation
            await HelperBotFunctions.send_embed_messages([message_to_send], message.channel, "Confirm deletion of (y/n)"
                                                         , content=f"<@{user_id}>", make_code_format=True)

            def check(m):
                return m.author == message.author

            confirmation = await self.__bot.wait_for('message', check=check, timeout=10.0)
        except asyncio.TimeoutError:
            return await message.channel.send('Sorry, you took too long.')
        if str(confirmation.content).lower() == "y" or str(confirmation.content).lower() == "yes":
            self.__list_of_reminders.get(user_id).pop(reminder_time)
            self.write_reminders_to_disk(user_id)
            await HelperBotFunctions.send_embed_messages([message_to_send], message.channel, "Deleted"
                                                         , content=f"<@{user_id}>", make_code_format=True)

    async def list_reminders(self, ctx):
        message = ctx.message
        author_id = message.author.id
        messages_to_send = []
        if str(author_id) not in self.__list_of_reminders:
            await message.channel.send("You don't have any reminders")
            return
        for index, reminder_time in enumerate(sorted(self.__list_of_reminders.get(str(author_id)))):
            reminder = await self.get_reminder(ctx, index)
            current_message = self.get_reminder_text(reminder, index) + "\n"
            messages_to_send.append(current_message)
        title = "List of reminders"
        content = f"<@{author_id}>"
        await HelperBotFunctions.send_embed_messages(messages_to_send, message.channel, title, content)

    async def date(self, ctx, reminder_date: str, reminder_time: str, message_text: str = "", *args):
        reminder_timestamp = get_valid_date(reminder_date, reminder_time)
        message = ctx.message
        # Return if date is incorrect
        if reminder_timestamp is None:
            return await message.channel.send(REMINDER_HELP)
        message_command = " ".join([COMMAND_PREFIX + str(ctx.command), reminder_date, reminder_time])
        await self.make_reminder(message, message_command, f"{message_text} {' '.join(args)}", reminder_timestamp)

    async def delta_time(self, ctx, time_amount: int, time_measure: str, message_text: str = "", *args):
        message = ctx.message
        reminder_timestamp = get_date_with_delta(time_amount, time_measure)
        message_command = " ".join([COMMAND_PREFIX + str(ctx.command), str(time_amount), time_measure])
        if reminder_timestamp is None:
            return await message.channel.send(REMINDER_HELP)
        await self.make_reminder(message, message_command, f"{message_text} {' '.join(args)}", reminder_timestamp)

    async def interval(self, ctx, index: int, interval: int, time_measure: str):
        message = ctx.message
        user_id = str(message.author.id)
        reminder = await self.get_reminder(ctx, index)
        if reminder is None:
            return
        if get_date_with_delta(interval, time_measure) is None:
            return await message.channel.send(REMINDER_HELP)
        reminder["interval"] = f"{interval} {time_measure}"
        self.write_reminders_to_disk(user_id)
        messages_to_send = [self.get_reminder_text(reminder, index)]
        title = "Interval added"
        content = f"<@{user_id}>"
        await HelperBotFunctions.send_embed_messages(messages_to_send, message.channel, title, content)

    async def make_reminder(self, message, message_command, message_text, timestamp):
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
        if user_id not in self.__list_of_reminders:
            self.__list_of_reminders[user_id] = {}
        # Check that user doesn't have too many reminder already
        elif len(self.__list_of_reminders.get(user_id)) > MAXIMUM_REMINDERS:
            return await message.channel.send("There are already too many reminders")
        # Make sure the same time doesn't exist multiple times
        while timestamp_str in self.__list_of_reminders.get(user_id):
            timestamp += 0.00001
            timestamp_str = str(timestamp)
        server_id = message.guild.id
        channel_id = message.channel.id
        message_id = message.id
        now = datetime.now().timestamp()
        now_readable_time = datetime.fromtimestamp(now).replace(microsecond=0).strftime(DATE_FORMAT)
        reminder_readable_time = datetime.fromtimestamp(timestamp).replace(microsecond=0).strftime(DATE_FORMAT)
        self.__list_of_reminders.get(user_id)[timestamp_str] = {"reminder_timestamp": str(timestamp),
                                                                "reminder_readable": str(reminder_readable_time),
                                                                "now_timestamp": str(now),
                                                                "now_readable": str(now_readable_time),
                                                                "user_id": str(user_id),
                                                                "message_id": str(message_id),
                                                                "channel_id": str(channel_id),
                                                                "server_id": str(server_id),
                                                                "raw_message": str(message.content),
                                                                "message_commands": str(message_command),
                                                                "message_text": str(message_text)}
        self.write_reminders_to_disk(user_id)
        reminder = self.__list_of_reminders.get(user_id).get(timestamp_str)
        index = sorted(self.__list_of_reminders.get(user_id)).index(timestamp_str)
        messages_to_send = [self.get_reminder_text(reminder, index)]
        title = "Reminder added"
        content = f"<@{user_id}>"
        await HelperBotFunctions.send_embed_messages(messages_to_send, message.channel, title, content)

    async def reminder_function(self):
        """
        Checks reminders every 10 seconds and send reminders
        :return: nothing
        """
        global reminder_task_started
        reminder_task_started = True
        while True:
            now = datetime.now().timestamp()
            # If reminder list is empty
            if len(self.__list_of_reminders) < 1:
                await asyncio.sleep(10)
                continue
            for user_id in self.__list_of_reminders:
                # If user has no reminders
                if len(self.__list_of_reminders.get(user_id)) < 1:
                    continue
                first_reminder = float(sorted(self.__list_of_reminders.get(user_id))[0])
                if now >= first_reminder:
                    reminder = self.__list_of_reminders.get(user_id).get(str(first_reminder))
                    time_to_remind, user_to_mention, server_id, channel_id, message_text, message_command, \
                    message_time, user_id, message_id, raw_message, interval = get_reminder_message_format(reminder)
                    title = "Reminder"
                    channel = self.__bot.get_guild(server_id).get_channel(channel_id)
                    message_to_send = self.get_reminder_text(reminder, 0)
                    await HelperBotFunctions.send_embed_messages([message_to_send], channel,
                                                                 title, user_to_mention)
                    self.__list_of_reminders.get(str(user_id)).pop(str(first_reminder))
                    self.write_reminders_to_disk(str(user_id))
            await asyncio.sleep(10)
