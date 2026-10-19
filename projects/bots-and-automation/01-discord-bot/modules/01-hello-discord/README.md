# Module 01: Hello, Discord

**Goal:** a bot with a personality and at least two slash commands that show up in Discord as you type `/`, and reply when used.

## Concepts

### Waiting without freezing: `async` and `await`

A bot spends nearly all its time waiting: for someone to type a command, for Discord to answer, for a message to send. If it waited the normal way, it would freeze and couldn't handle anyone else in the meantime.

discord.py uses **asynchronous** code instead. A function defined with `async def` is a *coroutine*: it can pause at each `await` and let the bot get on with other work until the thing it's waiting for is ready.

```python
import asyncio

async def make_tea():
    print("Kettle on")
    await asyncio.sleep(3)      # pause here; other code can run meanwhile
    print("Tea's ready")
```

Two rules cover almost everything in this project:

- **`await` anything that talks to Discord**, like sending a message. Forget the `await`, and nothing happens (you'll see a "coroutine was never awaited" warning).
- **You can only use `await` inside an `async def`** function.

You never call your coroutines yourself. discord.py runs an **event loop**, which calls them when things happen and juggles everything that's waiting.

### Decorators

A **decorator** is the `@something` line above a function. It hands the function to `something`, which can store it or wrap it. In `bot.py` you already have one:

```python
@bot.event
async def on_ready():
    ...
```

`@bot.event` tells the bot: "here's a function to call when the `on_ready` event happens". The function's name says which event. Decorators run when Python reads your file, which is why the checker can load your bot and see your commands without connecting to Discord.

### Slash commands and the command tree

Slash commands are the commands that pop up when someone types `/` in Discord, with a description and a box for each option. You add one with `@bot.tree.command`:

```python
@bot.tree.command(description="Check that Sprocket is awake")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Beep boop!")
```

- The **function name** becomes the command name (`/ping`). Names must be lowercase, with no spaces. To use a different name, write `@bot.tree.command(name="hi", ...)`.
- The **description** is what Discord shows under the name. Every command needs one.
- `bot.tree` is the bot's **command tree**: the collection of all its slash commands.

### Interactions: replying to a command

When someone uses a command, Discord sends your bot an **interaction**, and your function gets it as its first argument. It has what you need to know about the command (like `interaction.user`, who used it) and a way to reply:

```python
await interaction.response.send_message("Hello!")
```

Discord's rules: **every interaction gets exactly one response, within 3 seconds.** If you don't respond in time, the user sees "The application did not respond". If you respond twice, discord.py raises `InteractionResponded`.

### Syncing: telling Discord about your commands

Your commands live in your code, but Discord has to know about them to show them in the `/` menu. Sending Discord the list is called **syncing**. You can sync:

- **globally**, so the commands work in every server the bot is in. Changes can take a while to show up.
- **to one server** (a *guild*, in Discord's API), which updates instantly. Perfect for testing.

You sync once each time the bot starts, in a special method called `setup_hook`, which discord.py runs after logging in and before connecting. To add your own `setup_hook`, you make your own kind of bot: a class based on `commands.Bot`.

## Practice

### Think it through

**1. What does this print?**

```python
import asyncio

async def greet():
    return "hi"

result = greet()
print(type(result).__name__)
print(asyncio.run(greet()))
```

<details><summary>Answer</summary>

```
coroutine
hi
```

Calling an `async` function doesn't run it. It gives you a coroutine object: a paused piece of work. Something has to run it, either `await` (inside another `async` function) or `asyncio.run()`. (Python also warns that the first coroutine was never awaited.)

</details>

**2. Spot the problem.** This command never replies, but nothing crashes. Why?

```python
@bot.tree.command(description="Say hi")
async def hi(interaction: discord.Interaction):
    interaction.response.send_message("Hi!")
```

<details><summary>Answer</summary>

It's missing `await`. `send_message(...)` creates a coroutine, but nothing runs it, so the message is never sent and the user sees "The application did not respond". Look out for `RuntimeWarning: coroutine ... was never awaited` in your terminal: it almost always means a missing `await`.

</details>

**3. What does this print?**

```python
handlers = {}

def on(event):
    def decorator(func):
        handlers[event] = func
        return func
    return decorator

@on("ready")
def say_ready():
    return "Ready!"

print(list(handlers), handlers["ready"]())
```

<details><summary>Answer</summary>

`['ready'] Ready!`. `@on("ready")` first calls `on("ready")`, which returns `decorator`. Then Python calls `decorator(say_ready)`, which stores the function in `handlers` and gives it back. This is roughly how `@bot.event` and `@bot.tree.command` work.

</details>

### Try it in code

[`practice_01.py`](practice_01.py) has problems on decorators and async code: a command-registering decorator, async functions, running several at once with `asyncio.gather`, and a bug to fix.

1. Copy `practice_01.py` into your bot's folder, next to `check.py`.
2. Fill in each function where it says `# Your code here`. The **FIX THE BUG** problem already has code: find what's wrong.
3. Test your answers, with your venv active:
   ```sh
   python check.py practice 1
   ```

<details><summary>Hint: register()</summary>

`register(name)` isn't the decorator itself: it *makes* one. Look at `on()` in question 3 above: it's the same shape.

</details>

<details><summary>Hint: slow_double()</summary>

`time.sleep()` would freeze everything. `asyncio` has its own sleep that you `await`.

</details>

<details><summary>Hint: double_all()</summary>

`await slow_double(n)` in a loop waits for each one before starting the next. `asyncio.gather(a, b, c)` starts them all and waits for every one, returning their results in order. You can give it a whole list of coroutines with `*`: `await asyncio.gather(*coroutines)`.

</details>

<details><summary>Hint: shout_greeting()</summary>

Read the error: what type of object does it say `greeting` is? Compare with question 1.

</details>

## Steps

Continue in your `bot.py` from Module 00.

1. **Make your own kind of bot, and sync in `setup_hook`.** Replace the `bot = commands.Bot(...)` line with a class based on `commands.Bot`, and make the bot from that. Give the class your bot's name:
   ```python
   GUILD_ID = os.getenv("GUILD_ID")


   class SprocketBot(commands.Bot):
       async def setup_hook(self):
           # Runs once, after logging in and before connecting.
           if GUILD_ID:
               # Copy every command to the test server, and sync just there:
               # updates show up instantly.
               guild = discord.Object(id=int(GUILD_ID))
               self.tree.copy_global_to(guild=guild)
               await self.tree.sync(guild=guild)
           else:
               await self.tree.sync()


   intents = discord.Intents.default()
   bot = SprocketBot(command_prefix="!", intents=intents)
   ```
   Keep the variable called `bot`: the checker looks for it.

2. **Add `/ping`.** Below `on_ready`, add a command that replies with the bot's latency (how long Discord takes to answer it, in seconds):
   ```python
   @bot.tree.command(description="Check that Sprocket is awake")
   async def ping(interaction: discord.Interaction):
       ms = round(bot.latency * 1000)
       await interaction.response.send_message(f"Beep boop! I'm awake. ({ms} ms)")
   ```

3. **Run it and try it.** Start the bot with `python bot.py`, then type `/` in your test server. Your bot's commands appear in the menu. Pick `/ping` and press Enter.

   Don't see it? Press **Ctrl+R** (**Cmd+R** on a Mac) to reload Discord. If it's still missing, check `GUILD_ID` in `.env` (see Stuck?).

   **Every time you change your code, stop the bot with Ctrl+C and start it again.** The running bot doesn't notice changes to the file.

4. **Your turn: a second command.** Add a command of your own that greets whoever used it. `interaction.user.mention` is text that turns into an @mention of them, and `interaction.user.display_name` is their name in the server. Make it sound like your bot.

5. **Your turn: more commands.** Add at least one more command that shows your bot's personality: a `/joke` with a few jokes to pick from with `random.choice`, a `/compliment`, an `/about` with the bot's backstory. Anything goes.

> **What the checker needs:** a variable called `bot`; at least 2 slash commands; a description on every command; and every command must reply with `await interaction.response.send_message(...)`. It calls each command with a pretend Discord, so keep your commands to things like `interaction.user`, `interaction.guild` and `interaction.channel`.

## Make it yours

- **Pick a personality and stick to it.** A robot that says *beep*, a pirate, a wizard who's tired of being asked things. Every reply should sound like the same character.
- **Give it a face.** Back in the Developer Portal, give your application an avatar and a description. They show on the bot's profile.
- **Name things your way.** Commands can have any lowercase name. `/ping` could be `/poke`, `/heartbeat` or `/areyouthere`.

## Check your work

Stop the bot, then:

```sh
python check.py 1
```

This also re-runs the Module 00 checks.

## Stuck?

- **The commands don't appear in the `/` menu**: reload Discord with **Ctrl+R**. Check that `GUILD_ID` in `.env` is your test server's ID (right-click the server icon → **Copy Server ID**), and that you invited the bot with the `applications.commands` scope (Module 00, step 7). Without `GUILD_ID`, global commands can take a while to appear.
- **Every command appears twice**: you synced globally once (without `GUILD_ID`) and now sync to your server too. Both sets show up in that server. To clear the global ones, run the bot once with this in `setup_hook` instead, then put it back:
  ```python
  self.tree.clear_commands(guild=None)
  await self.tree.sync()
  ```
- **"The application did not respond"**: your command didn't reply within 3 seconds, usually because of a missing `await`, or because it crashed. Check the terminal for an error.
- **`RuntimeWarning: coroutine '...' was never awaited`**: a missing `await` on the line it mentions.
- **`discord.errors.InteractionResponded`**: your command responded twice. Use `send_message` once per command.
- **`TypeError: ... missing 1 required positional argument: 'interaction'`**: every command function needs `interaction` as its first parameter.
- **`CommandSignatureMismatch`** when you use a command: you changed a command but Discord still has the old version. Restart the bot so it syncs again.

<details><summary>Hint 1: where things go</summary>

The order in `bot.py` matters: imports, then reading `.env`, then the class, then `bot = ...`, then the commands (which use `bot`), then the `if __name__ == "__main__":` block at the very bottom.

</details>

<details><summary>Hint 2: the greeting command</summary>

It has the same shape as `/ping`: a decorator with a description, an `async def` that takes `interaction`, and one `await interaction.response.send_message(...)`. Use an f-string to put `interaction.user.mention` into the message.

</details>

<details><summary>Hint 3: nearly there</summary>

```python
@bot.tree.command(description="Say hello to Sprocket")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"Hello, {interaction.user.mention}! *whirr*"
    )
```

</details>

## Resources

- [discord.py: Interactions API](https://discordpy.readthedocs.io/en/stable/interactions/api.html): the reference for `Interaction`, `CommandTree` and `app_commands`. Skim the sections on `Interaction` and `InteractionResponse` to see what else you can do.
- [Real Python: Async IO in Python](https://realpython.com/async-io-python/): a longer look at `async` and `await`. The first few sections are plenty.
- [Real Python: Primer on Python decorators](https://realpython.com/primer-on-python-decorators/): how decorators work, if you want to write your own.

## Challenges (optional)

- Make `/ping` reply with a random one of several messages.
- Change the bot's status to "Playing ..." or "Listening to ..." in `on_ready`, with `await bot.change_presence(activity=discord.Game("..."))`.
- Add a command that only *you* can see the reply to, by adding `ephemeral=True` to `send_message`.

## Next

Continue to [Module 02: Options and Dice](../02-options-and-dice/).
