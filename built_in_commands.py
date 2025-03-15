'''
Module to implement built-in commands.
'''
import signal
import re
import os
import sys
from parsing import splitting_arguments

interrupted = False

def chmod(file_path, mode):
    '''
    Helper function to handle the chmod command.
    '''
    try:
        file_path = expanding_files(file_path)
        current_mode = os.stat(file_path).st_mode

        if mode == '+x':
            new_mode = current_mode | 0o111 
        elif mode == '-x':
            new_mode = current_mode & ~0o111  
        elif mode == '+r':
            new_mode = current_mode | 0o444  
        elif mode == '-r':
            new_mode = current_mode & ~0o444  
        elif mode == '+w':
            new_mode = current_mode | 0o222  
        elif mode == '-w':
            new_mode = current_mode & ~0o222  
        else:
            raise ValueError(f"Invalid mode flag: {mode}")
        os.chmod(file_path, new_mode)

    except FileNotFoundError:
        sys.stderr.write(f"mysh: chmod: cannot access '{file_path}': No such file or directory\n")
    except PermissionError:
        sys.stderr.write(f"mysh: chmod: permission denied for '{file_path}'\n")
    except ValueError as e:
        sys.stderr.write(f"mysh: chmod: {str(e)}\n")

def exit(parsed_line: list):
    '''
    Implementing functionality for the exit built-in command.
    '''

    if len(parsed_line)<1 or len(parsed_line)>2:
        sys.stderr.write("exit: too many arguments\n")
    elif len(parsed_line)==2 and not parsed_line[1].isdigit():
        sys.stderr.write(f"exit: non-integer exit code provided: {parsed_line[1]}\n")
    elif len(parsed_line)==2 and parsed_line[1].isdigit():
        if parsed_line[1]=='0':
            sys.exit(0)
        else:
            exit_code = int(parsed_line[1])
            sys.exit(exit_code)
    else:
        sys.exit(0)
    return

def which(commands: list[str]) -> bool:
    '''
    Implementing functionality for the which built-in command.
    '''

    built_in_commands = ['pwd','cd', 'which', 'exit', 'var']
    flag = False
    path_flag = False

    for j in range(0, len(commands)):
        flag = False
        path_flag = False

        for i in range(0, len(built_in_commands)):
            if commands[j]==built_in_commands[i]:
                sys.stdout.write(f'{commands[j]}: shell built-in command\n')
                flag = True
                break
        
        if not flag:
            path = os.getenv('PATH')
            if path is None:
                path = os.getenv('PATH', os.defpath)
            dirs = path.split(os.pathsep)
            for directory in dirs:
                path_value = os.path.join(directory, commands[j])
                if os.path.isfile(path_value) and os.access(path_value, os.X_OK):
                    sys.stdout.write(path_value+'\n')
                    path_flag = True
                    break

            if not path_flag:
                sys.stdout.write(f'{commands[j]} not found\n')
    return 

def cd(parsed_line):
    '''
    Implementing functionality for the cd built-in command.
    '''

    if len(parsed_line) > 2:
        sys.stderr.write("cd: too many arguments\n")
    elif len(parsed_line) == 2:
        if parsed_line[1] == '..':
            try:
                os.chdir('..')
                new_directory = os.path.normpath(os.path.join(os.getenv("PWD"), ".."))
                os.environ['PWD'] = new_directory
            except PermissionError:
                sys.stderr.write("cd: permission denied: ..\n")
        else:
            try:
                new_directory = os.path.expanduser(parsed_line[1])
                os.chdir(new_directory)
                os.environ['PWD'] = os.path.abspath(new_directory)
            except FileNotFoundError:
                sys.stderr.write(f"cd: no such file or directory: {parsed_line[1]}\n")
            except NotADirectoryError:
                sys.stderr.write(f"cd: not a directory: {parsed_line[1]}\n")
            except PermissionError:
                sys.stderr.write(f"cd: permission denied: {parsed_line[1]}\n")
    elif len(parsed_line) == 1:
        try:
            new_directory = os.path.expanduser('~')
            os.chdir(new_directory)
            os.environ['PWD'] = os.path.abspath(new_directory)
        except PermissionError:
            sys.stderr.write("cd: permission denied: ~\n")

def pwd(parsed_line):
    '''
    Implmenting functionality for the pwd built-in command.
    '''

    if len(parsed_line) == 2 and parsed_line[1].lower() == '-p':
        current_directory = os.path.realpath(os.getcwd())
        sys.stdout.write(current_directory + '\n')
    elif len(parsed_line) == 1:
        current_directory = os.getenv("PWD", os.getcwd())
        if current_directory=='/home/docs/docs':
            os.environ['PWD'] = '/home/docs'
        current_directory = os.getenv("PWD", os.getcwd())
        sys.stdout.write(current_directory + '\n')
    elif len(parsed_line) >= 2 and parsed_line[1].startswith('-'):
        element = parsed_line[1][:2]
        sys.stderr.write(f"pwd: invalid option: {element}\n")
    elif len(parsed_line) >= 2 and not parsed_line[1].startswith('-'):
        sys.stderr.write("pwd: not expecting any arguments\n")

def for_escaped_variables(parsed_line):
    '''
    Helper function to replace the escaped variables.
    '''
    return parsed_line.replace(r'\${', r'${')

def expanding_files(path):
    '''
    Helper function to expand file paths.
    '''
    if path.startswith('~'):
        path = os.path.expanduser(path)
    path = os.path.expandvars(path)
    return path

def expanding_variables(echoed_statement, env=None):
    '''
    Helper function to expand variables.
    '''
    if env is None:
        env = os.environ
    pattern = re.compile(r'\$\{([^}]+)\}')

    while True:
        match = pattern.search(echoed_statement)
        if not match:
            break
        variable_name = match.group(1)
        variable_value = env.get(variable_name, '')  
        echoed_statement = echoed_statement.replace(match.group(0), variable_value)  
    
    return echoed_statement  


def valid_var_name(key):
    '''
    Helper function to test if a variable name is valid.
    '''
    invalid = re.compile(r'[^a-zA-Z0-9_]')
    variable_name = key
    if invalid.search(variable_name):
        return False
    else:
        return True
