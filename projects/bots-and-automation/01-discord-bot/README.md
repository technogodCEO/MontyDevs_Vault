# Discord Bot

> Build your own Discord bot with slash commands, dice, XP levels and button polls, and give it a personality that's all yours.

**Difficulty:** Intermediate
**Language:** Python, with the [discord.py](https://discordpy.readthedocs.io/) library. discord.py is mature and well documented, and Python lets you focus on what the bot does rather than on boilerplate.
**Estimated time:** 10–15 hours across all modules, plus 30–45 minutes of setup

## What you'll build

A bot that lives in your Discord server and answers slash commands:

```
You:       /roll dice:2d6+3
Sprocket:  🎲 Rolling 2d6+3
           Rolls: 4, 6
           Total: 13

You:       /rank
Sprocket:  Ana is level 3 with 1,240 XP. *whirr*

You:       /poll question:Pizza or tacos? options:pizza, tacos
Sprocket:  Pizza or tacos?
           [ pizza ]  [ tacos ]      <- buttons anyone can click to vote
```

That's *Sprocket*, the example bot from the lessons. **Yours will be different.** You choose its name, its personality, how it talks, which extra commands it has, and how its levels work.

## What you'll learn

- `async` and `await`, events and decorators: how a bot waits for things to happen
- Working with a real library's API, and reading its documentation
- Structuring a bigger program: logic in plain Python modules, Discord code in cogs
- Parsing user input and handling errors gracefully
- Writing automated tests with pytest
- Storing data in a SQLite database
- Interactive messages with buttons

## Prerequisites

- You're comfortable with Python basics: functions, `if`, loops, lists and dictionaries. You've seen a `class` before, even if you don't write them often. (The [Text Adventure](../../games/01-text-adventure/) is a good warm-up, but you don't need to have done it.)
- A Discord account, and a computer you can install software on. [Module 00](modules/00-setup/) covers everything else, including making a private test server.

## Make it yours

Every module asks you to design something: what your bot says, which commands it has besides the required ones, how it rewards people, how its replies look. The lessons use Sprocket, a cheerful robot, as the example. A grumpy wizard, a cat that only sometimes helps, or a bot built around a game your friends play all work just as well.

The self-check never reads your bot's text. It loads your bot, finds your commands, and calls them with a pretend Discord to make sure they work. A few things need specific names so it can find them (like a `/roll` command, or a `dice.py` file), and each module says exactly which.

## How to work through this project

1. Start with [Module 00: Setup](modules/00-setup/). It gets Python and a virtual environment ready, creates your bot in Discord's Developer Portal, and gets a first `bot.py` online.
2. Work through the modules **in order**. Each one continues from the code you wrote in the last.
3. Each lesson starts with **Practice**: questions to think through, and a `practice_NN.py` file of small problems. Copy it into your bot's folder and test it with `python check.py practice 1` (using the module's number).
4. At the end of each module, check your work from your bot's folder, with your virtual environment active:
   ```sh
   python check.py 1      # use the module's number
   ```
5. Stuck? Each module's **Stuck?** section lists common mistakes, followed by hints you click to reveal, from a gentle nudge to nearly the whole answer. There are no full solutions for this project: the hints, the [discord.py docs](https://discordpy.readthedocs.io/) and your own debugging are how you get through.

## Modules

| # | Module | What you'll do |
| --- | --- | --- |
| 00 | [Setup](modules/00-setup/) | Install everything, create your bot in Discord, and get it online |
| 01 | [Hello, Discord](modules/01-hello-discord/) | Give your bot slash commands and a personality |
| 02 | [Options and Dice](modules/02-options-and-dice/) | Take options from the user, and roll dice like `2d6+3` |
| 03 | [Embeds and Errors](modules/03-embeds-and-errors/) | Make replies look good, and handle bad input gracefully |
| 04 | [Cogs and Tests](modules/04-cogs-and-tests/) | Split the bot into cogs, and write automated tests |
| 05 | [XP and a Database](modules/05-xp-and-a-database/) | Reward chatting with XP and levels, saved in SQLite |
| 06 | [Buttons and Polls](modules/06-buttons-and-polls/) | Make polls people vote on with buttons |

## Going further

Finished? Your bot is only online while `python bot.py` is running on your computer. Some ideas for what's next:

- **Host it.** Run it on an always-on machine: a Raspberry Pi at home, or a small cloud server. Read about [systemd services](https://wiki.archlinux.org/title/Systemd#Writing_unit_files) to keep it running and restart it when it crashes. Never put your token in the code you upload; use the host's environment variables.
- **Talk to the internet.** Use [aiohttp](https://docs.aiohttp.org/) (already installed with discord.py) to call a web API: jokes, weather, game stats, Wikipedia summaries.
- **Do things on a schedule.** [`discord.ext.tasks`](https://discordpy.readthedocs.io/en/stable/ext/tasks/index.html) runs a function every few minutes: reminders, daily questions, birthday messages.
- **More interactive messages.** Select menus, modals (pop-up forms) and persistent views that keep working after a restart. The [discord.py examples folder](https://github.com/Rapptz/discord.py/tree/master/examples) has one for each.
- **Grow the database.** Add tables for warnings, birthdays or an economy, and learn how to change a table's layout safely once it holds real data (a *migration*).
