import os
from pathlib import Path

COMMAND_PREFIX = "!"

EMBED_MESSAGE_MAX_CHARACTERS = 2048
MAXIMUM_REMINDERS = 200
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
INCORRECT_REMINDER_FORMAT = ("Your message wasn't formatted correctly\n"
                             "Correct format is: !remindme x [Time Measure] where x is the amount of time measures\n"
                             "Or !remindme dd.mm.yyyy hh.mm[.ss]\n"
                             "Or !remindme tomorrow/today hh.mm[.ss]\n"
                             "Or !remindme list\n"
                             "Or !remindme delete x\n"
                             "To get a list of time measures, try !timemeasures")
REMOVE_FROM_LINK = ["list", "index"]

# Path to home folder
HOME = str(Path.home())
PATH_TO_DISCORD = HOME + os.sep + "Discord"
PATH_TO_REMINDERS = HOME + os.sep + "Discord" + os.sep + "reminders"
