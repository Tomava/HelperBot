import discord
import datetime
import asyncio
import re
from dateutil.relativedelta import relativedelta
from HelperBotConstants import AUTO_CLEAN_PREFIX

class AutoCleaner:
    def __init__(self, bot):
        self.__bot = bot
        self.__started = False

    def get_started(self):
        return self.__started

    async def start(self):
        if self.__started:
            return
        self.__started = True
        re_pattern = rf"{AUTO_CLEAN_PREFIX}(\d+)"
        while True:
            for guild in self.__bot.guilds:
                for channel in guild.text_channels:
                    try:
                        description = channel.topic
                        if description is None:
                            continue
                        re_match = re.search(re_pattern, str(description))
                        if re_match is None:
                            continue
                        time_in_hours = int(re_match.group(1))
                        oldest_allowed = datetime.datetime.now() - relativedelta(hours=time_in_hours)
                        messages_before = channel.history(before=oldest_allowed, limit=None)
                        async for message in messages_before:
                            if message.pinned:
                                continue
                            print(f"Deleting: {message.id}")
                            await message.delete()
                    except (discord.errors.Forbidden, discord.errors.HTTPException):
                        continue
            await asyncio.sleep(3600)
