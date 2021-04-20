from HelperBotConstants import *


def make_dirs():
    if not os.path.exists(PATH_TO_REMINDERS):
        os.makedirs(PATH_TO_REMINDERS)


def craft_correct_length_messages(list_of_message_pieces):
    """
    Crafts a list with messages that don't exceed EMBED_MESSAGE_MAX_CHARACTERS
    :param list_of_message_pieces: list
    :return: list
    """
    current_message = ""
    list_of_new_pieces = []
    for piece in list_of_message_pieces:
        # Make this one message alone doesn't exceed max character length
        if len(piece) > EMBED_MESSAGE_MAX_CHARACTERS:
            piece = piece[:EMBED_MESSAGE_MAX_CHARACTERS]
        # If current and previous messages exceed max length, add crafted message to list
        if (len(piece) + len(current_message)) >= EMBED_MESSAGE_MAX_CHARACTERS:
            list_of_new_pieces.append(current_message)
            # Clear current_message
            current_message = ""
        # Add this message to current_message
        current_message += piece
    list_of_new_pieces.append(current_message)
    return list_of_new_pieces
