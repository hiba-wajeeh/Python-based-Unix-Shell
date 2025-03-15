# Python-based-Unix-Shell
**Custom Unix Shell (Python)**   A Unix-like shell that runs system programs, parses commands from JSON config files, and supports process management. Built in Python to mimic core Unix shell features like PATH execution and command handling.

**How does your shell translate a line of input that a user enters into a command which is executed in the command line?**

In the mysh.py file, within the main function, it first sets the environment PROMPT variable. Then within a loop it'll 
keep asking the user to input a line (line 75 in mysh.py) which is then set as the prompt variable. It then checks if the
user has used piping in their line or not. If not, then the line is split into a list of arguments using the 
splitting_arguments function in parsing.py. If yes, it'll check if there's any missing commands. If there are no missing commands,
it will execute the piped commands accordingly. If no piping is used, once the line has been split, it will go through if statements 
to see what the command the user entered is. It will first check if the user has entered a built-in command and if not then 
it will check if the command is in the systems PATH (which is also set to default in the beginning of the main function) and
execute it accordingly. 

**What is the logic that your shell performs to find and substitute environment variables in user input?** 

When an environment variable is included in user input, it tries to find it by searching for "{" and "}" in the user input (line 186
in executing_commands.py). If found, it will then check if the variable name contained within the curly braces is a valid variable 
name or not. If not, it will exit. If it is a valid name, the argument gets expanded using the expanding_variables function (starting 
line 166 in built_in_commands.py). The way it expands it is that it uses a regular expression to find a pattern in the form of 
${VAR_NAME} and replaces them with the value stored at that environment variable from the environment dictionary. The function goes 
through the whole string to find all of the matches and returns the fully expanded string.

**How does it handle the user escaping shell variables with a backslash (\) so that they are interpreted as literal strings?**

In the main file, it will first check for the presence of a backslash (line 94 onwards in mysh.py), if it is present, it will
call the executing_commands_with_escape_variables function, which interprets it as a literal string and executes the command 
accordingly. In the function, it goes through the list of arguments (that are returned after splitting the user input) and 
replaces the '\${' and '${' (line 155 in built_in_commands.py). This makes the executing commands function interpret it as a literal
string rather than a variable.

**How does your shell handle pipelines as part of its execution?**

My shell first checks if the user input contains a pipe. If it does, it verifies if there is a missing command (line 75 in mysh.py). 
If a command is missing, it prints an error message and continues with the loop. If all commands are present, it runs the executing_piped_commands 
function (starting at line 264 in executing_commands.py). This function creates pipes and forks a new process for each command. In each child process 
(line 278), stdin and stdout are redirected based on the command's position in the pipeline using os.dup2(). The command is 
then executed with os.execvp(), except when var is part of the pipeline. In that case, the function handling the var command is called instead. This 
special handling is necessary because, when implementing the var -s functionality, the command execution section already pipes it to manage var -s 
correctly (run_piped_command function in executing_commands.py, lines 117-144). After execution, the parent process closes unused pipe ends and waits 
for all child processes to complete.

**What logic in your program allows one command to read another command's stdout output as stdin ?**

The logic I used relies on os.pipe() and using os.dup2() to redirect file descriptors. The stdin of each command (except for the first one) is set to
read the previous pipes stdout and the stdout of each command (except the last) is set to the writing end of the current pipe. This can be seen starting
line 264 in the executing_piped_commands function in executing_commands.py.
