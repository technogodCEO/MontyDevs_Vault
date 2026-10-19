"""
Self-check for the Discord Bot project.

Run it from your bot's folder, with your virtual environment active, and give
it the module number you just finished:

    python check.py 3

(Use 0 right after setup, in Module 00.)

It checks that module and every module before it, so you know nothing broke.

It also tests the practice problems in each lesson:

    python check.py practice 2               # tests practice_02.py
    python check.py practice 2 my_file.py

The checker never connects to Discord, and never needs your token. It loads
your bot.py (and your cogs), finds your slash commands, and calls them with a
pretend interaction to see what they reply. Your bot's name, personality and
extra commands can be anything you like.
"""

import ast
import asyncio
import contextlib
import importlib
import importlib.util
import inspect
import io
import json
import os
import random
import re
import sqlite3
import subprocess
import sys
import tempfile
import traceback

# How long one practice problem may run, in seconds, before we assume it's stuck.
TIMEOUT = 5
# How long a single slash command may take.
COMMAND_TIMEOUT = 5
# How long the whole module check may take (it may run your tests too).
RUN_TIMEOUT = 60

FOLDER = os.getcwd()


class CheckFailed(Exception):
    """Raised when one of the checks finds a problem."""


def fail(message):
    raise CheckFailed(message)


def say(message):
    """Print a line that may contain the bot's own text (emoji and all)."""
    print(message, flush=True)


# ---------------------------------------------------------------------------
# A pretend Discord
# ---------------------------------------------------------------------------
# Slash commands receive an `Interaction` from Discord. We can't talk to
# Discord here, so we hand your commands a stand-in that has the parts most
# bots use, and records everything they send.

# Names of attributes your code asked for that the stand-in doesn't have.
MISSING = []


class NotFaked(AttributeError):
    """Raised when bot code uses a part of Discord that check.py doesn't pretend to have."""


class Fake:
    """Base class: asking for anything we didn't set up is reported clearly."""

    _what = "object"

    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        MISSING.append(f"{self._what}.{name}")
        raise NotFaked(f"check.py's pretend {self._what} has no '{name}'")


def message_text(content=None, embeds=()):
    """All the readable text in a message: its content and every embed."""
    parts = [str(content)] if content is not None else []
    for embed in embeds:
        if embed is None:
            continue
        data = embed.to_dict() if hasattr(embed, "to_dict") else {}
        parts += [str(data.get(key, "")) for key in ("title", "description")]
        for field in data.get("fields", []):
            parts += [str(field.get("name", "")), str(field.get("value", ""))]
        parts.append(str(data.get("footer", {}).get("text", "")))
        parts.append(str(data.get("author", {}).get("name", "")))
    return "\n".join(part for part in parts if part)


class Sent:
    """One message the bot sent."""

    def __init__(self, how, content=None, embed=None, embeds=None, view=None, ephemeral=False):
        self.how = how
        self.content = content
        self.embeds = ([embed] if embed is not None else []) + list(embeds or [])
        self.view = view
        self.ephemeral = ephemeral
        self.text = message_text(content, self.embeds)


class Asset(Fake):
    _what = "avatar"

    def __init__(self, user_id):
        self.url = f"https://cdn.discordapp.com/embed/avatars/{user_id % 5}.png"

    def __str__(self):
        return self.url


class FakeUser(Fake):
    _what = "interaction.user"

    def __init__(self, user_id, name="tester", bot=False):
        import datetime
        self.id = user_id
        self.name = name
        self.global_name = name.title()
        self.display_name = name.title()
        self.nick = None
        self.mention = f"<@{user_id}>"
        self.bot = bot
        self.avatar = None
        self.display_avatar = Asset(user_id)
        self.roles = []
        self.created_at = datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc)
        self.joined_at = self.created_at

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return getattr(other, "id", None) == self.id

    def __hash__(self):
        return hash(self.id)


class FakeChannel(Fake):
    _what = "interaction.channel"

    def __init__(self, record):
        self.id = 333
        self.name = "general"
        self.mention = "<#333>"
        self._record = record

    async def send(self, content=None, *, embed=None, embeds=None, view=None, **extra):
        self._record.append(Sent("channel.send", content, embed, embeds, view))


class FakeGuild(Fake):
    _what = "interaction.guild"

    def __init__(self, members):
        self.id = 111
        self.name = "Test Server"
        self.member_count = len(members)
        self.icon = None
        self._members = members

    def get_member(self, user_id):
        return self._members.get(user_id)


class FakeResponse(Fake):
    _what = "interaction.response"

    def __init__(self, interaction):
        self._interaction = interaction
        self._done = False

    def _respond(self):
        import discord
        if self._done:
            # Real Discord only allows one response per interaction.
            raise discord.InteractionResponded(self._interaction)
        self._done = True

    def is_done(self):
        return self._done

    async def send_message(self, content=None, *, embed=None, embeds=None, view=None,
                           ephemeral=False, **extra):
        self._respond()
        self._interaction.sent.append(Sent("send_message", content, embed, embeds, view, ephemeral))

    async def defer(self, *, ephemeral=False, thinking=False, **extra):
        self._respond()
        self._interaction.deferred_ephemeral = ephemeral

    async def edit_message(self, *, content=None, embed=None, embeds=None, view=None, **extra):
        self._respond()
        self._interaction.sent.append(Sent("edit_message", content, embed, embeds, view))


class FakeFollowup(Fake):
    _what = "interaction.followup"

    def __init__(self, interaction):
        self._interaction = interaction

    async def send(self, content=None, *, embed=None, embeds=None, view=None,
                   ephemeral=False, **extra):
        if not self._interaction.response.is_done():
            raise RuntimeError("followup.send() was used before responding. "
                               "Call interaction.response.defer() first.")
        ephemeral = ephemeral or self._interaction.deferred_ephemeral
        self._interaction.sent.append(Sent("followup.send", content, embed, embeds, view, ephemeral))


