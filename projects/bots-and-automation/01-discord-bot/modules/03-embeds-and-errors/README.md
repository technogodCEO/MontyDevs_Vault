# Module 03: Embeds and Errors

**Goal:** replies that look good, a `/roll` that explains bad input instead of crashing, and a `/help` command that always lists every command.

## Concepts

### Embeds

An **embed** is the boxed message with a coloured stripe that bots often send. It can have a title, a description, fields, a footer, a thumbnail and more:

```python
embed = discord.Embed(
    title="Rolling 2d6+3",
    description="**13**",
    color=0xF5A623,                 # a hex colour, like on the web
)
embed.add_field(name="Rolls", value="4, 6")
embed.add_field(name="Modifier", value="+3")
embed.set_footer(text="May the dice be ever in your favour")

await interaction.response.send_message(embed=embed)
```

- Fields sit side by side unless you pass `inline=False`.
- Field names and values can't be empty, and an embed can have up to 25 fields.
- Descriptions and field values understand Discord's Markdown: `**bold**`, `*italics*`, `` `code` ``.

### Ephemeral replies

Add `ephemeral=True` and only the person who used the command sees the reply, with a "Only you can see this" note. It's perfect for error messages and private information, and it keeps the chat tidy.

```python
await interaction.response.send_message("That's not something I can roll.", ephemeral=True)
```

### Handling errors

When a command raises an exception, discord.py prints the error in your terminal, and the user sees "The application did not respond". The bot keeps running, but the user has no idea what went wrong.

For mistakes the **user** can fix, like typing `banana` as dice, catch the exception and explain:

```python
try:
    count, sides, modifier = parse_dice(dice)
except ValueError as error:
    await interaction.response.send_message(f"Hmm. {error}", ephemeral=True)
    return
```

`except ValueError as error` gives you the exception, and `str(error)` (or putting it in an f-string) is the message it was raised with. That's why `parse_dice` should raise *helpful* messages: the user gets to read them.

Only catch what you expect. A bare `except Exception:` would hide real bugs in your own code, which you want to see and fix.

### Commands that know about each other

A help command written by hand goes out of date the moment you add a command. Instead, ask the tree: `bot.tree.get_commands()` returns every slash command, each with a `.name` and a `.description`. Build the help from that and it's always right.

## Practice

### Think it through

**1. What does this print?**

```python
def check_age(age):
    if age < 13:
        raise ValueError("You need to be 13 to use Discord.")
    return "OK"

for age in [15, 9]:
    try:
        print(check_age(age))
    except ValueError as error:
        print("Error:", error)
```

<details><summary>Answer</summary>

```
OK
Error: You need to be 13 to use Discord.
```

The message you raise with is what you get back from `str(error)`.

</details>

**2. What does this print?**

```python
class TooLoud(ValueError):
    pass

try:
    raise TooLoud("Use your indoor voice.")
except ValueError as error:
    print(type(error).__name__, "-", error)
```

<details><summary>Answer</summary>

`TooLoud - Use your indoor voice.` Because `TooLoud` is based on `ValueError`, `except ValueError` catches it too. Making your own exception classes lets code be as specific (`except TooLoud`) or as general (`except ValueError`) as it likes.

</details>

**3. Spot the problem.** This embed causes an error when sent. Why?

```python
embed = discord.Embed(title="Inventory")
items = []
embed.add_field(name="Items", value=", ".join(items))
```

<details><summary>Answer</summary>

`", ".join([])` is an empty string, and Discord rejects embed fields with an empty value (you get a `400 Bad Request` error). Use something like `", ".join(items) or "Nothing yet"`: `or` gives the second value when the first is empty.

</details>

### Try it in code

[`practice_03.py`](practice_03.py) has problems on exceptions and formatting: converting safely, raising your own exception, a ranked score list, and a bug to fix. Copy it into your bot's folder and run:

```sh
python check.py practice 3
```

<details><summary>Hint: safe_int()</summary>

Put the `int(...)` in a `try`, and return the default in the `except ValueError:` block.

</details>

<details><summary>Hint: pick()</summary>

People count from 1, Python lists from 0, so option `number` is `options[number - 1]`. Check the number is between 1 and `len(options)` first, and `raise InvalidChoice(f"...")` if not.

</details>

<details><summary>Hint: format_scores()</summary>

`sorted(scores.items(), key=...)` sorts the `(name, score)` pairs. To sort by score from highest, then by name, the key can return a tuple: `(-score, name)`. `enumerate(..., start=1)` numbers the lines, and `"\n".join(lines)` glues them together.

