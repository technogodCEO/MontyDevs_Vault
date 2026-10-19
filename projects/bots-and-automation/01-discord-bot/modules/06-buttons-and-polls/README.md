# Module 06: Buttons and Polls

**Goal:** a `/poll` command that posts a question with a button for each answer. Anyone can click to vote (or change their vote), and the message updates to show the counts.

## Concepts

### Views and buttons

Messages can carry **components**: buttons, select menus and more. In discord.py they live in a **view**, which you send along with a message:

```python
class Greeting(discord.ui.View):
    @discord.ui.button(label="Wave", style=discord.ButtonStyle.primary, emoji="👋")
    async def wave(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"{interaction.user.mention} waves back!")


await interaction.response.send_message("Hi there!", view=Greeting())
```

- `@discord.ui.button(...)` turns a method into a button. Its **callback** (the method) runs whenever someone clicks.
- `style` sets the colour: `primary` (blurple), `secondary` (grey), `success` (green) or `danger` (red).
- A click is a new **interaction**, from whoever clicked, and it needs a response just like a command does.

### Buttons made in a loop

`@discord.ui.button` is good for a fixed set of buttons. A poll needs one button per option, and the number of options changes. For that, make the buttons yourself and add them with `add_item`. One tidy way is a small `Button` subclass that remembers which option it is:

```python
class OptionButton(discord.ui.Button):
    def __init__(self, label, index):
        super().__init__(label=label, style=discord.ButtonStyle.secondary)
        self.index = index

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"You picked option {self.index}", ephemeral=True)


class Options(discord.ui.View):
    def __init__(self, labels):
        super().__init__()
        for index, label in enumerate(labels):
            self.add_item(OptionButton(label, index))
```

`super().__init__(...)` runs the parent class's setup: `Button`'s, or `View`'s. Your own `__init__` adds to it.

### Updating the message

A button callback can respond by **editing the message the button is on**, instead of sending a new one:

```python
await interaction.response.edit_message(embed=new_embed)
```

That's how a poll shows live counts: every click edits the poll's embed.

### Timeouts

A view stops listening after its **timeout**: 180 seconds by default. After that, clicks fail with "This interaction failed". Pass a longer one with `super().__init__(timeout=3600)` (in seconds), or `timeout=None` for no limit.

Views also stop working when the bot restarts, because the poll only exists in the running program's memory. Surviving restarts takes *persistent views* and saving the poll in your database: a good challenge once this works.

### Keep the rules separate, again

The rules of a poll (one vote each, changing your vote, counting, finding the winner) don't need Discord, so they go in `poll.py`, where they're easy to test. The view just connects clicks to those rules.

## Practice

### Think it through

**1. What does this print?**

```python
votes = {}
votes[101] = "tea"
votes[102] = "coffee"
votes[101] = "coffee"
print(votes, list(votes.values()).count("coffee"))
```

<details><summary>Answer</summary>

`{101: 'coffee', 102: 'coffee'} 2`. A dictionary has one value per key, so storing a user's vote under their id gives "one vote each, and voting again changes it" for free.

</details>

**2. Spot the problem.** Every button in this view says it's the last option. Why?

```python
class Options(discord.ui.View):
    def __init__(self, labels):
        super().__init__()
        for index, label in enumerate(labels):
            button = discord.ui.Button(label=label)

            async def clicked(interaction):
                await interaction.response.send_message(f"Option {index}")

            button.callback = clicked
            self.add_item(button)
```

<details><summary>Answer</summary>

Each `clicked` function uses the variable `index` itself, not its value at the time the function was made. By the time anyone clicks, the loop has finished, and `index` is the last value. This is a classic Python gotcha. The `Button` subclass in the Concepts section avoids it by storing `self.index` on each button.

</details>

**3. How many votes does each option have?** Three people vote: Ana picks option 0, Ben picks option 2, Cy picks option 2. Then Cy changes to option 0. The poll has three options.

<details><summary>Answer</summary>

`[2, 0, 1]`. Ana and Cy on option 0, nobody on option 1, Ben on option 2. This is exactly what the checker tries on your `Poll`.

</details>

### Try it in code

[`practice_06.py`](practice_06.py) has the helpers a poll needs: a text progress bar, tallying votes, finding the winners, and a bug to fix. Copy it into your bot's folder and run:

```sh
python check.py practice 6
```

<details><summary>Hint: progress_bar()</summary>

Clamp the fraction between 0 and 1 first (`max(0, min(fraction, 1))`), then `filled = round(fraction * width)`. `"#" * 3` is `"###"`.

</details>

<details><summary>Hint: tally()</summary>

For each option, count how many values in `votes` equal it. `list(votes.values()).count(option)` does one.

</details>

<details><summary>Hint: winners()</summary>

Find the highest count with `max()`. If it's 0, nobody voted. Otherwise keep each option whose count equals it: `zip(options, counts)` pairs them up.

</details>

<details><summary>Hint: percentages()</summary>

What is `total` when nobody has voted, and what happens when you divide by it?

</details>

## Steps

Continue from Module 05.