class FakeInteraction(Fake):
    _what = "interaction"

    def __init__(self, bot, user=None):
        import datetime
        self.sent = []
        self.deferred_ephemeral = False
        self.user = user or FakeUser(42)
        self.client = bot
        self.guild = FakeGuild({self.user.id: self.user})
        self.guild_id = self.guild.id
        self.channel = FakeChannel(self.sent)
        self.channel_id = self.channel.id
        self.message = None
        self.locale = "en-US"
        self.created_at = datetime.datetime.now(datetime.timezone.utc)
        self.response = FakeResponse(self)
        self.followup = FakeFollowup(self)

    async def edit_original_response(self, *, content=None, embed=None, embeds=None, view=None, **extra):
        self.sent.append(Sent("edit_original_response", content, embed, embeds, view))

    async def original_response(self):
        return None

    async def delete_original_response(self):
        pass

    def replies(self):
        """Everything sent in reply (not counting plain channel messages)."""
        return [sent for sent in self.sent if sent.how != "channel.send"]

    def text(self):
        return "\n".join(sent.text for sent in self.sent)


class FakeMessage(Fake):
    _what = "message"

    def __init__(self, author, record):
        import datetime
        self.author = author
        self.content = "hello there"
        self.guild = FakeGuild({author.id: author})
        self.channel = FakeChannel(record)
        self.id = 444
        self.created_at = datetime.datetime.now(datetime.timezone.utc)
        self.mentions = []
        self.attachments = []
        self.embeds = []

    async def reply(self, content=None, **extra):
        self.channel._record.append(Sent("message.reply", content, extra.get("embed"), extra.get("embeds")))

    async def add_reaction(self, emoji):
        pass


# ---------------------------------------------------------------------------
# Loading the learner's bot
# ---------------------------------------------------------------------------
class StartedOnImport(Exception):
    """bot.py tried to log in to Discord while being loaded."""


class Harness:
    """Loads bot.py once, and calls its slash commands."""

    def __init__(self):
        self.bot = None
        self.module = None
        self.cogs_loaded = False

    def load_bot(self):
        if self.bot is not None:
            return self.bot
        path = os.path.join(FOLDER, "bot.py")
        if not os.path.isfile(path):
            fail(f"Couldn't find {path}.\nRun this from your bot's folder.")
        try:
            import discord
            from discord.ext import commands
        except ImportError:
            fail("discord.py isn't installed for this Python:\n"
                 f"  {sys.executable}\n"
                 "Activate your virtual environment, then run: pip install discord.py python-dotenv")

        # Never let the bot connect: if bot.py logs in while loading, stop it.
        def blocked(*args, **kwargs):
            raise StartedOnImport()
        discord.Client.run = blocked
        discord.Client.start = blocked
        discord.Client.login = blocked

        try:
            with contextlib.redirect_stdout(io.StringIO()):
                self.module = importlib.import_module("bot")
        except StartedOnImport:
            fail("bot.py tried to log in to Discord as soon as it was loaded.\n"
                 "Put bot.run(...) inside an  if __name__ == \"__main__\":  block at the bottom.")
        except Exception as error:
            fail("bot.py crashed while loading:\n\n" + short_traceback(error))

        bot = getattr(self.module, "bot", None)
        if not isinstance(bot, commands.Bot):
            fail("bot.py should create your bot in a variable called `bot`, made with "
                 "commands.Bot(...) (or a class based on it).")
        # Offline, the bot's latency is "not a number", which breaks round().
        # Pretend we have a 42 ms connection instead.
        type(bot).latency = property(lambda self: 0.042)
        self.bot = bot
        return bot

    async def load(self):
        """Load bot.py and, if there is a cogs folder, every cog in it."""
        bot = self.load_bot()
        if self.cogs_loaded:
            return bot
        self.cogs_loaded = True
        for name in cog_files():
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    await bot.load_extension(f"cogs.{name}")
            except Exception as error:
                problem = describe_extension_error(error, name)
                if problem:
                    fail(problem)
        return bot

    def commands(self):
        """Every slash command, by name (like 'roll', or 'group sub' for groups)."""
        from discord import app_commands
        tree = self.bot.tree
        found = {}
        guild_ids = list(getattr(tree, "_guild_commands", {}).keys())
        import discord
        for guild in [None] + [discord.Object(id=guild_id) for guild_id in guild_ids]:
            for command in tree.walk_commands(guild=guild):
                if isinstance(command, app_commands.Command):
                    found.setdefault(command.qualified_name, command)
        return found

    def command(self, name, why=""):
        command = self.commands().get(name)
        if command is None:
            fail(f"Couldn't find a /{name} slash command.{why}")
        return command

    async def sample_args(self, command, interaction, given):
        """Make up a value for every required option, unless the test gave one."""
        from discord import AppCommandOptionType as Type
        values = {}
        for name, param in command._params.items():
            if name in given:
                raw = given[name]
            elif not param.required:
                continue
            elif param.choices:
                raw = param.choices[0].value
            elif param.type in (Type.user, Type.mentionable):
                values[name] = interaction.user
                continue
            elif param.type == Type.channel:
                values[name] = interaction.channel
                continue
            elif param.type == Type.integer:
                raw = int(param.min_value if param.min_value is not None else 2)
            elif param.type == Type.number:
                raw = float(param.min_value if param.min_value is not None else 2.5)
            elif param.type == Type.boolean:
                raw = True
            elif param.type == Type.string:
                raw = "test"
            else:
                fail(f"/{command.qualified_name} has an option '{name}' of a type check.py "
                     "can't fill in. Make it optional, or use a string, number or user option.")
            try:
                values[name] = await param.transform(interaction, raw)
            except Exception:
                values[name] = raw
        return values

    async def run(self, name, user=None, **given):
        """Call /name with a pretend interaction. Returns the interaction."""
        command = self.command(name)
        interaction = FakeInteraction(self.bot, user)
        kwargs = await self.sample_args(command, interaction, given)
        shown = " ".join(f"{key}:{value!r}" for key, value in given.items())
        label = f"/{name} {shown}".strip()
        args = [command.binding] if command.binding is not None else []
        await call_bot_code(label, command.callback(*args, interaction, **kwargs))
        if not interaction.replies():
            fail(f"{label} didn't reply. Reply with  await interaction.response.send_message(...)")
        return interaction


async def call_bot_code(label, coroutine):
    """Await some of the learner's code, turning crashes into clear messages."""
    MISSING.clear()
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            await asyncio.wait_for(coroutine, COMMAND_TIMEOUT)
    except asyncio.TimeoutError:
        fail(f"{label} was still running after {COMMAND_TIMEOUT} seconds. "
             "(Discord gives up after 3.)")
    except CheckFailed:
        raise
    except Exception as error:
        hint = ""
        if MISSING:
            hint = (f"\n\n(It used {MISSING[-1]}, which check.py's pretend Discord doesn't "
                    "have. Most bots don't need it. If yours really does, guard it so the "
                    "command still replies without it.)")
        fail(f"{label} crashed:\n\n{short_traceback(error)}{hint}")


