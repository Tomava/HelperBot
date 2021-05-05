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
LIST_OF_COMMANDS = {"!delete x": "This command deletes x amount of messages",
                    "!noclean": "I will automatically clean youtube links unless the message starts with this command",
                    "!count x": "I will count to x with about a second between messages. Use !count stop to stop counting",
                    "!remindme / !reminder \nx [Time Measure] \nOR\ndd.mm.yyyy_hh:mm[:ss]\nOR\ntomorrow/today_hh.mm[.ss]": "I will remind you in x amount of [Time Measures]",
                    "!remindme / !reminder list": "List your reminders",
                    "!remindme / !reminder delete / remove x": "Delete reminder at index x",
                    "!timemeasures": "Get a list of time measures",
                    "!answer": "I will try to answer your question",
                    "!roll": "Roll a roulette",
                    "!history": "Learn about my history",
                    "!game [game title]": "Notify others to play with you",
                    "!random x": "I will send x amount of random messages from channel history",
                    "!archive [true]": "Creates an archive of this server (requires Admin), if argument \"true\" is given downloads all attachment files"
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
REMINDER_HELP = ("Your message wasn't formatted correctly\n"
                 "Correct formats are: (using !remindme / !reminder)\n"
                 "!remindme in x [Time Measure]\n"
                 "!remindme time x [Time Measure]\n"
                 "!remindme on dd.mm.yyyy hh.mm[.ss]\n"
                 "!remindme at dd.mm.yyyy hh.mm[.ss]\n"
                 "!remindme date dd.mm.yyyy hh.mm[.ss]\n"
                 "!remindme tomorrow/today hh.mm[.ss]\n"
                 "!remindme list\n"
                 "!remindme remove/delete x\n"
                 "!remindme help\n\n"
                 "To get a list of time measures, try\n"
                 "!remindme timemeasures")

REMOVE_FROM_LINK = ["list", "index"]

# Path to home folder
HOME = str(Path.home())
PATH_TO_DISCORD = HOME + os.sep + "Discord"
PATH_TO_REMINDERS = HOME + os.sep + "Discord" + os.sep + "reminders"
