# Installing Python

The projects in this vault use **Python 3**, version 3.9 or newer. Follow the section for your computer, then [check that it worked](#check-that-it-worked).

## Windows

1. Go to [python.org/downloads](https://www.python.org/downloads/) and click the big **Download Python** button.
2. Run the installer. On the first screen, **tick "Add python.exe to PATH"** at the bottom. This step is easy to miss, and without it your terminal won't find Python.
3. Click **Install Now** and wait for it to finish.
4. Close any terminals you already had open, and open a new one so it picks up the change.

On Windows you can type either `python` or `py` to run Python.

> **Typing `python` opens the Microsoft Store?** Windows has a shortcut that does this when Python isn't found. Either install Python as above, or go to *Settings → Apps → Advanced app settings → App execution aliases* and turn off the two "python" aliases.

## macOS

1. Go to [python.org/downloads](https://www.python.org/downloads/) and download the macOS installer.
2. Open the downloaded `.pkg` file and follow the steps.

If you use [Homebrew](https://brew.sh/), `brew install python` works too.

**On macOS, type `python3` instead of `python`** everywhere the tutorials say `python`.

## Linux

Most Linux systems already have Python 3. If yours doesn't, install it with your package manager. On Ubuntu or Debian:

```sh
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

**On Linux, type `python3` instead of `python`** everywhere the tutorials say `python`.

## Check that it worked

Open a terminal (see [Terminal basics](terminal-basics.md)) and run:

```sh
python --version
```

(Or `python3 --version` on macOS and Linux, or `py --version` on Windows.)

You should see something like `Python 3.12.4`. If the number starts with 3 and is 3.9 or higher, you're ready.

## Troubleshooting

- **`command not found` or `'python' is not recognized`**: Python isn't installed, or isn't on your PATH. On Windows, run the installer again, choose **Modify**, and make sure "Add Python to environment variables" is ticked. Then open a new terminal.
- **It says `Python 2.7`**: you have an old Python. Use `python3` instead.
- **Still stuck?** Ask in the club chat, and include the exact command you typed and the message you got.