def short_traceback(error):
    """The parts of a traceback that are in the learner's own files."""
    frames = traceback.extract_tb(error.__traceback__)
    mine = [frame for frame in frames
            if os.path.abspath(frame.filename).startswith(FOLDER)
            and os.path.abspath(frame.filename) != os.path.abspath(__file__)]
    lines = traceback.format_list(mine[-4:] or frames[-2:])
    lines += traceback.format_exception_only(type(error), error)
    return "".join(lines).rstrip()


def cog_files():
    """Names of the cog files in cogs/, like ['fun', 'levels']."""
    folder = os.path.join(FOLDER, "cogs")
    if not os.path.isdir(folder):
        return []
    return sorted(name[:-3] for name in os.listdir(folder)
                  if name.endswith(".py") and not name.startswith("_"))


def describe_extension_error(error, name):
    """Explain why a cog wouldn't load, or None if it's fine to ignore."""
    from discord.ext import commands
    from discord import app_commands
    if isinstance(error, commands.ExtensionAlreadyLoaded):
        return None
    if isinstance(error, commands.NoEntryPointError):
        return (f"cogs/{name}.py has no setup function. Add one at the bottom:\n\n"
                "    async def setup(bot):\n        await bot.add_cog(YourCog(bot))")
    original = getattr(error, "original", error)
    if isinstance(original, app_commands.CommandAlreadyRegistered):
        return (f"Loading cogs/{name}.py added a command that already exists: {original}\n"
                "Did you leave a copy of it in bot.py, or in another cog?")
    return f"cogs/{name}.py crashed while loading:\n\n{short_traceback(original)}"


def load_learner_module(name, why):
    """Import one of the learner's own modules, like dice.py."""
    if not os.path.isfile(os.path.join(FOLDER, f"{name}.py")):
        fail(f"Couldn't find {name}.py in your bot's folder.{why}")
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            return importlib.import_module(name)
    except Exception as error:
        fail(f"{name}.py crashed while loading:\n\n{short_traceback(error)}")


def get_function(module, name):
    function = getattr(module, name, None)
    if not callable(function):
        fail(f"{module.__name__}.py should have a function or class called {name}.")
    return function


def numbers_in(text):
    return [int(number) for number in re.findall(r"-?\d+", text)]


