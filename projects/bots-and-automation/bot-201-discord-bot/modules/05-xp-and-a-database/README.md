# Module 05: XP and a Database

**Goal:** members earn XP by chatting, with a cooldown so spamming doesn't pay, stored in a SQLite database that survives restarts, with `/rank` and `/leaderboard` commands to show it off.

## Concepts

### Why a database?

Everything your bot knows lives in memory, and disappears when it restarts. To keep data, you need to store it somewhere. A JSON file works for small things, but it has problems as a bot grows: every change rewrites the whole file, a crash halfway through a write can corrupt it, and finding "the top 10 users" means loading everyone.

A **database** solves all three. **SQLite** is a database in a single file, with no server to run, and it's built into Node as `node:sqlite`. You talk to it in **SQL**, the language almost every database uses.

> On Node 22, the first use of `node:sqlite` prints `ExperimentalWarning: SQLite is an experimental feature`. It's harmless. Newer Node versions are quieter about it.

### SQL in five statements

Data lives in **tables**: rows with named columns, like a spreadsheet.

```sql
CREATE TABLE IF NOT EXISTS xp (
  user_id TEXT PRIMARY KEY,     -- one row per user; no duplicates allowed
  xp      INTEGER NOT NULL
);

INSERT INTO xp (user_id, xp) VALUES ('123', 10);          -- add a row
SELECT xp FROM xp WHERE user_id = '123';                   -- read
UPDATE xp SET xp = xp + 5 WHERE user_id = '123';           -- change
SELECT user_id, xp FROM xp ORDER BY xp DESC LIMIT 10;      -- the top 10
```

Discord ids are huge numbers, larger than JavaScript numbers can store exactly. discord.js gives them to you as strings. Store them as `TEXT`.

### `node:sqlite`

```ts
import { DatabaseSync } from "node:sqlite";

const db = new DatabaseSync("xp.db");     // opens the file, creating it if needed (":memory:" for a throwaway one)
db.exec("CREATE TABLE IF NOT EXISTS ...");  // run SQL that returns nothing

const add = db.prepare("INSERT INTO xp (user_id, xp) VALUES (?, ?)");
add.run("123", 10);                       // fills in the ?s, in order

const row = db.prepare("SELECT xp FROM xp WHERE user_id = ?").get("123");   // first row, or undefined
const rows = db.prepare("SELECT * FROM xp ORDER BY xp DESC").all();          // every row, as an array
```

`get()` and `all()` return rows as plain objects with one property per column. TypeScript can't know your columns, so cast: `as { xp: number } | undefined`. `DatabaseSync` is **synchronous**: no `await`, and nothing else runs while a query does. For a small bot's quick queries, that's simpler and plenty fast.

### `?`, never `${}`

Never build SQL by gluing text together:

```ts
db.prepare(`SELECT id FROM users WHERE name = '${name}'`)   // DON'T
```

If `name` is `O'Brien`, the quote ends the string early and the query breaks. Worse, a user could type `x' OR '1'='1` and change what the query does. That's **SQL injection**, one of the most common security holes there is. With `?` placeholders (a **prepared statement**), the database receives the value separately from the SQL, and treats it as data whatever it contains.

### UPSERT and transactions

Adding XP means "add to the row, or create it if it doesn't exist". One statement does both, an **UPSERT**, and `RETURNING` gives back the result:

```sql
INSERT INTO xp (user_id, xp) VALUES (?, ?)
ON CONFLICT (user_id) DO UPDATE SET xp = xp + excluded.xp
RETURNING xp;
```

(`excluded` means "the row you tried to insert".)

When several statements must all happen or not happen at all, like moving points from one user to another, wrap them in a **transaction**: `BEGIN`, the statements, then `COMMIT`. If anything goes wrong, `ROLLBACK` undoes everything since `BEGIN`.

### Listening to messages

Every message in a server triggers `Events.MessageCreate`, if the client asked for the **`GuildMessages`** intent. Your bot doesn't need to read what people write (that's the privileged `MessageContent` intent, which you leave off), just who sent it.

## Practice

### Think it through

**1. Spot the problem.** Each of these is called once per message. What goes wrong?

```ts
client.on(Events.MessageCreate, (message) => {
  store.addXp(message.author.id, 10);
});
```

<details><summary>Answer</summary>

Three things. Bots earn XP, including your own bot's messages. Anyone can farm XP by sending "a" fifty times a minute. And messages in DMs count too, if the bot can see them. Check `message.author.bot`, check `message.inGuild()`, and use a cooldown.

</details>

**2. Predict the output.** The table starts empty.

