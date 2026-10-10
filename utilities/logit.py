import datetime
import os
import inspect


# Define the log file path
LOG_FILE_PATH = 'static/app_log.txt'

# Ensure the log file exists or create it
if not os.path.exists(LOG_FILE_PATH):
    with open(LOG_FILE_PATH, 'w'):
        pass  # Create an empty log file if it doesn't exist

def _log_message(level, message):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    formatted_message = f"{timestamp} [{level.upper()}] - {message}\n"
    
    # Print to console
    print(formatted_message, end='')
    
    # Append the message to the log file
    with open(LOG_FILE_PATH, 'a') as log_file:
        log_file.write(formatted_message)

def debug(message):
    _log_message('debug', message)

def info(message):
    _log_message('info', message)

def warning(message):
    _log_message('warning', message)

def error(message):
    _log_message('error', message)

def logit(message):
    try:
        # Get the current timestamp
        timestr = datetime.datetime.now().strftime('%A_%b-%d-%Y_%H-%M-%S')

        # Get the caller's frame information
        caller_frame = inspect.stack()[1]
        filename = caller_frame.filename
        lineno = caller_frame.lineno
        function_name = caller_frame.function

        # Convert message to string if it's a list
        if isinstance(message, list):
            message_str = ' '.join(map(str, message))
        else:
            message_str = str(message)

        # Construct the log message with filename, line number, and function name
        log_message = (f"{timestr} - File: {filename}, Function: {function_name}, "
                       f"Line: {lineno} - Message: {message_str}\n")

        # Open the log file in append mode
        with open("static/app_log.txt", "a") as file:
            # Write the log message to the file
            file.write(log_message)

        # Print the log message to the console (optional)
        print(log_message)

    except Exception as e:
        # If an exception occurs during logit, print an error message
        error_message = f"Error occurred while logging: {e}\n"
        print(error_message)

        # Write the error message to the log file as well
        with open("static/app_log.txt", "a") as file:
            file.write(error_message)