def run_tests(minimum):
    """Run the learner's pytest tests. Returns how many passed."""
    if not os.path.isdir(os.path.join(FOLDER, "tests")):
        fail("Couldn't find a tests folder. Make one next to bot.py.")
    try:
        import pytest  # noqa: F401  (just checking it's installed)
    except ImportError:
        fail("pytest isn't installed. With your venv active, run: pip install pytest")
    try:
        result = subprocess.run(
            [sys.executable, "-B", "-m", "pytest", "-q", "-rf", "--tb=line", "-p", "no:cacheprovider", "tests"],
            cwd=FOLDER, capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=RUN_TIMEOUT // 2, stdin=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired:
        fail("Your tests were still running after a minute. Is a test stuck in a loop?")
    output = result.stdout + result.stderr
    passed = int((re.search(r"(\d+) passed", output) or [0, 0])[1])
    if result.returncode != 0:
        tail = "\n".join(output.strip().splitlines()[-15:])
        fail(f"Some of your tests fail (or couldn't run). Here's what pytest said:\n\n{tail}")
    if passed < minimum:
        fail(f"Found {passed} passing tests. Write at least {minimum}.")
    return passed


# ---------------------------------------------------------------------------
# The checks for each module
# ---------------------------------------------------------------------------
# A Discord token looks like three chunks of letters and digits joined by dots.
TOKEN_PATTERN = re.compile(r"[A-Za-z\d_-]{23,28}\.[A-Za-z\d_-]{6}\.[A-Za-z\d_-]{27,}")


async def check_00(h):
    if sys.version_info < (3, 9):
        fail(f"You're running Python {sys.version.split()[0]}. This project needs 3.9 or newer.")
    say(f"  - Python {sys.version.split()[0]}")

    for root, folders, files in os.walk(FOLDER):
        folders[:] = [f for f in folders if not f.startswith(".") and f not in ("venv", "__pycache__")]
        for name in files:
            if name.endswith(".py") and name != "check.py":
                path = os.path.join(root, name)
                with open(path, encoding="utf-8", errors="replace") as file:
                    if TOKEN_PATTERN.search(file.read()):
                        fail(f"{os.path.relpath(path, FOLDER)} seems to contain a bot token.\n"
                             "Tokens belong in .env only. If this file was ever shared or "
                             "pushed, reset the token in the Developer Portal.")
    say("  - no tokens written into your code")

    gitignore = os.path.join(FOLDER, ".gitignore")
    lines = []
    if os.path.isfile(gitignore):
        with open(gitignore, encoding="utf-8", errors="replace") as file:
            lines = [line.strip() for line in file]
    if ".env" not in lines:
        fail("Your .gitignore should have a line that says .env, so Git never uploads your token.")
    say("  - .gitignore keeps .env out of Git")

    h.load_bot()
    with open(os.path.join(FOLDER, "bot.py"), encoding="utf-8", errors="replace") as file:
        if "DISCORD_TOKEN" not in file.read():
            fail("bot.py should read the token from the DISCORD_TOKEN environment variable "
                 "(os.getenv(\"DISCORD_TOKEN\")).")
    say("  - bot.py loads without logging in, and reads DISCORD_TOKEN")
    if not os.path.isfile(os.path.join(FOLDER, ".env")):
        say("  - (no .env file yet: you'll need one to actually run the bot)")


# Options for commands that later modules ask for by name, so they get
# sensible values when check 01 tries every command.
SAMPLE_ARGS = {
    "roll": {"dice": "2d6"},
    "poll": {"question": "Best snack?", "options": "chips, fruit"},
}


async def check_01(h):
    await h.load()
    found = h.commands()
    if len(found) < 2:
        names = ", ".join("/" + name for name in found) or "none"
        fail(f"Your bot needs at least 2 slash commands. Found: {names}")
    for name, command in found.items():
        if not command.description or command.description == "…":
            fail(f"/{name} has no description. Add one: @bot.tree.command(description=\"...\")")
    say(f"  - {len(found)} slash commands, all with descriptions")
    for name in found:
        await h.run(name, **SAMPLE_ARGS.get(name, {}))
    say("  - every command replies")


async def check_02(h):
    dice = load_learner_module("dice", "")
    parse_dice = get_function(dice, "parse_dice")
    roll_dice = get_function(dice, "roll_dice")

    good = [("d20", (1, 20, 0)), ("2d6", (2, 6, 0)), ("3d8+2", (3, 8, 2)),
            ("1d4-1", (1, 4, -1)), (" 2D6 + 3 ", (2, 6, 3)), ("100d1000", (100, 1000, 0))]
    for text, want in good:
        try:
            got = parse_dice(text)
        except Exception as error:
            fail(f"parse_dice({text!r}) should return {want}, but raised "
                 f"{type(error).__name__}: {error}")
        if tuple(got) != want:
            fail(f"parse_dice({text!r}) should return {want}, but returned {got!r}.")
    for text in ["", "banana", "2x6", "d", "2d", "0d6", "2d1", "101d6", "2d1001", "2d6+"]:
        try:
            got = parse_dice(text)
        except ValueError:
            continue
        except Exception as error:
            fail(f"parse_dice({text!r}) should raise ValueError, but raised {type(error).__name__}.")
        fail(f"parse_dice({text!r}) should raise ValueError, but returned {got!r}.")
    say("  - parse_dice() reads good dice and rejects bad ones")

    for count, sides, modifier in [(3, 6, 2), (1, 20, 0), (5, 4, -3)]:
        first = roll_dice(count, sides, modifier, rng=random.Random(7))
        again = roll_dice(count, sides, modifier, rng=random.Random(7))
        rolls, total = first
        rolls = list(rolls)
        if len(rolls) != count or not all(1 <= roll <= sides for roll in rolls):
            fail(f"roll_dice({count}, {sides}, {modifier}) should return {count} rolls from "
                 f"1 to {sides}, but returned {list(first[0])}.")
        if total != sum(rolls) + modifier:
            fail(f"roll_dice({count}, {sides}, {modifier}) returned rolls {rolls} but a "
                 f"total of {total}. It should be {sum(rolls) + modifier}.")
        if list(again[0]) != rolls:
            fail("roll_dice() should roll with the rng it's given (rng.randint), "
                 "so the same seed gives the same rolls.")
    seen = set()
    rng = random.Random(1)
    for _ in range(300):
        seen.update(roll_dice(1, 6, 0, rng=rng)[0])
    if seen != {1, 2, 3, 4, 5, 6}:
        fail(f"300 rolls of 1d6 only ever gave {sorted(seen)}. Every side should come up.")
    say("  - roll_dice() rolls fairly and adds the modifier")

    await h.load()
    command = h.command("roll", " Name it roll, with an option called dice.")
    if "dice" not in command._params:
        fail("/roll should have an option called dice (async def roll(interaction, dice: str)).")
    interaction = await h.run("roll", dice="3d6+100")
    if not any(103 <= number <= 118 for number in numbers_in(interaction.text())):
        fail("/roll dice:3d6+100 should reply with the total (a number from 103 to 118). "
             f"It replied:\n{interaction.text()}")
    say("  - /roll replies with the total")

    others = [name for name, c in h.commands().items() if name != "roll" and c.parameters]
    if not others:
        fail("Your turn: add another command (not /roll) that takes at least one option.")
    say(f"  - /{others[0]} takes options too")


async def check_03(h):
    await h.load()
    interaction = await h.run("roll", dice="banana")
    if not any(sent.ephemeral for sent in interaction.replies()):
        fail("/roll dice:banana should reply with a friendly error that only the user sees "
             "(ephemeral=True), instead of a normal message.")
    say("  - /roll explains bad dice privately instead of crashing")

    interaction = await h.run("help")
    embeds = [embed for sent in interaction.replies() for embed in sent.embeds]
    if not embeds:
        fail("/help should reply with an embed (embed=discord.Embed(...)).")
    text = message_text(None, embeds)
    for name in h.commands():
        top = name.split()[0]
        if not re.search(r"(?<![\w-])" + re.escape(top) + r"(?![\w-])", text):
            fail(f"/help's embed doesn't mention /{top}. Build the list from "
                 "bot.tree.get_commands() so every command shows up.")
    say("  - /help lists every command in an embed")


async def check_04(h):
    names = cog_files()
    if len(names) < 2:
        fail("Make a cogs folder with at least 2 cog files in it (like cogs/fun.py and cogs/rolling.py).")
    bot = await h.load()
    if len(bot.cogs) < 2:
        fail(f"Your cog files only added {len(bot.cogs)} cog(s). Each file's setup() should "
             "call  await bot.add_cog(...)")
    from discord import app_commands
    with open(os.path.join(FOLDER, "bot.py"), encoding="utf-8", errors="replace") as file:
        source = file.read()
    if "load_extension" not in source:
        fail("bot.py should load your cogs in setup_hook, with await self.load_extension(...).")
    in_cogs = [c for c in h.commands().values() if c.binding is not None]
    if not in_cogs:
        fail("None of your slash commands are inside a cog yet. Move them into your cogs, "
             "using @app_commands.command inside the cog class.")
    say(f"  - {len(bot.cogs)} cogs load: {', '.join(sorted(bot.cogs))}")
    passed = run_tests(5)
    say(f"  - your tests pass ({passed} tests)")


async def check_05(h):
    xp = load_learner_module("xp", "")
    level_for = get_function(xp, "level_for")
    XPStore = get_function(xp, "XPStore")

    levels = [level_for(amount) for amount in range(0, 100001, 50)]
    if not all(isinstance(level, int) for level in levels):
        fail("level_for() should return a whole number (an int).")
    if levels[0] > 1:
        fail(f"level_for(0) is {levels[0]}. Someone with no XP should be level 0 or 1.")
    for amount, (before, after) in enumerate(zip(levels, levels[1:])):
        if after < before:
            fail(f"level_for() goes down: {before} at {amount * 50} XP, but {after} at "
                 f"{(amount + 1) * 50} XP. More XP should never mean a lower level.")
    if levels[-1] <= levels[0]:
        fail("level_for() never goes up, even at 100000 XP.")
    say("  - level_for() goes up with XP")

    with tempfile.TemporaryDirectory() as folder:
        path = os.path.join(folder, "test.db")
        try:
            store = XPStore(path)
            if store.get_xp(1) != 0:
                fail("get_xp() should return 0 for someone with no XP yet.")
            total = store.add_xp(1, 10)
            if total != 10:
                fail(f"add_xp(1, 10) for a new user should return 10, not {total!r}.")
            if store.add_xp(1, 5) != 15:
                fail("add_xp() should return the user's new total (10 + 5 = 15).")
            store.add_xp(2, 50)
            store.add_xp(3, 1)
            board = [tuple(row) for row in store.leaderboard(2)]
            if board != [(2, 50), (1, 15)]:
                fail(f"leaderboard(2) should be [(2, 50), (1, 15)], not {board}.")
            if hasattr(store, "close"):
                store.close()
            again = XPStore(path)
            if again.get_xp(1) != 15:
                fail("XP should still be there after making a new XPStore with the same file. "
                     "Did you forget conn.commit()?")
            if hasattr(again, "close"):
                again.close()
        except CheckFailed:
            raise
        except Exception as error:
            fail(f"XPStore crashed:\n\n{short_traceback(error)}")
    say("  - XPStore adds, ranks and saves XP")

    bot = await h.load()
    for name in ("rank", "leaderboard"):
        h.command(name)
    listeners = [listener for cog in bot.cogs.values()
                 for listener_name, listener in cog.get_listeners() if listener_name == "on_message"]
    if not listeners:
        fail("Add an on_message listener to a cog (@commands.Cog.listener()) that gives XP.")

    async def rank_text(user):
        interaction = await h.run("rank", user=user)
        # Each test user has a different id, so hide ids before comparing replies.
        return interaction.text().replace(str(user.id), "ID")

    chatty, quiet, robot = FakeUser(42), FakeUser(43), FakeUser(44, bot=True)
    record = []
    for user in (chatty, robot):
        for listener in listeners:
            await call_bot_code("Your on_message listener", listener(FakeMessage(user, record)))
    if await rank_text(chatty) == await rank_text(quiet):
        fail("After someone sent a message, /rank showed the same thing as for someone who "
             "never did. Does on_message give XP to message.author.id?")
    if await rank_text(robot) != await rank_text(quiet):
        fail("A bot's message earned XP. Ignore messages where message.author.bot is True.")
    say("  - messages earn XP (but not from bots), and /rank shows it")
    await h.run("leaderboard")
    say("  - /leaderboard replies")
    passed = run_tests(8)
    say(f"  - your tests pass ({passed} tests)")


async def check_06(h):
    poll = load_learner_module("poll", "")
    Poll = get_function(poll, "Poll")
    try:
        p = Poll("Best snack?", ["chips", "fruit", "cookies"])
        if list(p.counts()) != [0, 0, 0]:
            fail(f"A new poll's counts() should be [0, 0, 0], not {list(p.counts())}.")
        if list(p.winners()) != []:
            fail("winners() should be an empty list before anyone votes.")
        p.vote(1, 0)
        p.vote(2, 2)
        p.vote(3, 2)
        if list(p.counts()) != [1, 0, 2]:
            fail(f"After votes for options 0, 2 and 2, counts() should be [1, 0, 2], "
                 f"not {list(p.counts())}.")
        p.vote(3, 0)
        if list(p.counts()) != [2, 0, 1]:
            fail("When someone votes again, their old vote should move to the new option. "
                 f"Expected [2, 0, 1], got {list(p.counts())}.")
        if list(p.winners()) != ["chips"]:
            fail(f"winners() should be ['chips'], not {list(p.winners())}.")
        p.vote(4, 2)
        if sorted(p.winners()) != ["chips", "cookies"]:
            fail(f"With a tie, winners() should list both: ['chips', 'cookies'], "
                 f"not {list(p.winners())}.")
        for bad in (3, -1):
            try:
                p.vote(5, bad)
            except ValueError:
                continue
            fail(f"vote(user, {bad}) on a 3-option poll should raise ValueError.")
    except CheckFailed:
        raise
    except Exception as error:
        fail(f"Poll crashed:\n\n{short_traceback(error)}")
    say("  - Poll counts votes, changes votes and finds winners")

    import discord
    await h.load()
    command = h.command("poll", " Name it poll, with options called question and options.")
    for option in ("question", "options"):
        if option not in command._params:
            fail(f"/poll should have an option called {option}.")
    for text in ("just one", "a, b, c, d, e, f"):
        interaction = await h.run("poll", question="Pick one", options=text)
        if not all(sent.ephemeral for sent in interaction.replies()):
            fail(f"/poll options:{text!r} should reply with an ephemeral error "
                 "(polls need 2 to 5 options).")
    interaction = await h.run("poll", question="Best snack?", options="chips, fruit, cookies")
    views = [sent.view for sent in interaction.replies() if sent.view is not None]
    if not views:
        fail("/poll should send its message with view=... so it has buttons.")
    buttons = [item for item in views[0].children if isinstance(item, discord.ui.Button)]
    if len(buttons) != 3:
        fail(f"/poll with 3 options should have 3 buttons, but it has {len(buttons)}.")
    say("  - /poll checks its options and sends one button per option")

    click = FakeInteraction(h.bot, FakeUser(77))
    await call_bot_code("Clicking a poll button", buttons[1].callback(click))
    if not click.replies():
        fail("Clicking a button didn't respond. Every click needs a response, for example "
             "await interaction.response.edit_message(...) to update the counts.")
    say("  - clicking a button records a vote and responds")


CHECKS = [check_00, check_01, check_02, check_03, check_04, check_05, check_06]


async def run_checks(module):
    """(Runs in its own process.) Run every check up to `module`."""
    harness = Harness()
    for number in range(module + 1):
        say(f"Module {number:02d}:")
        try:
            await CHECKS[number](harness)
        except CheckFailed as problem:
            say(f"\n[NOT YET] {problem}")
            return 1
    say(f"\n[PASS] Everything up to module {module:02d} works. Nice!")
    return 0


def run_module_checks(module):
    """Run the checks in a fresh Python, in a scratch folder, and show the result."""
    with tempfile.TemporaryDirectory() as scratch:
        # The scratch folder catches any files (like databases) your bot makes
        # while being tested, so they don't end up in your project.
        env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONPATH=FOLDER)
        try:
            result = subprocess.run(
                [sys.executable, "-B", os.path.abspath(__file__), "--run", str(module), FOLDER],
                cwd=scratch, env=env, stdin=subprocess.DEVNULL, capture_output=True,
                text=True, encoding="utf-8", errors="replace", timeout=RUN_TIMEOUT,
            )
        except subprocess.TimeoutExpired:
            print(f"\n[NOT YET] The check was still running after {RUN_TIMEOUT} seconds. "
                  "Does something in your bot loop forever?")
            sys.exit(1)
    print(result.stdout, end="")
    if result.returncode not in (0, 1):
        print("\n[NOT YET] Something went wrong while checking your bot:\n")
        print("\n".join(result.stderr.strip().splitlines()[-10:]))
        sys.exit(1)
    sys.exit(result.returncode)


