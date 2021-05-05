import os
from pathlib import Path
from datetime import datetime

COMMAND_PREFIX = "!"

EMBED_MESSAGE_MAX_CHARACTERS = 2048
MESSAGE_MAX_CHARACTERS = 2000
MAXIMUM_REMINDERS = 200
MAXIMUM_REMOVED_MESSAGES = 5000
MAX_RANDOM_MESSAGES = 20
EPOCH_DATETIME = datetime(1970, 1, 1)
SECONDS_PER_DAY = 24 * 60 * 60
DATE_FORMAT = "%a %Y-%m-%d %H:%M:%S"
LIST_OF_COMMANDS = {f"{COMMAND_PREFIX}delete x": "This command deletes x amount of messages",
                    f"{COMMAND_PREFIX}noclean": "I will automatically clean youtube links unless the message starts with this command",
                    f"{COMMAND_PREFIX}count x": "I will count to x with about a second between messages. Use !count stop to stop counting",
                    f"{COMMAND_PREFIX}remindme / {COMMAND_PREFIX}reminder \nx [Time Measure] \nOR\ndd.mm.yyyy_hh:mm[:ss]\nOR\ntomorrow/today_hh.mm[.ss]": "I will remind you in x amount of [Time Measures]",
                    f"{COMMAND_PREFIX}remindme / {COMMAND_PREFIX}reminder list": "List your reminders",
                    f"{COMMAND_PREFIX}remindme / {COMMAND_PREFIX}reminder delete / remove x": "Delete reminder at index x",
                    f"{COMMAND_PREFIX}timemeasures": "Get a list of time measures",
                    f"{COMMAND_PREFIX}answer": "I will try to answer your question",
                    f"{COMMAND_PREFIX}roll": "Roll a roulette",
                    f"{COMMAND_PREFIX}history": "Learn about my history",
                    f"{COMMAND_PREFIX}game [game title]": "Notify others to play with you",
                    f"{COMMAND_PREFIX}random x": "I will send x amount of random messages from channel history",
                    f"{COMMAND_PREFIX}archive [true]": "Creates an archive of this server (requires Admin), if argument \"true\" is given downloads all attachment files"
                    }
LIST_OF_TASKS = ["I will tag you if you tag me",
                 "I will react like you do",
                 "I will automatically clean youtube links unless the message starts !noclean"
                 ]
LIST_OF_TIME_MEASURES = {"seconds": ["sec", "secs", "second", "seconds"],
                         "minutes": ["min", "mins", "minute", "minutes"],
                         "days": ["day", "days"],
                         "hours": ["hour", "hours"],
                         "weeks": ["week", "weeks"],
                         "months": ["month", "months"],
                         "years": ["year", "years"]
                         }
REMINDER_HELP = (f"Correct formats are: (using !remindme / !reminder)\n"
                 f"{COMMAND_PREFIX}remindme in x [Time Measure]\n"
                 f"{COMMAND_PREFIX}remindme time x [Time Measure]\n"
                 f"{COMMAND_PREFIX}remindme on dd.mm.yyyy hh.mm[.ss]\n"
                 f"{COMMAND_PREFIX}remindme at dd.mm.yyyy hh.mm[.ss]\n"
                 f"{COMMAND_PREFIX}remindme date dd.mm.yyyy hh.mm[.ss]\n"
                 f"{COMMAND_PREFIX}remindme tomorrow/today hh.mm[.ss]\n"
                 f"{COMMAND_PREFIX}remindme list\n"
                 f"{COMMAND_PREFIX}remindme remove/delete x\n"
                 f"{COMMAND_PREFIX}remindme help\n\n"
                 f"To get a list of time measures, try\n"
                 f"{COMMAND_PREFIX}remindme timemeasures")
ADMIN_HELP = (f"{COMMAND_PREFIX}archive [true]: Creates an archive of this server, if argument \"true\" is given downloads all attachment files\n"
              f"{COMMAND_PREFIX}admin help\n")
REMOVE_FROM_LINK = ["list", "index"]

# Path to home folder
HOME = str(Path.home())
PATH_TO_DISCORD = HOME + os.sep + "Discord"
PATH_TO_REMINDERS = HOME + os.sep + "Discord" + os.sep + "reminders"
