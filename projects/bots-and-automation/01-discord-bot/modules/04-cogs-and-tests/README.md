# Module 04: Cogs and Tests

**Goal:** your commands split into **cogs** (one file per group of features) that `bot.py` loads at startup, and automated **tests** that check `dice.py` in under a second.

Nothing new appears in Discord this module. Instead, you're getting the bot ready to grow: the next two modules each add a whole feature, and they'll be much easier to build in this shape.

## Concepts

### Cogs

`bot.py` is getting long, and it'll only get longer. A **cog** is a class that holds a group of related commands (and, later, event listeners). Each cog goes in its own file in a `cogs` folder, and the bot loads them when it starts.

```python
# cogs/fun.py
import discord
from discord import app_commands
from discord.ext import commands


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot      # keep the bot, for things like self.bot.latency

    @app_commands.command(description="Check that Sprocket is awake")
    async def ping(self, interaction: discord.Interaction):
        ms = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"Beep boop! ({ms} ms)")


async def setup(bot):
    # discord.py calls this when it loads the file.
    await bot.add_cog(Fun(bot))
```

What changes when a command moves into a cog:

- `@bot.tree.command(...)` becomes `@app_commands.command(...)`. The cog adds its commands to the tree when it's loaded.
- The command becomes a method, so it takes `self` before `interaction`.
- Anywhere it used `bot`, it uses `self.bot`.

Each cog file ends with an `async def setup(bot)` function. A file with a `setup` function is called an **extension**, and you load it by its module name, like `"cogs.fun"` for `cogs/fun.py`:

```python
await bot.load_extension("cogs.fun")
```

### Automated tests

So far you've tested by running the bot and typing commands. That's slow, and it's easy to forget to re-check something that used to work. An **automated test** is a small function that checks your code does what it should, and runs in milliseconds.