1. **Write `poll.py`.** A class `Poll(question, options)` that stores the question and the list of options, and has:

   | Method | What it does |
   | --- | --- |
   | `vote(user_id, index)` | Records that user's vote for option number `index` (counting from 0). Voting again replaces their old vote. Raises `ValueError` if there's no such option. |
   | `counts()` | A list with the number of votes for each option, in order |
   | `winners()` | A list of the option(s) with the most votes: more than one if there's a tie, and empty if nobody has voted |

2. **Test it.** Add `tests/test_poll.py`. Test a fresh poll, a vote, a changed vote, a tie, and an invalid option.

3. **Make a polls cog with `/poll`.** It takes two text options: `question`, and `options` (the answers, separated by commas). It needs **2 to 5** options; anything else gets an ephemeral error. Otherwise it makes a `Poll`, and sends an embed of the question with a view that has one button per option.

4. **Make the buttons vote.** When someone clicks, record their vote in the `Poll` and update the message with `interaction.response.edit_message(...)`, so the embed shows the new counts. Every click must respond somehow.

5. **Try it with a friend** (or a second Discord account) in your test server: vote, change your vote, and watch the counts update.

6. **Your turn: show the results nicely.** Use your `progress_bar` and `percentages` from practice so each option shows a bar and a percentage in the embed. Put the question in the title, and show who's winning.

7. **Your turn: end the poll.** When the view times out, nobody can vote any more, but the buttons still look clickable. Override `on_timeout` in your view to disable every button and edit the message one last time. You'll need to save the message: after sending, `message = await interaction.original_response()` gets it, and `await message.edit(view=self)` updates it.

> **What the checker needs:** `poll.py` with `Poll`, `vote`, `counts` and `winners` as described; a command named `poll` with options named `question` and `options`; an ephemeral error for fewer than 2 or more than 5 options; a view with one button per option; and a response to every click.

## Make it yours

- **Style the buttons.** Emoji on each one, different colours, or a separate "Close poll" button that only the person who made the poll can use (compare `interaction.user.id`).
- **Decide what's public.** Show the counts live, or hide them until the poll closes. Reply to each vote with an ephemeral "Got it, you voted for X".
- **Fit your bot's character.** Sprocket says "Votes are being processed... *whirr*". What does yours say?

## Check your work

Stop the bot, then:

```sh
python check.py 6
```

This is the last module, so it checks everything from Module 00 to here.

## Stuck?

- **"This interaction failed" when clicking a button**: the callback crashed (check the terminal), it didn't respond, or the view timed out or the bot was restarted since the poll was posted. Make a new poll after every restart.
- **`TypeError: ... callback() takes 2 positional arguments but 3 were given`**: a `@discord.ui.button` method takes `(self, interaction, button)`, but a `Button` subclass's `callback` takes only `(self, interaction)`. Check which one you wrote.
- **`ValueError: maximum number of children exceeded`**: a view can hold at most 25 buttons, 5 to a row. Not a problem with 5 options, but it will be if your checks let more through.
- **`400 Bad Request ... label: Must be 80 or fewer in length`**: a button label is too long. Shorten long options, like `label=option[:80]`.
- **Every button votes for the last option**: see practice question 2.

<details><summary>Hint 1: how the pieces connect</summary>

`/poll` makes a `Poll`, then a view, passing it the poll. The view's `__init__` loops over `poll.options` and adds one button per option, giving each button the poll and its index. A button's `callback` calls `self.poll.vote(interaction.user.id, self.index)`, then edits the message.

</details>

<details><summary>Hint 2: one embed-making function</summary>

You need the same embed when the poll is first sent and after every vote. Write a function, like `poll_embed(poll)`, that builds the embed from the poll's question, options and `counts()`, and call it from both places.

</details>

<details><summary>Hint 3: the button</summary>

```python
class VoteButton(discord.ui.Button):
    def __init__(self, poll, index):
        super().__init__(label=poll.options[index], style=discord.ButtonStyle.primary)
        self.poll = poll
        self.index = index

    async def callback(self, interaction: discord.Interaction):
        self.poll.vote(interaction.user.id, self.index)
        await interaction.response.edit_message(embed=poll_embed(self.poll))
```

</details>

## Resources

- [discord.py: Bot UI Kit](https://discordpy.readthedocs.io/en/stable/interactions/api.html#bot-ui-kit): the reference for `View`, `Button`, `Select` and the rest.
- [discord.py examples: views](https://github.com/Rapptz/discord.py/tree/master/examples/views): working examples of buttons, select menus, a counter, a confirmation prompt and persistent views.
- [Discord: Message components](https://discord.com/developers/docs/components/overview): Discord's own docs, including the limits on buttons and labels.

## Challenges (optional)

- Let polls run for a set time: add a `minutes` option, set the view's timeout from it, and announce the winners when it ends.
- Use a **select menu** (`discord.ui.Select`) instead of buttons when there are more than 5 options.
- Make polls survive a restart: save them in your database, and look up *persistent views* in the discord.py examples.

## You did it!

You've built a real Discord bot: slash commands with options, tidy embeds and friendly errors, cogs, automated tests, a database, and interactive buttons. That's the same toolkit big public bots are built with.

Your bot is only online while it runs on your computer, though. Head back to the project's [Going further](../../#going-further) section for hosting it, calling web APIs, scheduled tasks and more.

If you've been using Git, commit your finished bot and put it on GitHub. Your `.gitignore` keeps the token safe.
