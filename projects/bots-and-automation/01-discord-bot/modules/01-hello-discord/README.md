# Module 01: Hello, Discord

**Goal:** a bot with at least two slash commands, each in its own file, loaded by a command handler and registered with Discord by a deploy script.

## Concepts

### Promises and `async`/`await`

Almost everything a bot does takes time: sending a message, reading a file, asking Discord for something. JavaScript doesn't stop and wait for these. Instead, a function that takes time returns a **Promise**: an object standing for a result that will arrive later. A Promise ends up either **resolved** (with a value) or **rejected** (with an error).

`await` pauses an `async` function until a Promise settles, then gives you its value (or throws its error):

```ts
async function greet(interaction: ChatInputCommandInteraction): Promise<void> {
  await interaction.reply("Hi!");   // wait until Discord has the message
  console.log("Sent!");             // runs after the reply has gone
}
```

Three rules cover most of what goes wrong:

1. **An `async` function always returns a Promise.** If it returns a `string`, its return type is `Promise<string>`, and callers need `await` to get the string.
2. **Forgetting `await` doesn't stop the code; it just doesn't wait.** You get the Promise instead of the value, and if it rejects, nobody catches the error. TypeScript often notices (a `Promise<string>` has no `.length`), but not always.
3. **While a function is paused at `await`, other code runs.** That's how one bot answers many people at once: while it waits on Discord for one person, it handles the next.

To run several things at the same time, start them all and then wait for all of them: `await Promise.all([a(), b(), c()])`.

### Events

A Discord bot spends its life waiting. When something happens (someone uses a command, sends a message, joins the server), discord.js **emits an event**, and calls the functions you registered for it:

```ts
client.on(Events.InteractionCreate, async (interaction) => {
  // runs every time someone uses a slash command, clicks a button, ...
});
```

`client.once` is the same, but runs only the first time (like `ClientReady` in Module 00). The functions you pass are **listeners**.

### Slash commands, and registering them

A slash command has two halves that live in different places:

- **The definition** (name, description, options) is stored by **Discord**, so the app can show it when someone types `/`. You upload definitions with a **deploy script**, and only need to re-run it when a definition changes.
- **The code** that answers it runs in **your bot**. When someone uses `/ping`, Discord sends your bot an *interaction*, and your `InteractionCreate` listener answers it.

Commands can be registered **for one server** (a guild command: it updates instantly, good while developing) or **globally** (every server the bot is in). Registration is rate-limited (about 200 new commands per day per server), so register from the deploy script, never every time the bot starts.

Every interaction must be answered **within 3 seconds**, and **only once**. Otherwise Discord shows "The application did not respond". (Module 03 covers slow commands.)

### The command handler pattern

Putting every command in one big `if` grows messy fast. Real bots give each command its own file in `src/commands/`, all with the same shape: a `data` part (the definition) and an `execute` function (the code). A **loader** reads the folder and imports them all, and the `InteractionCreate` listener looks up the right one by name. Adding a command then means adding a file, nothing else.

TypeScript makes "the same shape" checkable with an **interface**:

```ts
export interface Command {
  data: { name: string; toJSON(): RESTPostAPIChatInputApplicationCommandsJSONBody };
  execute(interaction: ChatInputCommandInteraction, ctx: BotContext): Promise<void>;
}
```

`ctx` (the **context**) is everything a command might need from the rest of the bot, passed in rather than imported, starting with the list of commands. You'll add to it in later modules.

A command file then says it `satisfies Command`:

```ts
export default {
  data: new SlashCommandBuilder().setName("ping").setDescription("Check that I'm awake"),
  async execute(interaction) { ... },
} satisfies Command;
```

`satisfies` checks the object against the interface (a missing `execute`, or a typo in its name, is an error) and gives `interaction` its type, without you writing it out.

## Practice

### Think it through

**1. Predict the output.**