# ---------------------------------------------------------------------------
# Practice problems
# ---------------------------------------------------------------------------
# Each lesson has a practice_NN.py file of small functions to fill in. The
# tests for them live here, so the practice files only contain the problems.
#
# Every problem is tested in its own Python process, so one that loops
# forever can be stopped without stopping the rest.


class NotStarted(Exception):
    """Raised when a practice function hasn't been written yet."""


def is_unstarted(function):
    """
    True if a function's body is still just `pass` (plus maybe a docstring).
    For a class, True if every method in it is still just `pass`.
    """
    try:
        tree = ast.parse(inspect.cleandoc("\n" + inspect.getsource(function)))
    except (OSError, TypeError, SyntaxError):
        return False

    def empty(body):
        if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant):
            body = body[1:]  # skip the docstring
        return all(isinstance(statement, ast.Pass) for statement in body)

    node = tree.body[0]
    if isinstance(node, ast.ClassDef):
        methods = [item for item in node.body
                   if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))]
        return bool(methods) and all(empty(method.body) for method in methods)
    return empty(node.body)


class Practice:
    """Calls functions from a practice file."""

    def __init__(self, practice_module):
        self.practice_module = practice_module

    def get(self, name):
        function = getattr(self.practice_module, name, None)
        if function is None:
            fail(f"Couldn't find {name} in the practice file. Keep the names from the file.")
        if is_unstarted(function):
            raise NotStarted()
        return function

    def call(self, name, *args):
        """Call the learner's function `name`, and wait for it if it's async."""
        function = self.get(name)
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                result = function(*args)
                if inspect.isawaitable(result):
                    result = asyncio.run(asyncio.wait_for(result, TIMEOUT - 1))
        except CheckFailed:
            raise
        except Exception as error:
            fail(f"{name}() crashed with {type(error).__name__}: {error}")
        return result

    def raises(self, name, *args, error=ValueError):
        """Check that calling `name` raises `error`."""
        function = self.get(name)
        shown = ", ".join(repr(a) for a in args)
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                got = function(*args)
        except error as raised:
            return raised
        except Exception as other:
            fail(f"{name}({shown}) should raise {error.__name__}, but raised "
                 f"{type(other).__name__}: {other}")
        fail(f"{name}({shown}) should raise {error.__name__}, but returned {got!r}.")


