'''
Module to run the shell.
'''
import signal
import re
import sys
import json
import os
from parsing import (
    split_by_pipe_op, splitting_arguments
)
from built_in_commands import (
    cd, pwd, which, 
    valid_var_name, exit
)
from executing_commands import (
    executing_commands_with_escape_variable, 
    executing_commands_with_no_escape_variables,
    executing_piped_commands, var
)

def myshrc() -> None:
    """
    Parsing the .myshrc file.
    """
    path = os.getenv("MYSHDOTDIR", os.path.expanduser("~")) + "/.myshrc"
    if not os.path.exists(path):
        return
    try:
        with open(path, 'r') as f:
            config = json.load(f)
            for key, value in config.items():
                # Validating variable names and types from .myshrc
                if not valid_var_name(key):
                    sys.stderr.write(f"mysh: .myshrc: {key}: invalid characters for variable name\n")
                    continue
                elif not isinstance(value, str):
                    sys.stderr.write(f"mysh: .myshrc: {key}: not a string\n")
                    continue
                os.environ[key] = os.path.expanduser(value)
    except json.JSONDecodeError:
        sys.stderr.write("mysh: invalid JSON format for .myshrc\n")

def setup_signals() -> None:
    """
    Setup signals required by this program.
    """
    signal.signal(signal.SIGTTOU, signal.SIG_IGN)

def missing_commands(parsed_line: list) -> bool:
    """
    Testing for missing commands in piping.
    """
    num_commands = len(parsed_line)
    for i in range(num_commands):
        if parsed_line[i].strip() == "":
            sys.stderr.write('mysh: syntax error: expected command after pipe\n')
            return False
    return True

def main() -> None:
    '''
    Main loop for the shell.
    '''
    setup_signals()
    myshrc() 

    # Setting default environment variables if not already set
    os.environ.setdefault("PROMPT", ">> ")
    os.environ.setdefault("MYSH_VERSION", "1.0")
    prompt = os.environ['PROMPT']

    while True:
        try:
            command = input(prompt) # Reading the user input

            if '|' in command:
                # Handling piped commands
                parsed_line = split_by_pipe_op(command)
                if not missing_commands(parsed_line):
                    continue
                executing_piped_commands(parsed_line)
            else:
                # Handling single commands
                parsed_line = splitting_arguments(command)
                if len(parsed_line) != 0:
                    cmd = parsed_line[0].lower()
                    if cmd == 'exit':
                        exit(parsed_line)
                    elif cmd == 'cd':
                        cd(parsed_line)
                    elif cmd == 'pwd':
                        pwd(parsed_line)
                    elif cmd == 'which':
                        if len(parsed_line) != 1:
                            commands = parsed_line[1:]
                            which(commands)
                        else:
                            sys.stderr.write('usage: which command ...\n')
                    elif cmd == 'var':
                        var(parsed_line)
                    elif len(parsed_line) == 2:
                        if re.search(r'\\\$', command):
                            executing_commands_with_escape_variable(parsed_line)
                        else:
                            executing_commands_with_no_escape_variables(parsed_line)
                    else:
                        executing_commands_with_no_escape_variables(parsed_line)
        except EOFError:
            print('')  # Handling end-of-file (EOF) for input
            break

if __name__ == "__main__":
    main()