```ts
async function slow(): Promise<string> {
  console.log("B");
  return "C";
}

console.log("A");
const promise = slow();
console.log(promise instanceof Promise);
console.log(await promise);
console.log("D");
```

<details><summary>Answer</summary>

```
A
B
true
C
D
```

Calling `slow()` runs its body straight away, up to its first `await` (it has none), so `B` prints before anything else after `A`. But an `async` function always hands back a Promise, even when it returns a plain string, so `promise` is a Promise, not `"C"`. `await promise` unwraps it.

</details>

**2. Spot the problem.** This command sometimes crashes the bot with an "unhandled promise rejection", and the stack trace never mentions `execute`'s caller. Why?

```ts
async execute(interaction) {
  const reply = buildReply(interaction);   // buildReply is async
  interaction.reply(reply);
},
```

<details><summary>Answer</summary>

Both calls are missing `await`. Without it, `buildReply()` hands back a Promise, and `interaction.reply()` is given a Promise instead of a message (TypeScript would catch this one). Then `interaction.reply()` itself runs without anyone waiting for it: if Discord rejects the reply, the error isn't thrown inside `execute`, so no `try`/`catch` around it can catch it. The rejected Promise floats away and Node reports it as unhandled.

</details>

**3. Predict the output.** About how long does this take?

```ts
const wait = (ms: number) => new Promise((done) => setTimeout(done, ms));

const start = Date.now();
await Promise.all([wait(300), wait(200), wait(100)]);
console.log(Date.now() - start);
```

<details><summary>Answer</summary>

About **300 ms**, not 600. All three timers start at once, and `Promise.all` waits for the slowest. Writing `await wait(300); await wait(200); await wait(100);` would take 600 ms.

</details>

### Try it in code

[`practice_01.ts`](practice_01.ts) has four problems: `sleep()`, `withTimeout()`, `fetchAll()`, and a **FIX THE BUG**. Copy it into your bot's folder (next to `check.ts`), replace each `throw new Error("TODO")` with your code, and run:

```sh
node check.ts practice 1
```

The checker type-checks the file too, so a TypeScript error counts as "not yet".

<details><summary>Hint: sleep()</summary>

`new Promise((resolve) => ...)` makes a Promise you resolve yourself, by calling `resolve()`. `setTimeout(fn, ms)` calls `fn` after `ms` milliseconds. Put the two together.

</details>

<details><summary>Hint: withTimeout()</summary>

Make a new Promise. Inside it, start a timer that calls `reject(new Error(...))`, and also attach `.then(onValue, onError)` to the original promise to `resolve` or `reject` with its result. Whichever happens first wins: a Promise ignores everything after it has settled. Clear the timer when the original promise settles (`clearTimeout`), or it keeps your program running.

There's a shortcut too: look up `Promise.race`.

</details>

<details><summary>Hint: fetchAll()</summary>

`ids.map(fetchOne)` starts every fetch at once and gives you an array of Promises. Which function turns an array of Promises into a Promise of an array, in the same order?

</details>

<details><summary>Hint: FIX THE BUG</summary>

Read TypeScript's message carefully: what type does it say `text` has? What's missing in front of `fetchText(url)`?

</details>

## Steps

Keep working in `my-bot` from Module 00.

### 1. The `Command` type

Create `src/types.ts`. Command data comes from discord.js's `SlashCommandBuilder`, but the builder's exact type changes as you add options, so the interface only asks for the two things the handler uses: a `name`, and `toJSON()`, which turns it into what Discord's API expects.

```ts
import type {
  ChatInputCommandInteraction,
  Collection,
  RESTPostAPIChatInputApplicationCommandsJSONBody,
} from "discord.js";

// Everything a command can use from the rest of the bot.
export interface BotContext {
  commands: Collection<string, Command>;
}

// The shape every file in src/commands/ exports.
export interface Command {
  data: { name: string; toJSON(): RESTPostAPIChatInputApplicationCommandsJSONBody };
  execute(interaction: ChatInputCommandInteraction, ctx: BotContext): Promise<void>;
}
```

