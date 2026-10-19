# Module 05: XP and a Database

**Goal:** people earn XP by chatting, and level up as it grows. `/rank` shows someone's level, `/leaderboard` shows the top chatters, and everything is saved in a SQLite database, so nothing is lost when the bot restarts.

## Concepts

### Why a database?

Everything your bot knows disappears when it stops. To keep XP between restarts, it has to be saved somewhere. You could write a JSON file, like a game's save file, but a **database** is better at this job: many small updates, looking things up quickly, and sorting ("who has the most XP?").

Python comes with **SQLite**, a database that lives in a single file. There's nothing to install.

### SQL in five statements

You talk to the database in **SQL**. A database holds **tables**, which are like spreadsheets: each **row** is one record, and each **column** has a name and a type.

```python
import sqlite3

conn = sqlite3.connect("bot.db")    # opens the file (or creates it)

# Make a table, unless it's already there.
conn.execute("CREATE TABLE IF NOT EXISTS snacks (name TEXT PRIMARY KEY, stars INTEGER)")

# Add rows. The ?s are filled in, in order, from the tuple.
conn.execute("INSERT INTO snacks (name, stars) VALUES (?, ?)", ("crisps", 4))
conn.execute("INSERT INTO snacks (name, stars) VALUES (?, ?)", ("grapes", 3))

# Change rows.
conn.execute("UPDATE snacks SET stars = stars + 1 WHERE name = ?", ("crisps",))

# Save the changes to the file. Without this, they're thrown away.
conn.commit()

# Read rows.
best = conn.execute("SELECT name, stars FROM snacks ORDER BY stars DESC LIMIT 1").fetchone()
print(best)                                      # ('crisps', 5)
everything = conn.execute("SELECT name FROM snacks").fetchall()
print(everything)                                # [('crisps',), ('grapes',)]
```

- `fetchone()` gives one row as a tuple, or `None` if nothing matched. `fetchall()` gives a list of tuples.
- `PRIMARY KEY` means no two rows can have the same value in that column.
- A tuple with one item needs a trailing comma: `("crisps",)`.

### Always use `?` placeholders

Never build SQL with f-strings:

```python
conn.execute(f"SELECT * FROM snacks WHERE name = '{name}'")   # don't
conn.execute("SELECT * FROM snacks WHERE name = ?", (name,))  # do
```

With the f-string, a name like `don't` breaks the query (its `'` ends the text early), and a sneaky user can type something that changes what the query does. That's called **SQL injection**, and it's one of the most common security bugs there is. With `?`, SQLite treats the value purely as data, whatever it contains.

### "Insert, or add to it if it's there"

For XP you want: if this user has no row yet, make one; if they do, add to it. SQLite can do both in one statement, called an **upsert**:

```python
conn.execute(
    "INSERT INTO snacks (name, stars) VALUES (?, ?) "
    "ON CONFLICT(name) DO UPDATE SET stars = stars + excluded.stars",
    ("grapes", 1),
)
```

`excluded.stars` means "the value we tried to insert". You could also do it in two steps: `SELECT` the row, then `INSERT` or `UPDATE` depending on whether it exists.

### Listening for messages

Cogs can listen for events as well as hold commands. A **listener** is a method marked with `@commands.Cog.listener()`, named after the event:

```python
@commands.Cog.listener()
async def on_message(self, message: discord.Message):
    if message.author.bot:
        return              # ignore bots, including this one
    print(f"{message.author.display_name} said something")
```

Your bot only gets `on_message` for channels it can see. It doesn't need to read what the message *says* to give XP, so the default intents are enough. (Reading message text needs the privileged Message Content intent, which you don't need for this project.)

### Cooldowns

If every message earned XP, people would just spam. Most XP bots only reward one message per person per minute, which is what your `Cooldown` class from Module 04's practice does.

## Practice

### Think it through

**1. What does this print?**

```python
import sqlite3
conn = sqlite3.connect(":memory:")      # a database that only lives in memory
conn.execute("CREATE TABLE xp (user_id INTEGER PRIMARY KEY, xp INTEGER)")
conn.execute("INSERT INTO xp VALUES (?, ?)", (1, 30))
conn.execute("INSERT INTO xp VALUES (?, ?)", (2, 80))
print(conn.execute("SELECT xp FROM xp WHERE user_id = ?", (1,)).fetchone())
print(conn.execute("SELECT xp FROM xp WHERE user_id = ?", (3,)).fetchone())
print(conn.execute("SELECT user_id FROM xp ORDER BY xp DESC").fetchall())
```

<details><summary>Answer</summary>