def expect(name, args, got, want):
    """Fail with a clear message if a function returned the wrong thing."""
    if got != want:
        shown = ", ".join(repr(a) for a in args)
        fail(f"{name}({shown}) should return {want!r}, but returned {got!r}.")


def returns(p, name, *args, want):
    got = p.call(name, *args)
    expect(name, args, got, want)


# --- Module 01 --------------------------------------------------------------
def p01_register(p):
    register = p.get("register")
    commands = getattr(p.practice_module, "COMMANDS", None)
    if not isinstance(commands, dict):
        fail("Keep the COMMANDS dictionary at the top of the practice file.")
    commands.clear()
    try:
        @register("wave")
        def wave():
            return "o/"

        @register("cheer")
        def cheer():
            return "yay"
    except Exception as error:
        fail(f"Using @register(\"wave\") crashed with {type(error).__name__}: {error}")
    if set(commands) != {"wave", "cheer"}:
        fail(f"After @register(\"wave\") and @register(\"cheer\"), COMMANDS should have the "
             f"keys 'wave' and 'cheer', but it has {sorted(commands)}.")
    if not callable(wave) or wave() != "o/":
        fail("register() should give back the original function, so it still works "
             "after being decorated. (Return func from the inner function.)")
    if commands["cheer"]() != "yay":
        fail("COMMANDS['cheer'] should be the cheer function itself.")


def p01_slow_double(p):
    import time
    function = p.get("slow_double")
    if not inspect.iscoroutinefunction(function):
        fail("slow_double should be an async function: async def slow_double(x):")
    start = time.perf_counter()
    got = p.call("slow_double", 21)
    took = time.perf_counter() - start
    expect("slow_double", [21], got, 42)
    if took < 0.09:
        fail("slow_double() should wait 0.1 seconds first, with await asyncio.sleep(0.1).")
    if took > 0.5:
        fail("slow_double() took too long. Use await asyncio.sleep(0.1), not time.sleep().")


def p01_double_all(p):
    import time
    if not inspect.iscoroutinefunction(p.get("double_all")):
        fail("double_all should be an async function.")
    start = time.perf_counter()
    got = p.call("double_all", list(range(10)))
    took = time.perf_counter() - start
    expect("double_all", [list(range(10))], list(got) if got is not None else got,
           [n * 2 for n in range(10)])
    if took > 0.5:
        fail(f"double_all() took {took:.1f} seconds for 10 numbers, so it's doubling them one "
             "at a time. Use asyncio.gather() to wait for them all at once.")


def p01_shout_greeting(p):
    returns(p, "shout_greeting", "Ana", want="HELLO, ANA!")


# --- Module 02 --------------------------------------------------------------
def p02_parse_duration(p):
    for text, want in [("45s", 45), ("2m", 120), ("1h", 3600), ("1h30m", 5400),
                       ("1h 5m 3s", 3903), ("10M", 600), ("2d", 172800)]:
        returns(p, "parse_duration", text, want=want)
    for bad in ["", "abc", "5x", "h", "10"]:
        p.raises("parse_duration", bad)


