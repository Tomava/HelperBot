import discord
from discord.ext import commands
import asyncio
from datetime import datetime
from dateutil.relativedelta import relativedelta
import dateutil.parser
import json
from HelperBotConstants import *
import HelperBotFunctions


def get_date_with_delta(time_amount, time_measure, now=None):
    """
    Gets a time with given parameters
    :param time_amount: int, Amount of time_measures
    :param time_measure: str, E.g. seconds, mins
    :param now: Datetime, If given will use that
    :return: Datetime timestamp, None if invalid parameters
    """
    if now is None:
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
    :return: (user_to_mention), (time_to_remind, message_time), (user_id, server_id, channel_id, message_id),
    (message_text, message_command, raw_message), (interval_amount, interval_measure)
    """
    time_to_remind = str(reminder.get("reminder_readable"))
    time_to_remind_timestmap = float(reminder.get("reminder_timestamp"))
    message_time = str(reminder.get("now_readable"))
    message_timestamp = float(reminder.get("now_timestamp"))
    user_to_mention = str(f"<@{reminder.get('user_id')}>")
    user_id = int(reminder.get('user_id'))
    server_id = int(reminder.get('server_id'))
    channel_id = int(reminder.get('channel_id'))
    message_text = str(reminder.get('message_text'))
    message_command = str(reminder.get('message_commands'))
    message_id = str(reminder.get('message_id'))
    raw_message = str(reminder.get('raw_message'))
    interval_amount = reminder.get('interval_amount')
    interval_measure = reminder.get('interval_measure')
    # Change add_interval measure to empty string, so messages don't show "NoneNone"
    if interval_measure is None:
        interval_measure = ""
    if interval_amount is not None:
        interval_amount = int(interval_amount)
    return user_to_mention, (time_to_remind, time_to_remind_timestmap, message_time, message_timestamp), \
           (user_id, server_id, channel_id, message_id), (message_text, message_command, raw_message), \
           (interval_amount, str(interval_measure))


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

    async def get_reminder(self, message, index):
        """
        Gets reminder
        :param message: Message
        :param index: int, Index of the reminder
        :return: dict, Reminder
        """
        user_id = str(message.author.id)
        if user_id not in self.__list_of_reminders:
            await message.channel.send("You don't have any reminders!")
            return None
        try:
            reminder_time = str(sorted(self.__list_of_reminders.get(user_id))[index])
        except IndexError:
            await message.channel.send("You don't have that many reminders!")
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
        user_to_mention, (time_to_remind, time_to_remind_timestmap, message_time, message_timestamp), \
        (user_id, server_id, channel_id, message_id), (message_text, message_command, raw_message), \
        (interval_amount, interval_measure) = get_reminder_message_format(reminder)
        link = HelperBotFunctions.craft_message_link(server_id, channel_id, message_id)
        current_message = f"{index} : {message_time} -> {time_to_remind} (Interval: {interval_amount} " \
                          f"{interval_measure})\n{link}\n{message_command}\n{message_text}\n"
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
        reminder = await self.get_reminder(message, index)
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
            reminder = await self.get_reminder(message, index)
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

    async def delta_time(self, message, command, announce, time_amount: int, time_measure: str, message_text: str = "", *args):
        reminder_timestamp = get_date_with_delta(time_amount, time_measure)
        if reminder_timestamp is None:
            return await message.channel.send(REMINDER_HELP)
        return await self.make_reminder(message, command, f"{message_text} {' '.join(args)}", reminder_timestamp,
                                        announce)

    async def add_interval(self, message, reminder, interval: int, time_measure: str, announce=True):
        """
        Adds an interval to a given reminder
        :param message: message
        :param reminder: dict, Reminder
        :param interval: int, Time amount
        :param time_measure: str
        :param announce: bool, If true will send a message to announce adding interval
        :return: nothing
        """
        user_id = str(message.author.id)
        if reminder is None:
            return
        _, (_, reminder_timestamp, _, _), *_ = get_reminder_message_format(reminder)
        interval_timestamp = get_date_with_delta(interval, time_measure,
                                                 now=datetime.fromtimestamp(reminder_timestamp))
        if interval_timestamp is None:
            return await message.channel.send(REMINDER_HELP)
        # Check that interval is not too short
        if round(interval_timestamp - reminder_timestamp) < MINIMUM_INTERVAL_SECONDS:
            return await message.channel.send(f"That interval is too short (min {round(MINIMUM_INTERVAL_SECONDS / 60)}"
                                              f" minutes)")
        reminder["interval_amount"] = interval
        reminder["interval_measure"] = time_measure
        self.write_reminders_to_disk(user_id)
        if announce:
            _, (_, timestamp, _, _), *_ = get_reminder_message_format(reminder)
            index = sorted(self.__list_of_reminders.get(user_id)).index(str(timestamp))
            messages_to_send = [self.get_reminder_text(reminder, index)]
            title = "Interval added"
            content = f"<@{user_id}>"
            await HelperBotFunctions.send_embed_messages(messages_to_send, message.channel, title, content)

    async def remove_interval(self, message, reminder):
        reminder["interval_amount"] = None
        reminder["interval_measure"] = None
        user_id = str(message.author.id)
        self.write_reminders_to_disk(user_id)
        _, (_, timestamp, _, _), *_ = get_reminder_message_format(reminder)
        index = sorted(self.__list_of_reminders.get(user_id)).index(str(timestamp))
        messages_to_send = [self.get_reminder_text(reminder, index)]
        title = "Interval removed"
        content = f"<@{user_id}>"
        await HelperBotFunctions.send_embed_messages(messages_to_send, message.channel, title, content)

    async def make_reminder(self, message, message_command, message_text, timestamp, announce=True):
        """
        Makes a reminder with a given message and date
        :param message: MessageType
        :param message_command: str, '!reminder date/time'
        :param message_text: str
        :param timestamp: Datetime timestamp
        :param announce: bool, If true will send a message to announce adding interval
        :return: dict, Reminder
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
        if announce:
            index = sorted(self.__list_of_reminders.get(user_id)).index(timestamp_str)
            messages_to_send = [self.get_reminder_text(reminder, index)]
            title = "Reminder added"
            content = f"<@{user_id}>"
            await HelperBotFunctions.send_embed_messages(messages_to_send, message.channel, title, content)
        return reminder

    async def reminder_function(self):
        """
        Checks reminders every 10 seconds and send reminders
        :return: nothing
        """
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
                    user_to_mention, (time_to_remind, time_to_remind_timestmap, message_time, message_timestamp), \
                    (user_id, server_id, channel_id, message_id), (message_text, message_command, raw_message), \
                    (interval_amount, interval_measure) = get_reminder_message_format(reminder)
                    title = "Reminder"
                    channel = self.__bot.get_guild(server_id).get_channel(channel_id)
                    message_to_send = self.get_reminder_text(reminder, 0)
                    await HelperBotFunctions.send_embed_messages([message_to_send], channel,
                                                                 title, user_to_mention)
                    self.__list_of_reminders.get(str(user_id)).pop(str(first_reminder))
                    self.write_reminders_to_disk(str(user_id))
                    # Check if reminder has add_interval
                    if reminder.get("interval_amount") is not None:
                        message = await self.__bot.get_guild(server_id).get_channel(channel_id).fetch_message(message_id)
                        reminder = await self.delta_time(message, message_command, False, interval_amount,
                                                         interval_measure, message_text)
                        await self.add_interval(message, reminder, interval_amount, interval_measure, False)
            await asyncio.sleep(10)
