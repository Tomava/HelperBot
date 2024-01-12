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
        iso_date = dateutil.parser.parse(reminder_date_and_time, dayfirst=True)
    except dateutil.parser._parser.ParserError:
        raise commands.errors.UserInputError
    real_date = datetime.timestamp(datetime.fromisoformat(str(iso_date)))
    return real_date


def get_reminders():
    """
    Returns reminders as dictionary
    :return: dict
    """
    all_reminders = {}
    if len(os.listdir(PATH_TO_REMINDERS)) < 1:
        return {}
    for reminder_file_name in os.listdir(PATH_TO_REMINDERS):
        with open(PATH_TO_REMINDERS + os.sep + reminder_file_name, "r", encoding=ENCODING) as reminder_file:
            file_data = json.load(reminder_file)
        for reminder_json in file_data:
            reminder = Reminder()
            reminder.load_from_json(reminder_json)
            user_id = str(reminder.get_user_id())
            if user_id not in all_reminders:
                all_reminders[user_id] = []
            all_reminders.get(user_id).append(reminder)
    return all_reminders

def get_readable_time_from_timestamp(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp).replace(microsecond=0).strftime(DATE_FORMAT)

class Reminder:

    def __init__(self) -> None:
        self.time_to_remind_timestamp: float
        self.message_timestamp: float
        self.user_to_mention: str
        self.user_id: int
        self.server_id: int
        self.channel_id: int
        self.message_text: str
        self.message_command: str
        self.message_id: str
        self.raw_message: str
        self.interval_amount: None | int
        self.interval_measure: None | str
        self.failed_count: None | int
        self.interval_exists = False

    def load_from_json(self, reminder_json: dict) -> None:
        self.time_to_remind_timestamp = float(reminder_json.get("reminder_timestamp"))
        self.message_timestamp = float(reminder_json.get("now_timestamp"))
        self.user_id = int(reminder_json.get("user_id"))
        self.user_to_mention = str(f"<@{self.user_id}>")
        self.server_id = int(reminder_json.get("server_id"))
        self.channel_id = int(reminder_json.get("channel_id"))
        self.message_text = str(reminder_json.get("message_text"))
        self.message_command = str(reminder_json.get("message_commands"))
        self.message_id = str(reminder_json.get("message_id"))
        self.raw_message = str(reminder_json.get("raw_message"))
        self.interval_amount = reminder_json.get("interval_amount")
        self.interval_measure = reminder_json.get("interval_measure")
        self.failed_count = reminder_json.get("failed_count")
        self.set_additionals()

    def set_additionals(self) -> None:
        self.interval_exists = False

        if self.interval_measure is not None and self.interval_amount is not None:
            self.interval_exists = True
            self.interval_amount = int(self.interval_amount)

        if self.failed_count is None:
            self.failed_count = 0
        else:
            self.failed_count = int(self.failed_count)

    def get_interval_text(self) -> str:
        if not self.has_interval():
            return ""
        return f" (Interval: {self.interval_amount} {self.interval_measure})"

    def get_as_text(self, index) -> str:
        link = HelperBotFunctions.craft_message_link(self.server_id, self.channel_id, self.message_id)
        readable_message_time = get_readable_time_from_timestamp(self.message_timestamp)
        readable_reminder_time = get_readable_time_from_timestamp(self.time_to_remind_timestamp)
        message = f"> **{index} : {readable_message_time} -> {readable_reminder_time}{self.get_interval_text()}\n> {link}**" \
                        f"\n{self.message_command}\n{self.message_text}\n"
        return message
    
    def get_user_id(self) -> int:
        return self.user_id
    
    def get_reminder_timestamp(self) -> float:
        return self.time_to_remind_timestamp
    
    def get_server_id(self) -> int:
        return self.server_id

    def get_channel_id(self) -> int:
        return self.channel_id
    
    def get_user_to_mention(self) -> str:
        return self.user_to_mention
    
    def has_interval(self) -> bool:
        return self.interval_exists
    
    def get_interval_amount(self) -> int:
        return self.interval_amount

    def get_interval_measure(self) -> str:
        return self.interval_measure
    
    def get_failed_count(self) -> int:
        return self.failed_count
    
    def increase_failed_count(self) -> None:
        self.failed_count += 1

    def set_reminder_time(self, time_to_remind_timestamp: float):
        self.time_to_remind_timestamp = time_to_remind_timestamp

    def set_interval(self, interval_amount: int, interval_measure: str) -> None:
        self.interval_amount = interval_amount
        self.interval_measure = interval_measure
        self.interval_exists = True

    def remove_interval(self) -> None:
        self.interval_exists = False
        self.interval_amount = None
        self.interval_measure = None

    def to_save_object(self) -> dict:
        save_object = {"reminder_timestamp": str(self.get_reminder_timestamp()), "now_timestamp": str(self.message_timestamp), "user_id": str(self.user_id), "message_id": str(self.message_id), "channel_id": str(self.channel_id), "server_id": str(self.server_id), "raw_message": str(self.raw_message), "message_commands": str(self.message_command), "message_text": str(self.message_text)}
        if self.has_interval():
            save_object["interval_amount"] = self.interval_amount
            save_object["interval_measure"] = self.interval_measure
        if self.failed_count > 0:
            save_object["failed_count"] = self.failed_count
        return save_object

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

    async def get_reminder_with_index(self, message, index):
        """
        Gets reminder
        :param message: Message
        :param index: int, Index of the reminder
        :return: Reminder, Reminder
        """
        user_id = str(message.author.id)
        if user_id not in self.__list_of_reminders:
            await message.channel.send("You don't have any reminders!")
            return None
        reminders = self.__list_of_reminders.get(user_id)
        if len(reminders) <= index:
            await message.channel.send("You don't have that many reminders!")
            return None
        return reminders[index]

    def write_reminders_to_disk(self, user_id):
        """
        Writes a given users reminders to disk
        :param user_id: str
        :return: nothing
        """
        reminders = [reminder.to_save_object() for reminder in self.__list_of_reminders.get(user_id)]
        with open(PATH_TO_REMINDERS + os.sep + f"{user_id}.json", "w", encoding=ENCODING) as reminder_file:
            json.dump(reminders, reminder_file, indent=2, ensure_ascii=False)

    async def reminder_help(self, ctx, incorrect_format=""):
        message = ctx.message
        await HelperBotFunctions.send_messages([incorrect_format, REMINDER_HELP], message.channel,
                                               make_code_format=True)

    async def delete(self, ctx, index: int):
        message = ctx.message
        user_id = str(message.author.id)
        reminder = await self.get_reminder_with_index(message, index)

        if reminder is None:
            return

        message_to_send = reminder.get_as_text(index)
        try:
            # Get confirmation
            await HelperBotFunctions.send_embed_messages(
                [message_to_send], message.channel, "Confirm deletion of (y/n)", content=f"<@{user_id}>")

            def check(m):
                return m.author == message.author

            confirmation = await self.__bot.wait_for("message", check=check, timeout=10.0)
        except asyncio.TimeoutError:
            return await message.channel.send("Sorry, you took too long.")
        if str(confirmation.content).lower().startswith("y"):
            self.remove_reminder(user_id, reminder)
            await HelperBotFunctions.send_embed_messages([message_to_send], message.channel, "Deleted"
                                                         , content=f"<@{user_id}>")

    async def list_reminders(self, ctx):
        message = ctx.message
        author_id = str(message.author.id)
        messages_to_send = []
        if author_id not in self.__list_of_reminders:
            await message.channel.send("You don't have any reminders")
            return
        for index, reminder in enumerate(self.__list_of_reminders.get(author_id)):
            current_message = f"{reminder.get_as_text(index)}\n"
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

    async def add_interval(self, message, reminder: Reminder, interval: int, time_measure: str, announce=True):
        """
        Adds an interval to a given reminder
        :param message: message
        :param reminder: Reminder
        :param interval: int, Time amount
        :param time_measure: str
        :param announce: bool, If true will send a message to announce adding interval
        :return: nothing
        """
        user_id = str(message.author.id)
        if reminder is None:
            return
        reminder_timestamp = reminder.get_reminder_timestamp()
        interval_timestamp = get_date_with_delta(interval, time_measure,
                                                 now=datetime.fromtimestamp(reminder_timestamp))
        if interval_timestamp is None:
            return await message.channel.send(REMINDER_HELP)
        # Check that interval is not too short
        if interval_timestamp - reminder_timestamp < MINIMUM_INTERVAL_SECONDS:
            return await message.channel.send(f"That interval is too short (min {round(MINIMUM_INTERVAL_SECONDS / 60)}"
                                              f" minutes)")

        reminder.set_interval(interval, time_measure)
        self.write_reminders_to_disk(user_id)
        if announce:
            index = self.get_reminder_index(user_id, reminder)
            messages_to_send = reminder.get_as_text(index)
            title = "Interval added"
            content = f"<@{user_id}>"
            await HelperBotFunctions.send_embed_messages(messages_to_send, message.channel, title, content)

    async def remove_interval(self, message, reminder):
        if reminder is None:
            return
        user_id = str(message.author.id)

        if not reminder.has_interval():
            return await HelperBotFunctions.send_messages(["There's no interval set to given reminder"], message.channel)

        reminder.remove_interval()
        self.write_reminders_to_disk(user_id)
        index = self.get_reminder_index(user_id, reminder)
        messages_to_send = reminder.get_as_text(index)
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
        if user_id not in self.__list_of_reminders:
            self.__list_of_reminders[user_id] = {}
        # Check that user doesn't have too many reminder already
        elif len(self.__list_of_reminders.get(user_id)) > MAXIMUM_REMINDERS:
            return await message.channel.send("There are already too many reminders")

        server_id = message.guild.id
        channel_id = message.channel.id
        message_id = message.id
        now = datetime.now().timestamp()
        reminder_json = {"reminder_timestamp": str(timestamp),
                                                                "now_timestamp": str(now),
                                                                "user_id": str(user_id),
                                                                "message_id": str(message_id),
                                                                "channel_id": str(channel_id),
                                                                "server_id": str(server_id),
                                                                "raw_message": str(message.content),
                                                                "message_commands": str(message_command),
                                                                "message_text": str(message_text)}
        reminder = Reminder()
        reminder.load_from_json(reminder_json)
        self.add_reminder(user_id, reminder)

        if announce:
            index = self.get_reminder_index(user_id, reminder)
            messages_to_send = [reminder.get_as_text(index)]
            title = "Reminder added"
            content = f"<@{user_id}>"
            await HelperBotFunctions.send_embed_messages(messages_to_send, message.channel, title, content)
        return reminder
    
    def add_reminder(self, user_id: str, reminder: Reminder):
        user_reminders = self.__list_of_reminders.get(str(user_id))
        user_reminders.append(reminder)
        self.__list_of_reminders[str(user_id)] = sorted(user_reminders, key=lambda x: x.get_reminder_timestamp())
        self.write_reminders_to_disk(user_id)

    def remove_reminder(self, user_id: str, reminder: Reminder):
        index = self.get_reminder_index(user_id, reminder)
        self.__list_of_reminders.get(str(user_id)).pop(index)
        self.write_reminders_to_disk(user_id)

    def get_reminder_index(self, user_id: str, reminder: Reminder) -> int:
        return self.__list_of_reminders.get(user_id).index(reminder)

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
                to_be_handled = []
                user_reminders = self.__list_of_reminders.get(user_id)
                # If user has no reminders, go to next user
                if len(user_reminders) < 1:
                    continue
                for reminder in user_reminders:
                    if now >= reminder.get_reminder_timestamp():
                        to_be_handled.append(reminder)

                for reminder in to_be_handled:
                    server_id = reminder.get_server_id()
                    channel_id = reminder.get_channel_id()
                    user_to_mention = reminder.get_user_to_mention()
                    channel = self.__bot.get_guild(server_id).get_channel(channel_id)
                    index = self.get_reminder_index(user_id, reminder)
                    message_to_send = reminder.get_as_text(index)
                    failed_count = reminder.get_failed_count()
                    try:
                        await HelperBotFunctions.send_embed_messages([message_to_send], channel,
                                                                    "Reminder", user_to_mention)
                    except (discord.errors.Forbidden, discord.errors.HTTPException):
                        print(f"Failed to send reminder to channel {channel_id}")
                        # Send to message author instead
                        try:
                            user = await self.__bot.fetch_user(user_id)
                            await HelperBotFunctions.send_embed_messages([message_to_send], user,
                                                                    "Reminder", user_to_mention)
                        # Fail and try again the next time
                        except (discord.errors.Forbidden, discord.errors.HTTPException):
                            # Only skip deleting reminder if the maximum fail count is not reached (TODO)
                            if failed_count <= MAXIMUM_FAILED_COUNT:
                                continue
                            reminder.increase_failed_count()

                    # Remove reminder
                    self.remove_reminder(user_id, reminder)
                    # If reminder has interval make a new one after the interval
                    if reminder.has_interval():
                        interval_amount = reminder.get_interval_amount()
                        interval_measure = reminder.get_interval_measure()
                        time_to_remind_timestamp = reminder.get_reminder_timestamp()
                        new_timestamp = get_date_with_delta(interval_amount, interval_measure,
                                                            datetime.fromtimestamp(time_to_remind_timestamp))
                        if new_timestamp is not None:
                            reminder.set_reminder_time(new_timestamp)
                            self.add_reminder(user_id, reminder)

            # Sleep for 10 seconds after checking each user
            await asyncio.sleep(10)
