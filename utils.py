# utils.py
from datetime import datetime
import globals
import builtins

def add_timestamp(msg):
    """
    Takes a message as input and returns the message with the current timestamp.
    
    Args:
        msg (str): The message to be timestamped.

    Returns:
        str: The message with a timestamp in the format [YYYY-MM-DD HH:MM:SS].
    """
    current_time = datetime.now()
    return f"[{current_time.strftime(globals.DATE_FORMAT)}] {msg}"

def print_with_timestamp(*args, **kwargs):
    """
    Custom print function that adds a timestamp to every printed message.

    Args:
        *args: Variable length argument list to capture all print arguments.
        **kwargs: Keyword arguments passed to the original print function.

    Returns:
        None
    """
    # Join all positional arguments into a single message string
    msg = " ".join(map(str, args))
    
    # Add timestamp to the message using the add_timestamp function
    timestamped_msg = add_timestamp(msg)
    
    # Use the original built-in print to print the timestamped message
    builtins.print(timestamped_msg, **kwargs)
