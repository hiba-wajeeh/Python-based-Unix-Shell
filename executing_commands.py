'''
Module to handle executing commands that are a part of the systems PATH.
'''
import signal
import re
import sys
import os
from parsing import split_by_pipe_op, splitting_arguments
from built_in_commands import (
    valid_var_name, expanding_variables,
    expanding_files, for_escaped_variables,
    chmod
)

def executing_command(cmd, arguments):
    '''
    Function for executing commands on PATH.
    '''
    try:
        pid = os.fork()
        if pid == 0:
            os.setpgid(0, 0)
            os.execvp(cmd, arguments)
            sys.stderr.write(f"{cmd}: command not found\n")
            os._exit(1)
        else:
            while True:
                try:
                    finished_pid = os.waitpid(pid, 0)
                    if finished_pid == pid:
                        break
                except ChildProcessError:
                    break
            if os.isatty(sys.stdin.fileno()):
                os.tcsetpgrp(sys.stdin.fileno(), os.getpgrp())
    except OSError as e:
        sys.stderr.write(f"OS error while executing command {cmd}: {e}\n")

def var(parsed_line):
    '''
    Implementing functionality for the var built-in command.
    '''

    invalid = re.compile(r'[^a-zA-Z0-9_]')
    if len(parsed_line)==3:
        variable_name = parsed_line[1]
        argument = parsed_line[2]
        if invalid.search(variable_name):
            sys.stdout.write(f'var: invalid characters for variable {variable_name}\n')
        else:
            if variable_name=='PROMPT':
                prompt = os.environ['PROMPT']
                command = input(prompt)
            os.environ[variable_name] = argument
    elif (len(parsed_line)>=4) and (parsed_line[1].find('-')== -1):
        sys.stdout.write(f'var: expected 2 arguments, got {len(parsed_line)-1}\n')
    elif (len(parsed_line)==4) and (parsed_line[1]!='-s'):
        element = parsed_line[1]
        element = element.strip('-')
        element = element[0]
        sys.stdout.write(f'var: invalid option: -{element}\n')
    elif (len(parsed_line)>=4) and (parsed_line[1].lower()=='-s'):
        variable_name = parsed_line[2]
        executing_command = ''.join(parsed_line[3:])

        if invalid.search(variable_name):
            if '{' in variable_name and '}' in variable_name:
                start = variable_name.find('{') + 1
                end = variable_name.find('}')
                extracted = variable_name[start:end]
                if not valid_var_name(extracted):
                    sys.stderr.write(
                        f'mysh: syntax error: invalid characters '
                        f'for variable {extracted}\n'
                    )
                    return
        else:
            parsed_input = splitting_arguments(executing_command)
            os.environ[variable_name] = executing_commands_for_var(parsed_input)
    return

def executing_commands_for_var(parsed_line):
    '''
    Executing commands for var -s using piping.
    '''
    command = parsed_line[0]
    args = [expanding_variables(arg) for arg in parsed_line]
    flag = False

    if command == 'cat' and len(args) > 1:
        args[1] = expanding_files(args[1])
        flag = True

    if '/' in command:
        if os.path.isfile(command) and os.access(command, os.X_OK):
            return run_piped_command(command, args, flag)
        else:
            if os.path.isfile(command):
                error_message = "permission denied"
            else:
                error_message = "no such file or directory"
            sys.stderr.write(f"mysh: {error_message}: {command}\n")
            return None
    else:
        path = os.getenv('PATH', os.defpath)
        for directory in path.split(os.pathsep):
            path_value = os.path.join(directory, command)
            if os.path.isfile(path_value) and os.access(path_value, os.X_OK):
                result = run_piped_command(path_value, args, flag)
                if flag:
                    return result
                return result.strip()

        sys.stderr.write(f"mysh: command not found: {command}\n")
        return None

def run_piped_command(cmd, arguments, flag):
    '''
    Running commands that are on PATH using piping.
    '''
    try:
        rfd, wfd = os.pipe()
        pid = os.fork()

        if pid == 0:
            os.setpgid(0, 0)
            os.close(rfd)
            os.dup2(wfd, 1)
            os.dup2(wfd, 2)
            os.close(wfd)
            os.execvp(cmd, arguments)
        else:
            os.close(wfd)
            output = os.read(rfd, 4096).decode()
            os.close(rfd)
            _, status = os.waitpid(pid, 0)
            os.tcsetpgrp(sys.stdin.fileno(), os.getpgrp())
            if flag:
                return output
            else:
                return output.strip()
    except Exception as e:
        sys.stderr.write(f"Error executing command: {cmd}\n")
        return None

def handle_interrupt(signum, frame):
    '''
    Helper function to handle the interrupt.
    '''
    interrupted = True
    os.killpg(0, signal.SIGTERM)
    sys.exit(1)