```ts
const add = db.prepare(
  "INSERT INTO xp (user_id, xp) VALUES (?, ?) ON CONFLICT (user_id) DO UPDATE SET xp = xp + excluded.xp RETURNING xp",
);
console.log(add.get("a", 5), add.get("a", 7), add.get("b", 1));
console.log(db.prepare("SELECT xp FROM xp WHERE user_id = ?").get("zzz"));
```

<details><summary>Answer</summary>

```
{ xp: 5 } { xp: 12 } { xp: 1 }
undefined
```

The first call inserts; the second hits the conflict on `user_id` and adds 7 to the existing 5. `RETURNING` makes the INSERT return a row, so you call `get()` rather than `run()`. A `SELECT` that matches nothing gives `undefined`, which is why the cast includes `| undefined`. (Node prints the rows with `[Object: null prototype]` in front; that doesn't matter.)

</details>

**3. Which is the better level curve, and why?**

```ts
const a = (xp: number) => Math.floor(xp / 100);
const b = (xp: number) => Math.floor(Math.sqrt(xp / 50));
```

<details><summary>Answer</summary>

It depends what you want, which is why it's your decision. With `a`, every level costs the same 100 XP, so active members reach level 100 and the numbers stop meaning much. With `b`, each level costs more than the last (level 10 needs 5,000 XP, level 20 needs 20,000), so early levels come quickly and high levels are rare. Most bots use a curve like `b`.

</details>

### Try it in code

[`practice_05.ts`](practice_05.ts) has notes (INSERT and SELECT), `addPoints()` (an UPSERT), `transferPoints()` (a transaction), and a **FIX THE BUG** with SQL injection in it. Copy it next to `check.ts` and run `node check.ts practice 5`.

<details><summary>Hint: addNote() and notesFor()</summary>

`run()` returns an object with `lastInsertRowid`, the id of the row just added. Convert it with `Number(...)`. For `notesFor`, `ORDER BY id` gives oldest first, then `.map()` the rows to their `text`.

</details>

<details><summary>Hint: addPoints()</summary>

It's the UPSERT from the concepts, with `points` instead of `xp`.

</details>

<details><summary>Hint: transferPoints()</summary>

`db.exec("BEGIN")`, then read the sender's points. If there aren't enough, `db.exec("ROLLBACK")` and return `false`. Otherwise subtract from one, add to the other (your `addPoints` handles a receiver with no row), and `db.exec("COMMIT")`. Wrap the middle in `try`/`catch` and `ROLLBACK` in the `catch`, so an error never leaves the transaction open.

</details>

<details><summary>Hint: FIX THE BUG</summary>

Replace `'${name}'` with `?`, and pass `name` to `get()`.

</details>

## Steps

### 1. The XP module

Create `src/lib/xp.ts`. The checker imports it, so use these names:

```ts
// Your level curve: which level a total amount of XP gives.
export function levelFor(xp: number): number;

export class XPStore {
  constructor(path: string);                        // open (or create) the database at path
  addXp(userId: string, amount: number): number;    // add XP, return the user's new total
  getXp(userId: string): number;                    // their XP, or 0 if they have none
  leaderboard(limit?: number): { userId: string; xp: number }[];  // most XP first
  close(): void;
}
```

- **`levelFor`** is your design. The rules: levels are whole numbers, 0 or more; more XP never gives a lower level; and enough XP gives a higher level than 0.
- The **constructor** creates its table with `CREATE TABLE IF NOT EXISTS`, so it works on a new file or an existing one.
- **`addXp`** is one UPSERT.
- **`leaderboard`** returns `limit` users (default 10), highest first, as `{ userId, xp }` objects, not raw rows: convert the column names.
- Data must survive closing the store and opening a new `XPStore` on the same file.

Remember: **only `?` placeholders**, never `${}` in SQL.

### 2. Cooldowns

Copy your `Cooldown` class from the Module 04 practice into `src/lib/cooldown.ts`, exported. The checker creates it as `new Cooldown(ms, now)` with a fake clock and calls `tryUse(key)`.

### 3. Earn XP by chatting

- Add `GatewayIntentBits.GuildMessages` to the client's intents.
- Add `xp: XPStore` to your `BotContext`, and create it in `createBot()`. Use a path from `.env` with a default: `new XPStore(process.env.XP_DB ?? "xp.db")`.
- Listen for `Events.MessageCreate`. Ignore messages from bots and outside servers. If the author's cooldown allows it, award some XP (a random 15–25 is common, but it's your call).

### 4. `/rank` and `/leaderboard`