A `Collection` is discord.js's `Map` with extras like `.map()` and `.find()`. It maps each command's name to the command.

### 2. Your first command

Create `src/commands/ping.ts`:

```ts
import { SlashCommandBuilder } from "discord.js";
import type { Command } from "../types.ts";

export default {
  data: new SlashCommandBuilder()
    .setName("ping")                         // lowercase, no spaces, up to 32 characters
    .setDescription("Check that I'm awake"),  // up to 100 characters
  async execute(interaction) {
    // How long since the user pressed Enter, in milliseconds.
    const delay = Date.now() - interaction.createdTimestamp;
    await interaction.reply(`Pong! (${delay} ms)`);
  },
} satisfies Command;
```

Every command file must export its command as `default`, and nothing in `src/commands/` may be anything other than a command. (Helper code goes in `src/lib/`, from Module 02.)

### 3. The loader

Create `src/load-commands.ts`, exporting `loadCommands(): Promise<Collection<string, Command>>`. It should:

1. List the files in `src/commands/` with `readdir` from `node:fs/promises`.
2. For each file ending in `.ts`, import it with `await import(...)`.
3. Add its `default` export to a new `Collection`, keyed by `command.data.name`.

The tricky part is finding the folder. A relative path like `"./commands"` is relative to wherever you *ran* Node from, not to this file. Build paths from `import.meta.url`, the URL of the current file, instead:

```ts
const folder = new URL("./commands/", import.meta.url);   // always next to this file
const files = await readdir(folder);
// ...and for each file:
const mod = (await import(new URL(file, folder).href)) as { default: Command };
```

`import()` returns `Promise<any>` because TypeScript can't know what's in a file chosen at runtime. The `as { default: Command }` tells it what to expect. (That's a promise *you* make: if a file exports something else, TypeScript can't catch it, but the self-check will.)

### 4. Answer interactions

In `createBot()` in `src/bot.ts`, load the commands and listen for interactions. Here's the shape, with the middle for you to fill in:

```ts
const ctx: BotContext = { commands: await loadCommands() };

client.on(Events.InteractionCreate, async (interaction) => {
  // Interactions include button clicks and more. We only want slash commands.
  if (!interaction.isChatInputCommand()) return;

  // Your code here: find the command by interaction.commandName,
  // and run its execute() with the interaction and ctx.
});
```

After the `if`, hover over `interaction` in VS Code. Its type changed from `Interaction` to `ChatInputCommandInteraction`: `isChatInputCommand()` is a **type guard**, and TypeScript **narrows** the type once it has been checked.

