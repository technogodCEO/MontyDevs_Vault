# Module 02: Options and Dice

**Goal:** a `/roll` command that rolls dice written like `2d6+3`, with the dice rules in their own `dice.py` file, plus a command of your own that takes options.

## Concepts

### Options

A slash command's options are just the function's parameters. Their **type hints** tell Discord what kind of box to show and what to allow:

```python
@bot.tree.command(description="Repeat after me")
@app_commands.describe(text="What to say", times="How many times (1 to 5)")
async def echo(interaction: discord.Interaction, text: str,
               times: app_commands.Range[int, 1, 5] = 1):
    await interaction.response.send_message(" ".join([text] * times))
```

- `text: str` makes a text box. `int`, `float` and `bool` work too, and Discord rejects anything that isn't the right type before your code even runs.
- `discord.Member` lets the user pick someone from the server.
- `app_commands.Range[int, 1, 5]` only allows whole numbers from 1 to 5.
- A parameter with a default value (`= 1`) is optional.
- `@app_commands.describe(...)` gives each option a description. Add `from discord import app_commands` at the top of your file to use it.

To offer a fixed list of choices, use `typing.Literal`:

```python
from typing import Literal

async def coin(interaction: discord.Interaction, call: Literal["heads", "tails"]):
```

### Keep the logic out of the Discord code

`/roll` needs to understand text like `3d8+2` ("roll three 8-sided dice and add 2") and then roll. None of that has anything to do with Discord, so it goes in its own file, `dice.py`, as plain functions. The command itself stays short: read the option, call the functions, reply.

This pays off quickly. You can try `dice.py` in a terminal in seconds without starting the bot, and in Module 04 you'll write automated tests for it. Most of what makes a bot good lives in files like this.

### Parsing with regular expressions (optional)

Dice notation has a clear pattern: an optional count, a `d`, the number of sides, and an optional `+` or `-` modifier. You can parse it by hand with `split()` and `str.isdigit()`, or describe the whole pattern with a **regular expression**:

```python
import re

match = re.fullmatch(r"(\d+)x(\d+)", "1920x1080")
if match:
    width, height = int(match.group(1)), int(match.group(2))   # 1920, 1080
```

`\d+` means "one or more digits", and each pair of brackets captures a group you can read back. `re.fullmatch` only matches if the *whole* text fits the pattern. Either approach is fine for `dice.py`.

### Randomness you can test

`random.randint(1, 6)` rolls a die. But random results are hard to test: how do you check the answer when it's different every time? The trick is to let the caller pass in the random number generator:

```python
import random

def flip(rng=random):
    return rng.choice(["heads", "tails"])

flip()                      # really random
flip(rng=random.Random(4))  # a seeded generator: same answer every time
```

The `random` module and a `random.Random(seed)` object have the same methods, so the function works with either. The checker uses a seeded one to make sure your rolls add up.

## Practice

### Think it through

**1. What does this print?**

```python
text = " 2D6 + 3 "
print(text.replace(" ", "").lower())
print("3d8+2".split("d"))
print("12".isdigit(), "-1".isdigit(), "".isdigit())
```

<details><summary>Answer</summary>

```
2d6+3
['3', '8+2']
True False False
```