- **`/rank`** shows a user's XP **and** level. Give it an optional user option, so people can look each other up, defaulting to whoever ran it.
- **`/leaderboard`** shows the top users. `userMention(id)` from discord.js turns an id into a mention. Inside an embed, mentions don't ping anyone.

Restart the bot, chat in your server, and try both.

### 5. Your turn: tests

Add tests for `levelFor`, `XPStore` and `Cooldown`, until you have **at least 8** passing in total. Use `new XPStore(":memory:")` for a fresh, throwaway database in each test. For the "survives a restart" test, use a real file in a temporary folder: `mkdtempSync(join(tmpdir(), "xp-"))` from `node:fs`, `node:os` and `node:path`.

## Make it yours

- Announce level-ups: when `addXp` pushes someone past a level, `message.channel.send(...)` a congratulation (in your bot's voice).
- Reward roles at certain levels (look up `member.roles.add`; your bot needs the Manage Roles permission, and its role must be above the one it gives).
- Make `/rank` an embed with the user's avatar (`user.displayAvatarURL()`) and a progress bar to the next level. You'll write a progress bar in the Module 06 practice.
- Choose what earns XP: only some channels? Bonus XP on weekends?

## Check your work

```sh
node check.ts 5
```

The checker tests `levelFor`, `XPStore` (on a temporary file, including closing and reopening it) and `Cooldown` (with a fake clock). Then it sends your `MessageCreate` listener pretend messages, from a person and from a bot, and compares their `/rank` replies with someone who never posted. Finally it runs your tests (at least 8 must pass). It runs your bot in a temporary folder, so it never touches your real `xp.db`.

## Stuck?

- **`ExperimentalWarning: SQLite is an experimental feature`**: harmless; see the concepts.
- **`SqliteError: no such table: xp`**: the constructor must create the table before anything uses it.
- **`SqliteError: UNIQUE constraint failed`**: a plain `INSERT` for a user who already has a row. Use the UPSERT.
- **`/rank` always shows 0**: the listener isn't running. Check the `GuildMessages` intent, and that you restarted the bot.
- **"A bot account sent messages and earned XP"** from the checker: check `message.author.bot` first.
- **`Conversion of type 'Record<string, SQLOutputValue>' to type ...`**: cast to your row type with `as`, including `| undefined` for `get()`.
- **XP disappears when the bot restarts**: are you using `":memory:"` in the bot? That's only for tests.

<details><summary>Hint 1: XPStore's shape</summary>

Keep the `DatabaseSync` in a `private readonly db` field. The constructor opens it and runs `CREATE TABLE IF NOT EXISTS xp (user_id TEXT PRIMARY KEY, xp INTEGER NOT NULL)`. Each method is one `prepare(...)` with `?`s, and a `run`, `get` or `all`.

</details>

<details><summary>Hint 2: getXp and leaderboard</summary>

```ts
const row = this.db.prepare("SELECT xp FROM xp WHERE user_id = ?").get(userId) as { xp: number } | undefined;
return row?.xp ?? 0;
```

For the leaderboard, `ORDER BY xp DESC LIMIT ?`, then `.map((row) => ({ userId: row.user_id, xp: row.xp }))`.

</details>

<details><summary>Hint 3: the listener</summary>

```ts
client.on(Events.MessageCreate, (message) => {
  if (message.author.bot || !message.inGuild()) return;
  if (!cooldown.tryUse(message.author.id)) return;
  ctx.xp.addXp(message.author.id, 15 + Math.floor(Math.random() * 11));
});
```

`cooldown` is a `new Cooldown(60_000)` made once in `createBot()`, not inside the listener.

</details>

## Resources

- [Node.js docs: SQLite](https://nodejs.org/api/sqlite.html): `DatabaseSync`, `prepare`, and what `run`, `get` and `all` return.
- [SQLBolt](https://sqlbolt.com/): short interactive SQL lessons in the browser. Lessons 1–6 and 13–15 cover everything here.
- [SQLite: UPSERT](https://sqlite.org/lang_upsert.html): the official description of `ON CONFLICT ... DO UPDATE`.
- [OWASP: SQL Injection](https://owasp.org/www-community/attacks/SQL_Injection): how injection attacks work, and why parameters stop them.

## Challenges (optional)

- Add a `/givexp` command for server admins only (`setDefaultMemberPermissions(PermissionFlagsBits.ManageGuild)`), using a transaction if it moves XP between users.
- Keep XP per server: add a `guild_id` column, and make the primary key `(guild_id, user_id)`.
- Add a `schema_version` table, and write a small migration that upgrades an old database to your new columns.

## Next

Continue to [Module 06: Buttons and Polls](../06-buttons-and-polls/).
