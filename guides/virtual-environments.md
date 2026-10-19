# Virtual environments

A **virtual environment** (or *venv*) is a private copy of Python for one project. Libraries you install with `pip` go into that project's venv, not into the Python shared by your whole computer.

## Why bother?

- **Projects don't fight.** One project can use version 1 of a library while another uses version 2.
- **You know what a project needs.** Everything installed in its venv is there because that project asked for it.
- **Mistakes are cheap.** If a venv gets into a mess, delete its folder and make a new one. Your code isn't touched.

Projects that only use Python's built-in modules, like the [Text Adventure](../projects/games/01-text-adventure/), don't need a venv. Any project that installs libraries with `pip` should have one.

## Make one

Open a terminal in your project's folder and run:

```sh
# Windows
python -m venv venv

# macOS / Linux
python3 -m venv venv
```

That creates a folder called `venv` inside your project. It holds the private Python and, later, every library you install. You don't need to look inside it, and it should never go into Git: add `venv/` to your project's `.gitignore`.

## Turn it on (activate)

You activate the venv **every time you open a new terminal** to work on the project:

| System | Command |
| --- | --- |
| Windows (PowerShell, VS Code's default) | `venv\Scripts\Activate.ps1` |
| Windows (Command Prompt) | `venv\Scripts\activate.bat` |
| macOS / Linux | `source venv/bin/activate` |

When it's active, your prompt starts with `(venv)`:

```
(venv) PS C:\Users\ana\Code\my-bot>
```

While it's active, `python` and `pip` mean the venv's copies, on every system. (On macOS and Linux, `python` works inside a venv even if you normally type `python3`.)

To check, run `python -c "import sys; print(sys.prefix)"`. It should print a path ending in your project's `venv` folder.

## Install libraries into it

With the venv active:

```sh
pip install discord.py
```

`pip list` shows everything installed in this venv.

## Turn it off

```sh
deactivate
```

Or just close the terminal.

## Let VS Code use it

VS Code can activate the venv for you in every new terminal, and use it to understand your imports:

1. Open your project folder in VS Code.
2. Press **Ctrl+Shift+P** (**Cmd+Shift+P** on a Mac) and choose **Python: Select Interpreter**.
3. Pick the one that mentions `venv` (something like `Python 3.12 ('venv')`).

New terminals in VS Code now start with `(venv)` already active. Terminals that were open before you picked it don't change: close them and open a new one.

## Troubleshooting

- **PowerShell says "running scripts is disabled on this system".** Windows blocks scripts like `Activate.ps1` by default. Allow scripts you've made yourself by running this once, then try activating again:
  ```powershell
  Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
  ```
  Or use Command Prompt instead, with `venv\Scripts\activate.bat`.
- **`ModuleNotFoundError` for a library you installed.** The venv isn't active in this terminal (no `(venv)` at the start of the prompt), or you installed the library before activating it. Activate it and run `pip install` again.
- **`No module named venv`** (Linux). Install it: `sudo apt install python3-venv` on Ubuntu or Debian.
- **You moved or renamed the project folder, and now the venv is broken.** Venvs remember where they were made. Delete the `venv` folder, make a new one, and reinstall what you need.

## Learn more

- [Python docs: Virtual environments and packages](https://docs.python.org/3/tutorial/venv.html): the official tutorial. Short, and covers `requirements.txt` files too.
