# Terminal basics

The **terminal** (also called the command line, shell or console) is a window where you type commands instead of clicking. You'll use it to run your programs and the project self-checks.

## Opening a terminal

- **Windows:** press the Windows key, type **Terminal** (or **PowerShell**), and press Enter.
- **macOS:** press Cmd+Space, type **Terminal**, and press Enter.
- **Linux:** usually Ctrl+Alt+T.
- **In VS Code** (any system): *Terminal → New Terminal*. It opens in the folder you have open, which saves a lot of moving around. See [Setting up VS Code](vs-code.md).

## Where am I?

A terminal is always "in" a folder, called the **current directory**. Commands like `python adventure.py` look for files there.

| What you want | Windows (PowerShell) | macOS / Linux |
| --- | --- | --- |
| Show the current folder | `pwd` | `pwd` |
| List files here | `dir` (or `ls`) | `ls` |
| Go into a folder | `cd my-adventure` | `cd my-adventure` |
| Go up one folder | `cd ..` | `cd ..` |
| Make a new folder | `mkdir my-adventure` | `mkdir my-adventure` |

Folder names with spaces need quotes: `cd "My Projects"`.

**Shortcut:** type `cd ` (with a space), then drag a folder from your file explorer into the terminal window. Its full path appears, so you only need to press Enter.

## Running a Python program

Go to the folder with your file, then run:

```sh
python adventure.py
```

(Use `python3` on macOS and Linux. See [Installing Python](installing-python.md).)

## Handy keys

- **Up arrow:** bring back the last command, so you don't have to retype it.
- **Tab:** auto-complete a file or folder name. Type the first few letters and press Tab.
- **Ctrl+C:** stop a running program, for example one stuck in a loop.

## Common problems

- **`No such file or directory`** or **`can't open file`**: you're in the wrong folder. Run `pwd` to see where you are and `ls` (or `dir`) to see what's there, then `cd` to the right place.
- **Nothing happens and there's no prompt**: your program is running and waiting, perhaps for input. Type something, or press Ctrl+C to stop it.