`isdigit()` is `False` for `"-1"` (the `-` isn't a digit) and for the empty string. Remember that when you parse `-1` modifiers.

</details>

**2. Spot the problem.** A user types `/roll dice:banana`. What happens?

```python
@bot.tree.command(description="Roll dice")
async def roll(interaction: discord.Interaction, dice: str):
    count, sides, modifier = parse_dice(dice)   # raises ValueError for "banana"
    rolls, total = roll_dice(count, sides, modifier)
    await interaction.response.send_message(f"You rolled {total}")
```

<details><summary>Answer</summary>

`parse_dice` raises `ValueError`, the command stops before replying, and the user sees "The application did not respond" (the error appears in your terminal). Nothing breaks permanently, but it's not friendly. You'll fix exactly this in Module 03.

</details>

**3. Will these two lines always print the same list?**

```python
import random
print([random.Random(42).randint(1, 6) for _ in range(3)])
rng = random.Random(42)
print([rng.randint(1, 6) for _ in range(3)])
```

<details><summary>Answer</summary>

No. The first line makes a **new** generator with seed 42 for every roll, so it gets the first number of that sequence three times (like `[6, 6, 6]`). The second makes one generator and keeps using it, so it gets the first three numbers of the sequence. That's why `roll_dice` should take one `rng` and use it for every die.

</details>

### Try it in code

[`practice_02.py`](practice_02.py) has parsing problems: durations like `1h30m`, comma-separated options, hex colours, and a bug to fix. Copy it into your bot's folder and run:

```sh
python check.py practice 2
```

<details><summary>Hint: parse_duration()</summary>

Clean up the text first (spaces, case). Then either walk through it character by character, building up digits until you reach a unit letter, or use `re.fullmatch(r"(\d+[dhms])+", text)` to check the format and `re.findall(r"(\d+)([dhms])", text)` to get each number-and-unit pair. A dictionary from unit to seconds keeps the maths tidy.

</details>

<details><summary>Hint: split_options()</summary>

`split(",")`, then `strip()` each piece, and only keep the ones that aren't empty. A list comprehension with an `if` does it in one line.

</details>

<details><summary>Hint: parse_color()</summary>

`int("ff8800", 16)` reads hex. Strip spaces and the `#` first, then check it's exactly 6 characters, all from `0123456789abcdefABCDEF`, before converting. `int()` alone would accept some things you don't want, like `"ff88"`.

</details>

<details><summary>Hint: average()</summary>

What type is each `part`? What does the error say you can't add together?

</details>

## Steps

Continue in your `bot.py` from Module 01.

1. **Write `dice.py`.** Make a new file, `dice.py`, next to `bot.py`, with two functions. No Discord code goes in this file.

   **`parse_dice(text)`** reads dice notation and returns `(count, sides, modifier)`:

   | Text | Returns |
   | --- | --- |
   | `"d20"` | `(1, 20, 0)`: no count means 1 |
   | `"2d6"` | `(2, 6, 0)` |
   | `"3d8+2"` | `(3, 8, 2)` |
   | `"1d4-1"` | `(1, 4, -1)` |
   | `" 2D6 + 3 "` | `(2, 6, 3)`: ignore spaces and case |

   It raises `ValueError` with a helpful message for anything else, like `"banana"`, `"2d"`, `"2d6+"` or `""`. It also rejects silly sizes: **1 to 100 dice, with 2 to 1000 sides**.

   **`roll_dice(count, sides, modifier=0, rng=random)`** rolls `count` dice with `rng.randint` and returns `(rolls, total)`: the list of rolls, and their sum plus the modifier.

2. **Try it without Discord.** In the terminal (venv active), start Python by typing `python`, and try it:
   ```python
   >>> from dice import parse_dice, roll_dice
   >>> parse_dice("3d8+2")
   (3, 8, 2)
   >>> roll_dice(3, 8, 2)
   ([5, 1, 8], 16)
   >>> parse_dice("banana")
   ValueError: ...
   ```
   Type `exit()` to leave. Fixing bugs here is much quicker than restarting the bot each time.

3. **Add `/roll`.** In `bot.py`, import your functions (`from dice import parse_dice, roll_dice`) and add a command called `roll`, with one text option called `dice`. It parses the option, rolls, and replies with the rolls and the total. Describe the option with `@app_commands.describe` so users know what to type.

4. **Your turn: a command with options.** Add another command (not `/roll`) with at least one option, designed by you. Use a type you haven't used yet: a `Range`, a `Literal` list of choices, a `discord.Member`, or an optional parameter with a default. Some ideas: `/choose` between comma-separated options (your `split_options` from practice would help), `/rate` something out of 10, `/hug` another member, or `/8ball` that answers a question.

> **What the checker needs:** `dice.py` with `parse_dice` and `roll_dice` as described above, and a command named `roll` with an option named `dice`. Its reply must include the total. And at least one other command with an option.

## Make it yours

- **Make rolling dramatic.** Celebrate a natural 20, groan at a 1, or add a sound effect.
- **Choose your format.** Show each die, just the total, or both. Maybe bold the total with `**13**` (Discord uses Markdown).
- **Your second command can be anything.** It's a good place to try out the personality from Module 01.

## Check your work

```sh
python check.py 2
```

## Stuck?

- **`ModuleNotFoundError: No module named 'dice'`**: `dice.py` must be in the same folder as `bot.py`, and you must run the bot from that folder.
- **The new option doesn't show up in Discord**: restart the bot so it syncs, then reload Discord (**Ctrl+R**).
- **`TypeError: cannot unpack non-iterable NoneType object`**: `parse_dice` or `roll_dice` forgot to `return` something on some path.
- **`/roll` works for `2d6` but not `d20`**: when the count is missing, it should be 1. Check what your parsing gets for the part before the `d` (it's an empty string).

<details><summary>Hint 1: a plan for parse_dice</summary>

1. Remove spaces and lowercase the text.
2. Split off the modifier: find a `+` or `-` after the `d` and read the number after it (no modifier means 0).
3. Split what's left on `"d"`: the left part is the count (empty means 1), the right part is the sides.
4. Check every part is digits, then convert and check the limits. Raise `ValueError` at the first problem.

</details>

<details><summary>Hint 2: the regular expression version</summary>

The pattern `(\d*)d(\d+)([+-]\d+)?` has three groups: the count (`\d*` allows it to be empty), the sides, and an optional modifier. With `match = re.fullmatch(pattern, cleaned)`, `match.group(3)` is `None` when there's no modifier, and `int("+2")` is `2`.

</details>

<details><summary>Hint 3: the /roll command</summary>

```python
@bot.tree.command(description="Roll some dice, like 2d6+1")
@app_commands.describe(dice="Which dice to roll, like d20 or 3d6+2")
async def roll(interaction: discord.Interaction, dice: str):
    count, sides, modifier = parse_dice(dice)
    rolls, total = roll_dice(count, sides, modifier)
    await interaction.response.send_message(f"You rolled {rolls}: **{total}**")
```

</details>

## Resources

- [discord.py: app_commands](https://discordpy.readthedocs.io/en/stable/interactions/api.html#decorators): the `describe`, `choices` and `rename` decorators, and the `Range` type.
- [Python docs: Regular expression HOWTO](https://docs.python.org/3/howto/regex.html): read up to "Grouping" for everything `dice.py` needs.
- [regex101](https://regex101.com/): paste a pattern and some text, and see exactly what matches and why. Choose the Python flavour on the left.

## Challenges (optional)

- Support `4d6kh3`: roll 4, **k**eep the **h**ighest 3 (how many games roll stats).
- Support several groups at once: `1d20+1d4+2`.
- Add an `advantage` option that rolls twice and keeps the higher roll.

## Next

Continue to [Module 03: Embeds and Errors](../03-embeds-and-errors/).