def executing_commands_with_escape_variable(parsed_line):
    '''
    Executes commands on PATH for variables that are escaped.
    '''
    command = parsed_line[0]
    args = [for_escaped_variables(arg) for arg in parsed_line]       
    if '/' in command:
        if os.path.isfile(command) and os.access(command, os.X_OK):
            executing_command(command, args)
        else:
            sys.stderr.write(f"mysh: {'permission denied' if os.path.isfile(command) else 'no such file or directory'}: {command}\n")
    else:
        path = os.getenv('PATH', os.defpath)
        for directory in path.split(os.pathsep):
            path_value = os.path.join(directory, command)
            if os.path.isfile(path_value) and os.access(path_value, os.X_OK):
                executing_command(path_value, args)
                return  
        sys.stderr.write(f"mysh: command not found: {command}\n") 

def executing_commands_with_no_escape_variables(parsed_line):
    '''
    Function for executing commands on PATH with no escape variable.
    '''
    interrupted = False  
    signal.signal(signal.SIGINT, handle_interrupt)  

    command = parsed_line[0]
    args = [expanding_variables(arg) for arg in parsed_line]

    if len(parsed_line) == 2:
        element = parsed_line[1]
        if '{' in element and '}' in element:
            start = element.find('{') + 1
            end = element.find('}')
            extracted = element[start:end]

            if not valid_var_name(extracted):
                sys.stderr.write(f'mysh: syntax error: invalid characters for variable {extracted}\n')
                return

    if command == 'cat' and len(args) > 1:
        args[1] = expanding_files(args[1])

    if command == 'chmod' and len(args) >= 3:
        mode = args[1]
        file_path = args[2]
        try:
            if mode.isdigit():
                os.chmod(file_path, int(mode, 8))
            elif mode.startswith(('+', '-')):
                chmod(file_path, mode)
            else:
                sys.stderr.write(f"mysh: chmod: invalid mode: {mode}\n")
        except FileNotFoundError:
            sys.stderr.write(
                f"mysh: chmod: cannot access '{file_path}': "
                "No such file or directory\n"
            )
        except PermissionError:
            sys.stderr.write(f"mysh: chmod: permission denied for '{file_path}'\n")
        return

    pid_list = []  

    if '/' in command:
        if os.path.isfile(command) and os.access(command, os.X_OK):
            pid = executing_command(command, [command] + args[1:])
            if pid is not None:
                pid_list.append(pid)
        else:
            sys.stderr.write(
                f"mysh: {'permission denied' if os.path.isfile(command) else 'no such file or directory'}: "
                f"{command}\n"
            )
            return
    else:
        path = os.getenv('PATH', os.defpath)
        for directory in path.split(os.pathsep):
            path_value = os.path.join(directory, command)
            if os.path.isfile(path_value) and os.access(path_value, os.X_OK):
                pid = executing_command(path_value, [command] + args[1:])
                if pid is not None:
                    pid_list.append(pid)
                break
        else:
            sys.stderr.write(f"mysh: command not found: {command}\n")
            return

    while pid_list:
        try:
            pid, status = os.wait()
            if pid in pid_list:
                pid_list.remove(pid)
                if os.WIFEXITED(status) or os.WIFSIGNALED(status):
                    continue
        except ChildProcessError:
            break
        except KeyboardInterrupt:
            sys.stderr.write("\nmysh: Process interrupted (Ctrl+C)\n")
            for pid in pid_list:
                try:
                    os.kill(pid, signal.SIGKILL)  
                except OSError:
                    pass
            pid_list.clear()

    if interrupted:
        sys.stderr.write("mysh: Interrupted by user\n")

def executing_piped_commands(commands):
    """
    Function that runs a series of commands connected by pipes.
    """
    signal.signal(signal.SIGINT, handle_interrupt)
    n = len(commands)
    pipes = []

    for _ in range(n - 1):
        pipes.append(os.pipe())

    for i in range(n):
        pid = os.fork()

        if pid == 0:  
            os.setpgid(0, 0)  
            
            if i > 0:
                os.dup2(pipes[i-1][0], 0) 
            
            if i < n - 1:
                os.dup2(pipes[i][1], 1) 

            cmd_args = splitting_arguments(commands[i])
            if cmd_args[0] == 'var':
                var(cmd_args)  
            else:
                try:
                    os.execvp(cmd_args[0], cmd_args)  
                except Exception as e:
                    sys.stderr.write(f'Command execution failed: {e}')
                    os._exit(1)  
        
        else:    
            if i > 0:
                os.close(pipes[i-1][0])  
            
            if i < n - 1:
                os.close(pipes[i][1])  

    for pipe in pipes:
        try:
            os.close(pipe[0])
        except OSError as e:
            if e.errno != 9:  
                raise

        try:
            os.close(pipe[1])
        except OSError as e:
            if e.errno != 9:  
                raise

    while True:
        try:
            os.wait()
        except ChildProcessError:
            break  
        except OSError as e:
            if e.errno == 10: 
                break
            else:
                raise
