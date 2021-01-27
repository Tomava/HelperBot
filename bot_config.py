import os
from pathlib import Path

list_of_commands = {"!delete x": "This command deletes x amount of messages",
                    "!noclean": "I will automatically clean youtube links unless the message starts with this command",
                    "!count x": "I will count to x with about a second between messages. Use !count stop to stop counting",
                    "!remindme / !reminder \nx [Time Measure] \nOR\ndd.mm.yyyy hh.mm[.ss]\nOR\ntomorrow/today hh.mm[.ss]": "I will remind you in x amount of [Time Measures]",
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
list_of_tasks = ["I will tag you if you tag me",
                 "I will react like you do",
                 "I will automatically clean youtube links unless the message starts !noclean"
                 ]
list_of_time_measures = {"seconds": ["sec", "secs", "second", "seconds"],
                         "minutes": ["min", "mins", "minute", "minutes"],
                         "days": ["day", "days"],
                         "hours": ["hour", "hours"],
                         "weeks": ["week", "weeks"],
                         "months": ["month", "months"],
                         "years": ["year", "years"]
                         }
incorrect_reminder_format = ("Your message wasn't formatted correctly\n"
                             "Correct format is: !remindme x [Time Measure] where x is the amount of time measures\n"
                             "Or !remindme dd.mm.yyyy hh.mm[.ss]\n"
                             "Or !remindme tomorrow/today hh.mm[.ss]\n"
                             "Or !remindme list\n"
                             "Or !remindme delete x\n"
                             "To get a list of time measures, try !timemeasures")

embed_message_max_characters = 2048

# Path to home folder
home = str(Path.home())
path_to_discord = home + os.sep + "Discord"
path_to_reminders = home + os.sep + "Discord" + os.sep + "reminders"


def make_dirs():
    if not os.path.exists(path_to_reminders):
        os.makedirs(path_to_reminders)
