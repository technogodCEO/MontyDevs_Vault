# Module 00: Setup

**Goal:** Python and a virtual environment ready, a bot created in Discord's Developer Portal and invited to your own test server, and a `bot.py` that logs in.

This takes 30–45 minutes the first time. If you've already done another Python project in the vault, skip steps 1–3 (but check your Python version).

## 1. Install Python

Follow [Installing Python](../../../../../guides/installing-python.md), then check it worked:

```sh
python --version
```

You need **3.9 or newer**. (On macOS and Linux, type `python3` until you've activated the virtual environment in step 5. After that, `python` works everywhere.)

New to the terminal? Read [Terminal basics](../../../../../guides/terminal-basics.md) first.

## 2. Install a code editor

Follow [Setting up VS Code](../../../../../guides/vs-code.md), including the Python extension.

## 3. Get the vault

You need a copy of the vault on your computer for this project's `check.py` and practice files:

- **With Git (recommended):** in the folder where you keep projects, run
  ```sh
  git clone https://github.com/technogodCEO/MontyDevs_Vault.git
  ```
  See [Git and GitHub basics](../../../../../guides/git-and-github.md) if you haven't installed Git.
- **Without Git:** on the vault's GitHub page, click **Code → Download ZIP**, and unzip it.

## 4. Make your bot's folder

Make a folder for **your** bot, **outside** the vault, for example `my-bot` next to `MontyDevs_Vault`. Copy `check.py` from `MontyDevs_Vault/projects/bots-and-automation/01-discord-bot/` into it:

```sh
# from the folder that holds MontyDevs_Vault:
mkdir my-bot

# Windows (PowerShell)
Copy-Item MontyDevs_Vault\projects\bots-and-automation\01-discord-bot\check.py my-bot\

# macOS / Linux
cp MontyDevs_Vault/projects/bots-and-automation/01-discord-bot/check.py my-bot/
```

Then open `my-bot` in VS Code (*File → Open Folder...*). By the end of this module it will look like this:

```
Code/
├── MontyDevs_Vault/      # the tutorials (don't put your code in here)
└── my-bot/               # your bot
    ├── venv/             # its private Python (made in step 5)
    ├── .env              # your bot's secret token (step 8)
    ├── .gitignore        # keeps secrets out of Git (step 8)
    ├── bot.py            # your bot (step 9)
    └── check.py          # the self-check
```

## 5. Make a virtual environment and install discord.py

This project installs libraries, so it gets its own **virtual environment**. Read [Virtual environments](../../../../../guides/virtual-environments.md) if you haven't used one before. In VS Code's terminal (*Terminal → New Terminal*), inside `my-bot`:

```sh
python -m venv venv                 # macOS / Linux: python3 -m venv venv
```

Activate it:

```sh
venv\Scripts\Activate.ps1           # Windows (PowerShell)
source venv/bin/activate            # macOS / Linux
```

Your prompt should now start with `(venv)`. Install the libraries:

```sh
pip install discord.py python-dotenv
```

[discord.py](https://discordpy.readthedocs.io/) talks to Discord for you. [python-dotenv](https://pypi.org/project/python-dotenv/) reads secrets from a `.env` file, so they never have to be written in your code.

Finally, tell VS Code to use the venv: **Ctrl+Shift+P** → **Python: Select Interpreter** → pick the one that mentions `venv`.

> **Every time** you come back to this project, activate the venv in your terminal before running anything. If `python check.py` says discord.py isn't installed, that's almost always why.

## 6. Make a test server

Your bot needs somewhere to live. Make a private server just for testing, so you can experiment without bothering anyone:

1. In Discord, click the **+** at the bottom of your server list.
2. Choose **Create My Own** → **For me and my friends**, and give it a name like "Bot Lab".

Then turn on **Developer Mode**, which lets you copy the ID of anything in Discord: open **User Settings** (the cog next to your name) → **Advanced** → switch on **Developer Mode**.

Now right-click your new server's icon and choose **Copy Server ID**. Paste it somewhere for step 8.

## 7. Create your bot in the Developer Portal

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications) and log in.
2. Click **New Application**, give it your bot's name, accept the terms and click **Create**. You can add an avatar and a description on this page too.
3. In the menu on the left, open **Bot**. Click **Reset Token**, confirm, and **copy the token**. You'll paste it into a file in the next step.

   > **Your token is a password for your bot.** Anyone who has it can control your bot. Never paste it into a chat, a screenshot, or your code. If it ever leaks, come back here and click **Reset Token**: the old one stops working immediately.

4. Still in the menu, open **OAuth2**, then scroll to the **OAuth2 URL Generator**. Tick these scopes:
   - `bot`
   - `applications.commands`

   A **Bot Permissions** list appears. Tick **View Channels**, **Send Messages**, **Embed Links** and **Read Message History**.
5. Copy the **Generated URL** at the bottom, open it in your browser, choose your test server, and click **Authorize**.

Your bot now appears in your server's member list, offline. Next you'll bring it online.

## 8. Keep the token secret: `.env` and `.gitignore`

In VS Code, create a file in `my-bot` called exactly `.env` (with the dot, and nothing after it). Put your token and server ID in it:

```
DISCORD_TOKEN=paste-your-token-here
GUILD_ID=paste-your-server-id-here
```

No quotes and no spaces around the `=`.

Then create a file called `.gitignore`, which lists files Git should never save or upload:

```
.env
venv/
__pycache__/
*.db
```

Even if you never use Git, make it now: the self-check makes sure `.env` is in it, so your token can't end up on GitHub by accident later.

## 9. Create `bot.py`

Create `bot.py` and type this in:

```python
# bot.py: my Discord bot.
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

# Read DISCORD_TOKEN (and GUILD_ID) from the .env file into the environment.
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Intents say which events the bot wants Discord to send it.
# The defaults are enough for everything in this project.
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    # Runs once the bot has connected to Discord.
    print(f"Logged in as {bot.user}")


# Start the bot only when this file is run directly, so check.py can load
# your code without the bot logging in.
if __name__ == "__main__":
    bot.run(TOKEN)
```

You'll learn what `async`, `@bot.event` and the rest mean in Module 01. (`command_prefix` is for old-style `!commands`, which this project doesn't use, but `commands.Bot` needs one anyway.)