</details>

<details><summary>Hint: describe_error()</summary>

Python checks `except` blocks from top to bottom and uses the first one that matches. Which block catches *everything*?

</details>

## Steps

Continue in your `bot.py` from Module 02.

1. **Handle bad dice.** Change `/roll` so that when `parse_dice` raises `ValueError`, it replies with the error message, ephemerally, and stops. Try `/roll dice:banana` and `/roll dice:500d6` in Discord.

2. **Reply with an embed.** Change `/roll` to reply with an embed: what was rolled, each die, and the total. Make the total stand out.

3. **Add `/help`.** Add a command named `help` that replies with an embed listing every command, built from `bot.tree.get_commands()`: one line or field per command, with its name and description. Since `help` is also the name of a Python built-in, name the function something else and set the command name in the decorator:
   ```python
   @bot.tree.command(name="help", description="See everything I can do")
   async def help_command(interaction: discord.Interaction):
       ...
   ```

4. **Your turn: embeds everywhere it helps.** Go through your other commands and decide which would look better as embeds. Not all of them: a quick `/ping` reply is fine as text. Use your bot's own colour on every embed, so they look like a set (your `parse_color` from practice can turn `"#f5a623"` into the number).

5. **Your turn: friendly errors in your own command.** Look at the command you made in Module 02. What could a user type that would make it crash? Catch it and reply with something helpful and ephemeral.

> **What the checker needs:** `/roll dice:banana` must reply with `ephemeral=True` instead of crashing, and a command named `help` must reply with an embed that mentions every command by name.

## Make it yours

- **Pick a colour scheme.** One colour for normal replies, another for errors. Store them in variables like `COLOR = 0xF5A623` at the top of `bot.py`.
- **Errors can have personality too.** "Bzzt! I can't roll a banana." is friendlier than "Invalid input."
- **Design your help.** Group commands, add an intro line, a footer with a tip, or your bot's avatar as the thumbnail (`embed.set_thumbnail(url=bot.user.display_avatar.url)`, guarded for when `bot.user` is `None`).

## Check your work

```sh
python check.py 3
```

## Stuck?

- **`400 Bad Request ... Must be 1024 or fewer in length`**: a field value is too long. Rolling 100 dice makes a long list: shorten it, or show only the total for big rolls.
- **`400 Bad Request ... This field is required`**: a field name or value is empty. See practice question 3.
- **`/help` doesn't list commands you just added**: restart the bot. The tree is filled in when `bot.py` loads.
- **`TypeError: send_message() takes from 1 to 2 positional arguments`**: an embed has to be passed by name: `send_message(embed=embed)`.
- **The check says `/help` doesn't mention a command**: make sure each command's name appears in the embed (in a field name, field value, title or description), not only its description.

<details><summary>Hint 1: the shape of /help</summary>

Make an embed, then loop over `bot.tree.get_commands()` and add a field for each one: the name as the field name (with a `/` in front looks nice) and the description as the value. Send the embed at the end.

</details>

<details><summary>Hint 2: the error handling</summary>

The `try` should only wrap the line that can fail (`parse_dice`). In the `except ValueError as error:` block, send the message with `ephemeral=True` and then `return`, so the rest of the command doesn't run.

</details>

<details><summary>Hint 3: nearly there</summary>

```python
@bot.tree.command(name="help", description="See everything I can do")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(title="My commands", color=COLOR)
    for command in bot.tree.get_commands():
        embed.add_field(name=f"/{command.name}", value=command.description, inline=False)
    await interaction.response.send_message(embed=embed)
```

</details>

## Resources

- [discord.py: Embed](https://discordpy.readthedocs.io/en/stable/api.html#discord.Embed): every method an embed has, like `set_author`, `set_thumbnail` and `set_image`.
- [Discord: Markdown text formatting](https://support.discord.com/hc/en-us/articles/210298617-Markdown-Text-101-Chat-Formatting-Bold-Italic-Underline): what you can use in messages and embeds.
- [Python docs: Errors and exceptions](https://docs.python.org/3/tutorial/errors.html): `try`, `except`, `raise`, and making your own exceptions.

## Challenges (optional)

- Add a global error handler with `@bot.tree.error`, so any command that crashes replies with a friendly "Something went wrong" (and still prints the real error to your terminal).
- Give `/help` an optional `command` option that shows more detail about one command, including its options (`command.parameters`).
- Add a `/userinfo` command that shows a member's avatar, name and when they joined, in an embed.

## Next

Continue to [Module 04: Cogs and Tests](../04-cogs-and-tests/).
