# ░▀█▀░█▄█░█▀█░█▀█░█▀▄░▀█▀░█▀▀
# ░░█░░█░█░█▀▀░█░█░█▀▄░░█░░▀▀█
# ░▀▀▀░▀░▀░▀░░░▀▀▀░▀░▀░░▀░░▀▀▀

from subprocess import Popen, PIPE
from pathlib import Path
import logging
import os
import sys
from enum import Enum


# ░█▀▀░█░░░█▀█░█▀▀░█▀▀░█▀▀░█▀▀
# ░█░░░█░░░█▀█░▀▀█░▀▀█░█▀▀░▀▀█
# ░▀▀▀░▀▀▀░▀░▀░▀▀▀░▀▀▀░▀▀▀░▀▀▀


class Color(Enum):
    """ Class for coloring print statements.  Nothing to see here, move along. """
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    PURPLE = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    END = '\033[0m'
    BOLD = '\033[1m'

    @staticmethod
    def string(string: str, color=None, bold: bool = False) -> str:
        """ Prints the given string in a few different colors.

        Args:
            string: string to be printed
            color:  valid colors Color.RED, "blue", Color.GREEN, "yellow"...
            bold:   T/F to add ANSI bold code

        Returns:
            ANSI color-coded string (str)
        """
        boldstr = Color.BOLD.value if bold else ""
        if not isinstance(color, Color):
            color = Color.WHITE

        return f'{boldstr}{color.value}{string}{Color.END.value}'

# ░█▀▀░█░█░█▀█░█▀▀░▀█▀░▀█▀░█▀█░█▀█░█▀▀
# ░█▀▀░█░█░█░█░█░░░░█░░░█░░█░█░█░█░▀▀█
# ░▀░░░▀▀▀░▀░▀░▀▀▀░░▀░░▀▀▀░▀▀▀░▀░▀░▀▀▀


def run_command(command: list, check=True, working_directory=os.getcwd(), capture_output=True, special_process_function=None, special_process_args=None) -> str:
    """Run synchronous command

    Args:
        command           (Array): all command arguments.
        check             (bool): defines if we check if the command can be executed or not.
        working_directory (str): if necessary, the working directory or the file path for the command.
        capture_output    (bool): prints the output as it comes on the console.
        special_process_function: if given, will execute a given function for each line of the output.
        special_process_args    : if given, will use this tuple as arguments for the special function.
    Returns:
        command_output (str): the complete output of the command.
    """

    command_output = ""
    command = [str(arg) for arg in command]

    # Check if the command first argument does exist
    if check and not check_command(command):
        logging.error(f"{command[0]} does not exist, please install it.")
        return

    logging.info(" ".join(command))

    # Check & create working directory if necessary
    if os.path.isfile(working_directory):
        working_directory = os.path.dirname(working_directory)
    check_dir(working_directory, verbose=capture_output)

    process = Popen(command, stdout=PIPE, stderr=PIPE, cwd=working_directory, shell=True)
    output = None

    # Start the process
    try:
        # Print the output as it becomes available
        while True:
            try:
                output = process.stdout.readline()
                if output == b'' and process.poll() is not None:
                    break

                if output:
                    line = output.decode('utf-8')
                    command_output += line

                    # If we want verbose
                    if capture_output:
                        sys.stdout.write(line)
                        sys.stdout.flush()

                    # If given, execute the special function on the outputed line
                    if special_process_function != None:
                        special_process_function(line, *special_process_args)
            except KeyboardInterrupt:
                logging.info("Keyboard Interruption")
                break

    except:
        logging.exception(f"The {command[0]} command failed to execute")

    return command_output


def check_dir(directory: str, verbose=False) -> None:
    """Check if a directory exists or not, then creates it if it doesn't

    Arguments:
        directory (str): is the path of the checked directory
    """
    path = Path(directory)

    if not os.path.isdir(directory):
        try:
            path.mkdir(parents=True)
            if verbose:
                logging.info(f"Successfully created {directory} directory")
        except:
            logging.error(f"Error creating {directory} directory")


def check_command(command: list) -> bool:
    """Check if a given command can be executed or not

    Args:
        command (list): the command arguments.
    """

    if os.path.isdir(command[0]):
        return True
    else:
        type_check = run_command([command[0]], check=False, capture_output=True)
        print(type_check)

        # If "not found" not in output, and output is not empty
        return "not found" not in type_check and len(type_check.strip()) != 0