`commands.get(name)` returns `Command | undefined`, and strict mode won't let you call `execute` on something that might be `undefined`. Handle the missing case: if Discord sends a command the bot doesn't have (one you deleted, but didn't re-deploy), reply with a short message instead of crashing.

### 5. The deploy script

Create `src/deploy-commands.ts`. Registering uses Discord's REST API directly, through discord.js's `REST` class:

```ts
import { REST, Routes } from "discord.js";
import { loadCommands } from "./load-commands.ts";

const { DISCORD_TOKEN, CLIENT_ID, GUILD_ID } = process.env;
if (!DISCORD_TOKEN || !CLIENT_ID || !GUILD_ID) {
  throw new Error("Set DISCORD_TOKEN, CLIENT_ID and GUILD_ID in .env");
}

const commands = await loadCommands();
const body = commands.map((command) => command.data.toJSON());

// PUT replaces the server's whole list of commands with this one.
const rest = new REST().setToken(DISCORD_TOKEN);
await rest.put(Routes.applicationGuildCommands(CLIENT_ID, GUILD_ID), { body });
console.log(`Registered ${body.length} commands.`);
```

After the `if`, the three variables are `string`, not `string | undefined`: TypeScript narrowed them, because the code only gets past the `if` when they're all set.

### 6. Try it in Discord

```sh
npm run deploy
npm start
```

In your server, type `/`. Your bot's commands appear in the list. Run `/ping`.

Re-run `npm run deploy` whenever you add a command or change its name, description or options. Changing only `execute` just needs a restart of the bot (Ctrl+C, `npm start`).

### 7. Your turn: a second command

Add at least one more command of your own, in its own file. Some ideas: `/hello` that greets the user by name (`interaction.user.displayName`), `/coin` that flips a coin, `/about` that describes your bot. Deploy, restart and try it.

## Make it yours

- Decide your bot's personality now, and write every reply in its voice: polite butler, grumpy robot, overexcited puppy.
- Give it an avatar and a description in the Developer Portal (General Information).
- Add a few more simple commands: an inside joke for your friends, a random fact, a fortune.

## Check your work

```sh
node check.ts 1
```

The checker loads every file in `src/commands/`, checks each has a name and description, then sends each command to your `InteractionCreate` listener as a pretend interaction and checks it replies exactly once. It also makes sure an unknown command doesn't crash the bot. Make sure `npx tsc` is clean first: the checker runs it too.

## Stuck?

- **The command doesn't show up when you type `/`**: run `npm run deploy` again, and check `GUILD_ID` is your test server's id. Discord's app sometimes needs a restart (or Ctrl+R) to refresh the list.
- **"The application did not respond"**: your bot isn't running, the command threw an error before replying, or `execute` never called `interaction.reply()`. Look in the terminal running the bot for an error.
- **`Unknown interaction` (error 10062)**: you replied more than 3 seconds after the command, or the bot was restarted halfway through.
- **`The reply to this interaction has already been sent or deferred`**: you called `reply()` twice. One interaction, one reply.
- **`'command' is possibly 'undefined'`**: `commands.get()` might not find the name. Check for `undefined` first.
- **`Invalid Form Body ... name`** from the deploy script: command names must be lowercase, with no spaces or capitals, like `my-command`.
- **`should export a command`** from the checker: every file in `src/commands/` must `export default` an object with `data` and `execute`.

<details><summary>Hint 1: the loader</summary>

Start with an empty `const commands = new Collection<string, Command>();`, loop over the file names with `for (const file of files)`, skip names that don't end with `.ts`, import each one, and `commands.set(...)` it. Return `commands` at the end.

</details>

<details><summary>Hint 2: the listener</summary>

`const command = ctx.commands.get(interaction.commandName);` then an `if (!command)` that replies and `return`s. After that `if`, TypeScript knows `command` is a `Command`.

</details>

<details><summary>Hint 3: the listener, almost complete</summary>

```ts
const command = ctx.commands.get(interaction.commandName);
if (!command) {
  await interaction.reply("I don't know that command any more.");
  return;
}
await command.execute(interaction, ctx);
```

Don't forget the `await` before `command.execute`: Module 03 relies on it.

</details>

## Resources

- [discord.js Guide](https://discordjs.guide/): the official guide. Its "Creating your app" section uses the same command-handler idea in JavaScript; compare it with your TypeScript version.
- [javascript.info: Promises, async/await](https://javascript.info/async): the clearest explanation of Promises on the web. Read "Introduction: callbacks" through "Async/await".
- [TypeScript Handbook: Narrowing](https://www.typescriptlang.org/docs/handbook/2/narrowing.html): how `if` checks change a variable's type. You'll use this in every module.

## Challenges (optional)

- Make the loader report a clear error if a command file is missing `data` or `execute`, or two files use the same name.
- Add `npm run deploy -- --global` support, registering with `Routes.applicationCommands(CLIENT_ID)` when the flag is given.
- Log every command used, with the user and how long it took to run.

## Next

Continue to [Module 02: Options and Dice](../02-options-and-dice/).