def p02_split_options(p):
    returns(p, "split_options", "pizza, tacos ,, sushi", want=["pizza", "tacos", "sushi"])
    returns(p, "split_options", "one", want=["one"])
    returns(p, "split_options", " , ", want=[])


def p02_parse_color(p):
    for text, want in [("#ff8800", 0xFF8800), ("FF8800", 0xFF8800),
                       (" #00aa11 ", 0x00AA11), ("#000000", 0)]:
        returns(p, "parse_color", text, want=want)
    for bad in ["", "#ff88", "#gg0000", "red", "#ff88001"]:
        p.raises("parse_color", bad)


def p02_average(p):
    returns(p, "average", "3, 4, 5", want=4.0)
    returns(p, "average", "10", want=10.0)


# --- Module 03 --------------------------------------------------------------
def p03_safe_int(p):
    returns(p, "safe_int", "42", 0, want=42)
    returns(p, "safe_int", " 7 ", 0, want=7)
    returns(p, "safe_int", "seven", -1, want=-1)
    returns(p, "safe_int", "", 5, want=5)


def p03_pick(p):
    InvalidChoice = getattr(p.practice_module, "InvalidChoice", None)
    if not (isinstance(InvalidChoice, type) and issubclass(InvalidChoice, ValueError)):
        fail("Keep the InvalidChoice class from the practice file (it's a kind of ValueError).")
    returns(p, "pick", ["red", "blue"], 1, want="red")
    returns(p, "pick", ["red", "blue"], 2, want="blue")
    for bad in (0, 3):
        raised = p.raises("pick", ["red", "blue"], bad, error=InvalidChoice)
        if "1" not in str(raised) or "2" not in str(raised):
            fail(f"pick(['red', 'blue'], {bad}) raised InvalidChoice, but its message "
                 f"({str(raised)!r}) should say to pick from 1 to 2.")


def p03_format_scores(p):
    returns(p, "format_scores", {"Ana": 50, "Ben": 70, "Cy": 50},
            want="1. Ben - 70\n2. Ana - 50\n3. Cy - 50")
    returns(p, "format_scores", {}, want="No scores yet.")


def p03_describe_error(p):
    returns(p, "describe_error", "4", want="25.0")
    returns(p, "describe_error", "0", want="Can't divide by zero.")
    returns(p, "describe_error", "four", want="That's not a number.")


# --- Module 04 --------------------------------------------------------------
def good_clamp(value, low, high):
    return max(low, min(value, high))


BAD_CLAMPS = [
    ("ignores the high limit", lambda value, low, high: max(low, value)),
    ("ignores the low limit", lambda value, low, high: min(value, high)),
    ("mixes up low and high", lambda value, low, high: max(high, min(value, low))),
    ("is off by one when the value is exactly on the high limit",
     lambda value, low, high: high - 1 if value == high else max(low, min(value, high))),
]


def p04_test_clamp(p):
    test = p.get("test_clamp")
    module = p.practice_module
    original = getattr(module, "clamp", None)
    try:
        module.clamp = good_clamp
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                test()
        except AssertionError as error:
            fail(f"test_clamp() fails on a clamp() that works. Check your expected values. ({error})")
        for why, bad in BAD_CLAMPS:
            module.clamp = bad
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    test()
            except AssertionError:
                continue
            except Exception:
                continue
            fail(f"test_clamp() passed for a broken clamp() that {why}. "
                 "Add an assert that would catch that.")
    finally:
        module.clamp = original


def p04_add_tag(p):
    first = p.call("add_tag", "fun")
    second = p.call("add_tag", "games")
    if second != ["games"]:
        fail(f"add_tag('fun') then add_tag('games') should give ['games'] the second time, "
             f"but it gave {second!r}. The first call's tag is leaking into the second.")
    expect("add_tag", ["fun"], first, ["fun"])
    mine = ["a"]
    returns(p, "add_tag", "b", mine, want=["a", "b"])


def p04_cooldown(p):
    Cooldown = p.get("Cooldown")
    try:
        cool = Cooldown(10)
        checks = [(1, 0, True), (1, 5, False), (2, 5, True), (1, 10, True), (1, 15, False),
                  (2, 14, False), (2, 15.5, True)]
        for user, now, want in checks:
            got = cool.ready(user, now)
            if got != want:
                fail(f"With Cooldown(10), after the calls before it, ready({user}, {now}) "
                     f"should be {want}, not {got!r}. (Calls in order: {checks})")
    except CheckFailed:
        raise
    except Exception as error:
        fail(f"Cooldown crashed with {type(error).__name__}: {error}")


def p04_extension_names(p):
    returns(p, "extension_names", ["fun.py", "__init__.py", "levels.py", "notes.txt", "_draft.py"],
            want=["cogs.fun", "cogs.levels"])
    returns(p, "extension_names", [], want=[])


# --- Module 05 --------------------------------------------------------------
def notes_db():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE notes (id INTEGER PRIMARY KEY, user_id INTEGER, text TEXT)")
    return conn


def p05_add_and_list(p):
    conn = notes_db()
    p.call("add_note", conn, 1, "buy milk")
    p.call("add_note", conn, 2, "walk dog")
    p.call("add_note", conn, 1, "call Sam")
    returns(p, "notes_for", conn, 1, want=["buy milk", "call Sam"])
    returns(p, "notes_for", conn, 3, want=[])


def p05_top_users(p):
    conn = notes_db()
    conn.executemany("INSERT INTO notes (user_id, text) VALUES (?, ?)",
                     [(1, "a"), (2, "b"), (2, "c"), (3, "d"), (2, "e"), (3, "f")])
    got = p.call("top_users", conn, 2)
    expect("top_users", ["conn", 2], [tuple(row) for row in got or []], [(2, 3), (3, 2)])


def p05_delete_note(p):
    conn = notes_db()
    conn.execute("INSERT INTO notes (id, user_id, text) VALUES (7, 1, 'old')")
    returns(p, "delete_note", conn, 7, want=True)
    returns(p, "delete_note", conn, 7, want=False)
    if conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0] != 0:
        fail("delete_note(conn, 7) should remove the note from the table.")