```
(30,)
None
[(2,), (1,)]
```

Rows come back as tuples, even with one column, so the XP itself is `row[0]`. A user with no row gives `None`, which your code has to handle (that's someone with 0 XP).

</details>

**2. Spot the problem.** The bot gives XP, `/rank` shows it, but after a restart everyone is back to 0. Why?

```python
def add_xp(self, user_id, amount):
    self.conn.execute("UPDATE xp SET xp = xp + ? WHERE user_id = ?", (amount, user_id))
    return self.get_xp(user_id)
```

<details><summary>Answer</summary>

There's no `self.conn.commit()`. The same connection can see its own changes, so everything looks fine while the bot runs, but they're never saved to the file. (Also, `UPDATE` changes nothing for a user who doesn't have a row yet. See the upsert above.)

</details>

**3. Design a curve.** With `level = xp // 100`, how many messages (at 20 XP each) does it take to reach level 1? Level 10? With `level = int((xp / 100) ** 0.5)`?

<details><summary>Answer</summary>

With `xp // 100`, every level takes 100 XP: 5 messages for level 1, 50 for level 10. With the square root, level *n* needs 100 × *n*² XP: still 5 messages for level 1, but 500 for level 10. Early levels come fast, and later ones take real effort. Most XP bots use a curve like this, so new members level up quickly and long-time members still have something to aim for.

</details>

### Try it in code

[`practice_05.py`](practice_05.py) has SQL problems on a `notes` table: adding and listing notes, counting with `GROUP BY`, deleting, and an injection bug to fix. Copy it into your bot's folder and run:

```sh
python check.py practice 5
```

<details><summary>Hint: add_note() and notes_for()</summary>

`INSERT INTO notes (user_id, text) VALUES (?, ?)`, then `commit()`. For the list: `SELECT text FROM notes WHERE user_id = ? ORDER BY id`, and turn each row tuple into just its text with a list comprehension.

</details>

<details><summary>Hint: top_users()</summary>

`SELECT user_id, COUNT(*) FROM notes GROUP BY user_id` counts the notes for each user. Then sort with `ORDER BY COUNT(*) DESC` and cut it off with `LIMIT ?`.

</details>

<details><summary>Hint: delete_note()</summary>

`conn.execute(...)` returns a cursor, and `cursor.rowcount` is how many rows the statement changed.

</details>

<details><summary>Hint: find_notes()</summary>

The `%` signs go in the *value*, not the SQL: `LIKE ?`, with `(f"%{word}%",)` as the parameters.

</details>

## Steps

Continue from Module 04.

1. **Design your levels.** Decide how XP turns into levels. Write it as `level_for(xp)` in a new file, `xp.py`: it takes an amount of XP and returns a whole-number level. Someone with 0 XP is level 0 (or 1, if you prefer), and more XP never means a lower level. Use practice question 3 to help you choose.

2. **Write `XPStore`.** In `xp.py`, write a class that keeps XP in a SQLite database:

   | Method | What it does |
   | --- | --- |
   | `XPStore(path)` | Opens (or creates) the database file at `path`, and makes the table if it doesn't exist |
   | `get_xp(user_id)` | Returns that user's XP, or 0 if they have none |
   | `add_xp(user_id, amount)` | Adds `amount` to their XP, saves it, and returns their new total |
   | `leaderboard(limit=10)` | Returns up to `limit` `(user_id, xp)` pairs, highest XP first |

   Like `dice.py`, this file has no Discord code in it.

3. **Test it.** Add `tests/test_xp.py`, with tests for `level_for` and `XPStore`. pytest gives any test a fresh, empty folder if it asks for one by naming a parameter `tmp_path`, which is perfect for a test database:
   ```python
   def test_new_user_has_no_xp(tmp_path):
       store = XPStore(tmp_path / "test.db")
       assert store.get_xp(123) == 0
   ```
   Test that XP adds up, that it's still there in a new `XPStore` opened on the same file, and that the leaderboard is in the right order. You need at least **8 tests** in total now, including your dice tests.

4. **Make a levels cog.** Add `cogs/levels.py` with a cog that makes an `XPStore("xp.db")` in its `__init__`. The database file appears in whichever folder you run the bot from. (Your `.gitignore` already ignores `*.db`, so it won't end up on GitHub.)

5. **Give XP for messages.** Add an `on_message` listener to the levels cog. It ignores bots, gives the author some XP (a fixed amount, or a random one like 15 to 25), and respects a per-user cooldown. Your `Cooldown` class from practice fits here (`time.time()` gives the current time in seconds).

6. **Add `/rank`.** It shows someone's XP and level. Give it an optional `member: discord.Member = None` option, so people can look up each other, and use `interaction.user` when it's left empty.

7. **Add `/leaderboard`.** It shows the top 10. To show names without looking each user up, use a mention: `f"<@{user_id}>"` displays as their name in Discord, and doesn't ping anyone when it's inside an embed.

8. **Your turn: level-up messages.** When someone's level goes up, announce it in the channel with `await message.channel.send(...)`. You'll need their level from before the XP was added.

> **What the checker needs:** `xp.py` with `level_for` and `XPStore` as described; an `on_message` listener in a cog that gives XP to `message.author.id` and ignores bots; commands named `rank` and `leaderboard`; and at least 8 passing tests. The checker sends a pretend message, then compares what `/rank` says for that person and for someone who never posted, so `/rank` must show the XP or level.

## Make it yours

- **Your curve, your rewards.** Fast levels or slow ones? Bonus XP for the first message of the day? Different amounts for different channels?
- **Make `/rank` something to show off.** An embed in their colour, a progress bar to the next level (you'll write one in Module 06's practice), or a title for each level ("Rookie", "Regular", "Legend").
- **Celebrate.** A big level-up message at every 5th level, or a special one at level 10.

## Check your work

Stop the bot, then:

```sh
python check.py 5
```

The checker runs your bot in a temporary folder, so the database it creates while testing doesn't mix with your real one.

## Stuck?

- **`sqlite3.OperationalError: no such table: xp`**: the `CREATE TABLE IF NOT EXISTS` must run in `XPStore.__init__`, before anything reads from the table.
- **`sqlite3.OperationalError: near "...": syntax error`**: a typo in your SQL, or text put straight into the SQL instead of a `?`. Print the statement to see exactly what SQLite was given.
- **`sqlite3.ProgrammingError: Incorrect number of bindings supplied`**: the number of `?`s doesn't match the number of values. A single value needs a trailing comma: `(user_id,)`.
- **XP resets when the bot restarts**: a missing `conn.commit()` (practice question 2), or the bot is running from a different folder each time, so it opens a different `xp.db`.
- **`on_message` never runs**: the listener needs `@commands.Cog.listener()` above it, must be named `on_message`, and the cog must be loaded. Also check the bot can see the channel.
- **`/leaderboard` shows `<@123...>` instead of names**: mentions only display as names for users Discord has loaded on your screen. In embeds this usually works; in plain text on mobile it may not. It's harmless.

<details><summary>Hint 1: the shape of XPStore</summary>

`__init__` saves `sqlite3.connect(path)` as `self.conn`, creates a table like `xp (user_id INTEGER PRIMARY KEY, xp INTEGER NOT NULL)`, and commits. Each method runs one or two statements on `self.conn`. `get_xp` turns a `None` row into 0.

</details>

<details><summary>Hint 2: add_xp</summary>

Use the upsert from the Concepts section, with `user_id` as the conflict column, then `commit()`, then return `self.get_xp(user_id)`.

</details>

<details><summary>Hint 3: the listener</summary>

```python
@commands.Cog.listener()
async def on_message(self, message: discord.Message):
    if message.author.bot or message.guild is None:
        return
    if not self.cooldown.ready(message.author.id, time.time()):
        return
    before = level_for(self.store.get_xp(message.author.id))
    total = self.store.add_xp(message.author.id, random.randint(15, 25))
    # ...compare level_for(total) with before, and announce a level-up
```

</details>

## Resources

- [Python docs: sqlite3 tutorial](https://docs.python.org/3/library/sqlite3.html#tutorial): a short walkthrough of connecting, creating, inserting and querying.
- [SQLite: UPSERT](https://www.sqlite.org/lang_upsert.html): the `ON CONFLICT ... DO UPDATE` syntax in full.
- [SQLBolt](https://sqlbolt.com/): free interactive SQL lessons in the browser. Lessons 1–6 and 12 cover everything used here.
- [pytest: tmp_path](https://docs.pytest.org/en/stable/how-to/tmp_path.html): temporary folders for tests.

## Challenges (optional)

- Add a `/givexp` command that only server admins can use, with `@app_commands.default_permissions(administrator=True)`.
- Give out a role when someone reaches a level, with `await member.add_roles(role)`. The bot needs the **Manage Roles** permission, and its own role must be above the one it gives out.
- Keep XP separate for each server: add a `guild_id` column, and make the primary key `(guild_id, user_id)`.

## Next

Continue to [Module 06: Buttons and Polls](../06-buttons-and-polls/).