## 10. Run it

With the venv active:

```sh
python bot.py
```

After a few lines of log output you should see `Logged in as YourBot#1234`, and your bot shows as **online** in your server. It stays online until you stop the program with **Ctrl+C** in the terminal.

## 11. Run the self-check

Stop the bot with **Ctrl+C**, then:

```sh
python check.py 0
```

The checker never connects to Discord or reads your token: it only loads your code. `[PASS]` means you're ready for [Module 01](../01-hello-discord/).

## Optional: track your bot with Git

Run `git init` in `my-bot` and commit at the end of each module. Your `.gitignore` already keeps the token and the venv out. [Git and GitHub basics](../../../../../guides/git-and-github.md) walks you through it.

## Stuck?

- **`ModuleNotFoundError: No module named 'discord'`** (or `'dotenv'`): the venv isn't active in this terminal. Activate it (step 5) and try again. If it still happens, run `pip install discord.py python-dotenv` with the venv active.
- **PowerShell says "running scripts is disabled"** when you activate: see the troubleshooting section of [Virtual environments](../../../../../guides/virtual-environments.md).
- **`discord.errors.LoginFailure: Improper token has been passed`**: the token in `.env` is wrong or incomplete. Reset it in the Developer Portal, copy it again, and paste it after `DISCORD_TOKEN=` with no spaces or quotes.
- **`TypeError: expected token to be a str, received NoneType`**: `os.getenv("DISCORD_TOKEN")` found nothing. Check that the file is called exactly `.env` (not `.env.txt` or `env`), that it's in the same folder as `bot.py`, and that the line starts with `DISCORD_TOKEN=`.
- **A warning about the "message content intent"**: discord.py mentions this because `commands.Bot` can do `!commands`, which need it. This project only uses slash commands, so you can ignore it.
- **The bot is in the server but never comes online**: is `python bot.py` still running? The bot is only online while the program runs.
- **The check says `.gitignore` is missing `.env`**: make sure the file is named exactly `.gitignore`, and `.env` is on a line by itself.

## Resources

- [discord.py: Creating a Bot Account](https://discordpy.readthedocs.io/en/stable/discord.html): the same Developer Portal steps, with screenshots.
- [discord.py: Quickstart](https://discordpy.readthedocs.io/en/stable/quickstart.html): a minimal bot, like the one you just made.