def p05_find_notes(p):
    conn = notes_db()
    conn.executemany("INSERT INTO notes (user_id, text) VALUES (?, ?)",
                     [(1, "don't forget lunch"), (1, "lunch at noon"), (2, "nap")])
    returns(p, "find_notes", conn, "lunch", want=["don't forget lunch", "lunch at noon"])
    returns(p, "find_notes", conn, "don't", want=["don't forget lunch"])
    returns(p, "find_notes", conn, "' OR '1'='1", want=[])


# --- Module 06 --------------------------------------------------------------
def p06_progress_bar(p):
    returns(p, "progress_bar", 0.5, 10, want="#####-----")
    returns(p, "progress_bar", 0, 4, want="----")
    returns(p, "progress_bar", 1, 4, want="####")
    returns(p, "progress_bar", 0.26, 10, want="###-------")
    returns(p, "progress_bar", 1.7, 5, want="#####")
    returns(p, "progress_bar", -1, 3, want="---")


def p06_tally(p):
    votes = {101: "tea", 102: "coffee", 103: "tea"}
    returns(p, "tally", votes, ["coffee", "tea", "juice"], want=[1, 2, 0])
    returns(p, "tally", {}, ["a", "b"], want=[0, 0])


def p06_winners(p):
    returns(p, "winners", ["a", "b", "c"], [2, 5, 1], want=["b"])
    returns(p, "winners", ["a", "b", "c"], [4, 1, 4], want=["a", "c"])
    returns(p, "winners", ["a", "b"], [0, 0], want=[])


def p06_percentages(p):
    returns(p, "percentages", [1, 1, 2], want=[25, 25, 50])
    returns(p, "percentages", [0, 0], want=[0, 0])


# These problems cover two functions, or a class, so give them clearer names.
p04_cooldown.label = "Cooldown class"
p05_add_and_list.label = "add_note() and notes_for()"

# The problems for each module, in the order they appear in practice_NN.py.
PRACTICE_TESTS = {
    1: [p01_register, p01_slow_double, p01_double_all, p01_shout_greeting],
    2: [p02_parse_duration, p02_split_options, p02_parse_color, p02_average],
    3: [p03_safe_int, p03_pick, p03_format_scores, p03_describe_error],
    4: [p04_test_clamp, p04_add_tag, p04_cooldown, p04_extension_names],
    5: [p05_add_and_list, p05_top_users, p05_delete_note, p05_find_notes],
    6: [p06_progress_bar, p06_tally, p06_winners, p06_percentages],
}


def run_one_practice(module, index, path):
    """(Runs in its own process.) Test one problem and print the result as JSON."""
    test = PRACTICE_TESTS[module][index]
    status, message = "pass", ""
    try:
        spec = importlib.util.spec_from_file_location("practice", path)
        practice_module = importlib.util.module_from_spec(spec)
        # Register the module, so inspect can find the source of its classes.
        sys.modules["practice"] = practice_module
        with contextlib.redirect_stdout(io.StringIO()):
            spec.loader.exec_module(practice_module)
        test(Practice(practice_module))
    except NotStarted:
        status = "todo"
    except CheckFailed as problem:
        status, message = "fail", str(problem)
    except Exception as error:
        status, message = "fail", f"Python couldn't load the file: {type(error).__name__}: {error}"
    print("\n" + json.dumps({"status": status, "message": message}))


def run_practice(module, path):
    """Test every practice problem for a module and print a short report."""
    tests = PRACTICE_TESTS[module]
    passed = 0
    for index, test in enumerate(tests):
        label = f"{index + 1}. " + getattr(test, "label", f"{test.__name__[4:]}()")
        try:
            result = subprocess.run(
                [sys.executable, "-B", os.path.abspath(__file__),
                 "--practice-one", str(module), str(index), path],
                stdin=subprocess.DEVNULL, capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=TIMEOUT,
                env=dict(os.environ, PYTHONIOENCODING="utf-8"),
            )
            outcome = json.loads(result.stdout.strip().splitlines()[-1])
        except subprocess.TimeoutExpired:
            outcome = {"status": "fail", "message": f"Still running after {TIMEOUT} "
                       "seconds. Is there a while loop that never ends?"}
        except (ValueError, IndexError):
            outcome = {"status": "fail", "message": result.stderr.strip()}

        if outcome["status"] == "pass":
            passed += 1
            print(f"[PASS]    {label}")
        elif outcome["status"] == "todo":
            print(f"[TODO]    {label}  (not started yet)")
        else:
            print(f"[NOT YET] {label}\n          {outcome['message']}")

    print(f"\n{passed} of {len(tests)} practice problems solved.")
    if passed == len(tests):
        print("All done. On to the steps!")
    sys.exit(0 if passed == len(tests) else 1)


def main():
    # Bots love emoji, but some terminals can't show them. Show a ? instead of crashing.
    for stream in (sys.stdout, sys.stderr):
        with contextlib.suppress(AttributeError, ValueError):
            stream.reconfigure(errors="replace")

    args = sys.argv[1:]

    # Used internally: run the module checks in a fresh process.
    if args[:1] == ["--run"]:
        global FOLDER
        FOLDER = args[2]
        sys.path.insert(0, FOLDER)
        sys.exit(asyncio.run(run_checks(int(args[1]))))

    # Used internally: test a single practice problem in a fresh process.
    if args[:1] == ["--practice-one"]:
        run_one_practice(int(args[1]), int(args[2]), args[3])
        return

    # python check.py practice N [file]
    if args[:1] == ["practice"]:
        if len(args) < 2 or not args[1].isdigit() or int(args[1]) not in PRACTICE_TESTS:
            print(f"Usage: python check.py practice N  (N is 1 to {len(PRACTICE_TESTS)})")
            sys.exit(1)
        module = int(args[1])
        path = os.path.abspath(args[2] if len(args) > 2 else f"practice_{module:02d}.py")
        if not os.path.isfile(path):
            print(f"Couldn't find {path}.")
            print(f"Copy practice_{module:02d}.py from the module's folder into this folder first.")
            sys.exit(1)
        run_practice(module, path)
        return

    if len(args) != 1 or not args[0].isdigit() or not 0 <= int(args[0]) < len(CHECKS):
        print(__doc__)
        sys.exit(1)
    if not os.path.isfile(os.path.join(FOLDER, "bot.py")):
        print(f"Couldn't find bot.py in {FOLDER}.")
        print("Run this from your bot's folder (the one with bot.py in it).")
        sys.exit(1)
    run_module_checks(int(args[0]))


if __name__ == "__main__":
    main()