[pytest](https://docs.pytest.org/) finds test functions and runs them. A test is any function whose name starts with `test_`, in a file whose name starts with `test_`, and it checks things with `assert`:

```python
# tests/test_dice.py
import pytest

from dice import parse_dice


def test_two_dice():
    assert parse_dice("2d6") == (2, 6, 0)


def test_rejects_bananas():
    with pytest.raises(ValueError):
        parse_dice("banana")
```

- `assert something` does nothing if `something` is true, and fails the test if it's false. pytest then shows you both sides of the comparison.
- `with pytest.raises(ValueError):` passes only if the code inside raises `ValueError`.

Run every test with:

```sh
python -m pytest
```

(Using `python -m pytest` rather than just `pytest` makes sure Python can find your `dice.py`.)

Because `dice.py` doesn't touch Discord, it's easy to test. That's the payoff of keeping logic in its own files.

**A good test checks one thing, and its name says what.** When `test_rejects_bananas` fails, you know exactly what broke. Test the normal cases, the edges (the smallest and biggest allowed values), and the mistakes.

## Practice

### Think it through

**1. Will this test pass?**

```python
def double(x):
    return x * 2

def test_double():
    double(4) == 8
```

<details><summary>Answer</summary>

It passes, but it tests nothing. Without `assert`, the comparison is worked out and thrown away. Even if `double` returned 9, the test would still pass. A test that can't fail isn't a test.

</details>

**2. What does this print?**

```python
def add_item(item, bag=[]):
    bag.append(item)
    return bag

print(add_item("map"))
print(add_item("rope"))
```

<details><summary>Answer</summary>

```
['map']
['map', 'rope']
```

A default value is made **once**, when Python reads the `def` line, not each time the function is called. So every call that uses the default shares the same list. The usual fix is `bag=None`, then `if bag is None: bag = []` inside the function.

</details>

**3. Which of these are found by pytest?** A file `tests/test_dice.py` containing functions `test_roll`, `check_modifier` and `testing_limits`; and a file `tests/dice_tests.py` containing `test_parse`.

<details><summary>Answer</summary>

`test_roll` and `testing_limits` (any function starting with `test`, in a file starting with `test_`). `check_modifier` has the wrong name, and `dice_tests.py` isn't a test file name, so `test_parse` is never run. If your test count looks too low, check the names.

</details>

### Try it in code

[`practice_04.py`](practice_04.py) has you **write a test** that the checker tries against working and broken code, plus a mutable-default bug, a `Cooldown` class you'll use next module, and a function for finding cog files. Copy it into your bot's folder and run:

```sh
python check.py practice 4
```

<details><summary>Hint: test_clamp()</summary>

Write several `assert clamp(...) == ...` lines: a value in the middle, one below the low limit, one above the high limit, and values exactly on each limit. Each broken version gets one of these cases wrong.

</details>

<details><summary>Hint: add_tag()</summary>

Practice question 2 above is the same bug.

</details>

<details><summary>Hint: Cooldown</summary>

In `__init__`, store `seconds` and make an empty dictionary on `self` that maps user ids to the last time they were ready. In `ready()`, look up the user: if they're there and `now` minus their last time is less than `seconds`, return `False`. Otherwise update their time and return `True`.

</details>

<details><summary>Hint: extension_names()</summary>

Keep names that end with `.py` and don't start with `_`. `name[:-3]` cuts off `.py`. Add `"cogs."` in front, and `sorted()` the result.

</details>

## Steps

Continue from Module 03.

1. **Install pytest.** With your venv active:
   ```sh
   pip install pytest
   ```

2. **Plan your cogs.** Group your commands into at least two cogs by theme. For example, Sprocket has `cogs/fun.py` (ping, hello, joke, help) and `cogs/rolling.py` (roll). Don't name a cog file after one of your own modules, like `cogs/dice.py`, or it gets confusing which `dice` you mean.

3. **Make the cogs.** Create a `cogs` folder next to `bot.py`. For each cog, make a file with a `commands.Cog` class and a `setup` function, like the example above. **Move** your commands into them (don't copy: a command can only exist once) and update them for life inside a class. Imports they need, like `from dice import parse_dice, roll_dice`, go at the top of the cog file.

   `/help` needs the bot to reach the tree: in a cog, that's `self.bot.tree.get_commands()`.

4. **Load the cogs in `setup_hook`.** Before syncing, load every file in `cogs`. You could list them by hand (`await self.load_extension("cogs.fun")`), but then you'd have to remember to add new ones. Instead, find them with `pathlib` (your `extension_names` from practice does the same thing):
   ```python
   from pathlib import Path

   COGS = Path(__file__).parent / "cogs"    # the cogs folder next to bot.py


   class SprocketBot(commands.Bot):
       async def setup_hook(self):
           for file in sorted(COGS.glob("*.py")):
               if not file.name.startswith("_"):
                   await self.load_extension(f"cogs.{file.stem}")
           ...  # then sync, like before
   ```
   Loading has to happen **before** syncing, or Discord is sent an empty list.

5. **Run the bot** and check every command still works in Discord. `bot.py` should now be short: setup, the bot class, `on_ready`, and `bot.run`.

6. **Your turn: write tests.** Make a `tests` folder and a `tests/test_dice.py` file. Write at least **5 tests** for `parse_dice` and `roll_dice`: plain dice, a missing count, positive and negative modifiers, spaces and capitals, things that should raise `ValueError`, the limits, and that `roll_dice`'s total adds up (with a seeded `random.Random`). Run them with `python -m pytest`, and check each one can fail: break `dice.py` on purpose for a moment, and make sure some test notices.

> **What the checker needs:** a `cogs` folder with at least 2 cog files, each with a `setup` function, loaded by `bot.py` with `load_extension`. Every command from earlier modules must still work. And at least 5 passing tests in `tests`, run with `python -m pytest`.

## Make it yours

- **Organise cogs your way.** By theme (fun, games, utility), or one cog per feature. There's no right answer, but each cog should have one clear job.
- **Write the tests you'd want.** If you've had a bug in `dice.py` before, write a test for it, so it can never come back unnoticed.

## Check your work

Stop the bot, then:

```sh
python check.py 4
```

This runs your tests too.

## Stuck?

- **`ExtensionNotFound: Extension 'cogs.fun' could not be loaded`**: the file isn't at `cogs/fun.py`, next to `bot.py`, or the name in `load_extension` doesn't match the file name.
- **`NoEntryPointError`**: the cog file has no `async def setup(bot):` at the bottom (or it isn't `async`).
- **`CommandAlreadyRegistered`**: a command still exists in `bot.py` or another cog. Delete the old copy.
- **`TypeError: ... takes 1 positional argument but 2 were given`**: a command inside a cog is missing `self`, before `interaction`.
- **`NameError: name 'bot' is not defined`** inside a cog: use `self.bot`. Make sure `__init__` saves it, and `setup` passes it: `Fun(bot)`.
- **Commands disappeared from Discord**: the cogs must be loaded *before* `self.tree.sync(...)` in `setup_hook`.
- **pytest says `ModuleNotFoundError: No module named 'dice'`**: run `python -m pytest` from the bot's folder, not plain `pytest`, and not from inside `tests`.
- **pytest says "no tests ran"**: test files must start with `test_` and test functions with `test`.

<details><summary>Hint 1: converting a command</summary>

Before:

```python
@bot.tree.command(description="Say hello")
async def hello(interaction: discord.Interaction):
```

After, indented inside the cog class:

```python
    @app_commands.command(description="Say hello")
    async def hello(self, interaction: discord.Interaction):
```

</details>

<details><summary>Hint 2: what's left in bot.py</summary>

The imports, reading `.env`, `COGS`, the bot class with `setup_hook` (load the cogs, then sync), `bot = ...`, `on_ready`, and the `if __name__ == "__main__":` block. No commands.

</details>

<details><summary>Hint 3: a couple of tests to start from</summary>

```python
import random

import pytest

from dice import parse_dice, roll_dice


def test_missing_count_means_one():
    assert parse_dice("d20") == (1, 20, 0)


@pytest.mark.parametrize("bad", ["", "banana", "0d6", "2d1", "2d6+"])
def test_rejects_bad_dice(bad):
    with pytest.raises(ValueError):
        parse_dice(bad)


def test_total_adds_modifier():
    rolls, total = roll_dice(3, 6, 2, rng=random.Random(1))
    assert total == sum(rolls) + 2
```

`@pytest.mark.parametrize` runs the same test once for each value, and each run counts as a separate test.

</details>

## Resources

- [discord.py: Cogs](https://discordpy.readthedocs.io/en/stable/ext/commands/cogs.html) and [Extensions](https://discordpy.readthedocs.io/en/stable/ext/commands/extensions.html): the official guides. They use prefix commands in their examples, but cogs work the same way with slash commands.
- [pytest: Get started](https://docs.pytest.org/en/stable/getting-started.html): writing and running tests, and `pytest.raises`.
- [pytest: Parametrizing tests](https://docs.pytest.org/en/stable/how-to/parametrize.html): one test, many inputs.

## Challenges (optional)

- Add an owner-only `/reload` command that reloads a cog with `await self.bot.reload_extension(...)`, so you can update code without restarting the bot. (Check `interaction.user.id` against your own ID.)
- Measure how much of `dice.py` your tests run with [pytest-cov](https://pypi.org/project/pytest-cov/): `pip install pytest-cov`, then `python -m pytest --cov=dice`.

## Next

Continue to [Module 05: XP and a Database](../05-xp-and-a-database/).
