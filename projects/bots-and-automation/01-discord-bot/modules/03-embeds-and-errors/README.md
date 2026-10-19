# Module 03: Embeds and Errors

**Goal:** errors shown only to the person who caused them, one error handler that keeps the bot alive whatever a command does, and a `/help` command that builds an embed from your loaded commands.

## Concepts

### Embeds

An **embed** is the card-style message with a coloured stripe, a title, fields and a footer. discord.js builds them with `EmbedBuilder`:

```ts
const embed = new EmbedBuilder()
  .setTitle("Rolled 3d6+2")
  .setColor(0x5865f2)                                // a hex colour
  .setDescription("**13** (4, 1, 6, +2)")            // Discord Markdown works here
  .addFields(
    { name: "Highest", value: "6", inline: true },
    { name: "Lowest", value: "1", inline: true },
  )
  .setFooter({ text: `Rolled by ${interaction.user.displayName}` })
  .setTimestamp();

await interaction.reply({ embeds: [embed] });
```

Embeds have limits: 256 characters for a title, 4096 for the description, 25 fields, and 6000 characters in total. A plain message is limited to 2000 characters. Long, user-controlled text (names, lists) needs cutting down to fit.

### Ephemeral replies

An **ephemeral** reply is visible only to the person who used the command, with a "Only you can see this" note. Use it for errors, and for anything personal or noisy:

```ts
await interaction.reply({ content: "That isn't dice.", flags: MessageFlags.Ephemeral });
```

(Older code writes `ephemeral: true`. discord.js now warns that's deprecated: use `flags`.)

### Throwing, catching, and `unknown`

`throw` stops a function and passes an error up to the nearest `try`/`catch` in the functions that called it. In `async` code, this works through `await`: if an awaited Promise rejects, `await` throws, and a `try` around it catches it. Without the `await`, the rejection skips your `try` entirely.

Anything can be thrown in JavaScript, not just `Error` objects (`throw "oops"` is legal). So in strict mode, the variable in `catch (error)` has the type **`unknown`**: TypeScript won't let you use it until you've checked what it is.

```ts
try {
  await something();
} catch (error) {
  const message = error instanceof Error ? error.message : String(error);
}
```

You can make your own error types by extending `Error`, and tell them apart with `instanceof`:

```ts
class UserError extends Error {}   // "this message is fine to show the user"

if (error instanceof UserError) { ... }
```

### One handler for every command

A bug in one command (a `null` you didn't expect, a Discord API error) should never take the whole bot down, and the user should always get *some* answer. The place to guarantee that is your `InteractionCreate` listener: wrap everything it does in `try`/`catch`, log the error for yourself, and tell the user something went wrong.

Two details make this tricky:

- If the command already replied (or deferred) before failing, a second `reply()` throws. Use `followUp()` then. `interaction.replied` and `interaction.deferred` tell you which case you're in.
- Telling the user can itself fail (the interaction might have expired). An error *inside* your `catch` is uncaught again. Catch that too.

### Slow commands: defer

Discord waits only **3 seconds** for an answer. A command that might take longer (calling a website, a big database query) should **defer** first, which shows "Bot is thinking..." and buys 15 minutes:

```ts
await interaction.deferReply();            // within 3 seconds
const result = await somethingSlow();
await interaction.editReply(result);       // replaces "thinking..."
```

## Practice

### Think it through

**1. Predict the output.**

```ts
async function fails(): Promise<void> {
  throw new Error("boom");
}

try {
  fails();
  console.log("after");
} catch {
  console.log("caught");
}
```

<details><summary>Answer</summary>

It prints `after`, and then Node crashes with an unhandled rejection: `Error: boom`. Calling an `async` function never throws: it returns a rejected Promise. Without `await`, nothing in the `try` throws, so `catch` never runs. With `await fails();`, it prints `caught`.

</details>

**2. Spot the problem.**

```ts
async execute(interaction) {
  await interaction.deferReply();
  const page = await fetchWeather();
  await interaction.reply(page);
},
```

<details><summary>Answer</summary>

After `deferReply()`, the interaction counts as answered, so `reply()` throws "The reply to this interaction has already been sent or deferred". Use `editReply(page)` to replace the "thinking..." message.

</details>

**3. Predict the output.**

```ts
class UserError extends Error {}
class CooldownError extends UserError {}

const error: unknown = new CooldownError("slow down");
console.log(error instanceof CooldownError, error instanceof UserError, error instanceof Error, error instanceof TypeError);
```

<details><summary>Answer</summary>

`true true true false`. An object is an `instanceof` its own class and every class above it. That's why one `if (error instanceof UserError)` in your handler can cover every kind of user-facing error you'll ever add.

</details>

### Try it in code

[`practice_03.ts`](practice_03.ts) has `toReply()`, a `CooldownError` class, `truncate()`, and a **FIX THE BUG** that runs fine but doesn't type-check. Copy it next to `check.ts` and run `node check.ts practice 3`.

<details><summary>Hint: toReply()</summary>

One `instanceof UserError` check covers it. Everything else gets the same generic message.

</details>

<details><summary>Hint: CooldownError</summary>

Declare the field in the class body (`readonly seconds: number;`), then in the constructor call `super(...)` with the finished message first, and set `this.name` and `this.seconds` after. `this` can't be used before `super()`. You can't write `constructor(readonly seconds: number)` here: that shortcut isn't plain JavaScript, and `erasableSyntaxOnly` forbids it.

</details>

<details><summary>Hint: truncate()</summary>

If the text already fits, return it unchanged. Otherwise keep `max - 3` characters, so there's room for the three dots. `text.slice(0, n)` keeps the first `n`.

</details>

<details><summary>Hint: FIX THE BUG</summary>

`error` is `unknown`. Check it's an `Error` before reading `.message`, and decide what to return when it isn't.

</details>

## Steps

### 1. Private errors from `/roll`

Change `/roll` so that when parsing fails, the error goes in an **ephemeral** reply. Successful rolls stay public, so everyone sees them.

### 2. A central error handler

Wrap the body of your `InteractionCreate` listener in `try`/`catch`. In the `catch`:

1. Log the error with `console.error`, so you can see what broke.
2. Tell the user, ephemerally, that something went wrong. If `interaction.replied || interaction.deferred`, use `followUp`; otherwise `reply`.
3. Make sure an error while telling the user can't escape (a `try`/`catch` inside the `catch`, or `.catch(...)` on the Promise).

`interaction` in the `catch` is the original `Interaction` type, which includes kinds of interaction you can't reply to. `interaction.isRepliable()` narrows it to ones you can.

Then test it: add `throw new Error("testing the handler");` at the top of one command's `execute`, restart, and run that command. You should get your "something went wrong" message, see the error in the terminal, and your other commands should still work. Remove the line afterwards.

The checker tests this by running `/roll` with its `dice` option missing. `getString("dice", true)` then throws, just like a bug would.

### 3. `/help`

Write a `/help` command that replies with an embed listing every command with its description. Don't type the list out: build it from `ctx.commands`, so a new command shows up in `/help` automatically. (The description is in `command.data.toJSON().description`.)

### 4. Your turn: an embed and a defer

- Turn one more reply into an embed: `/roll`'s results are a good candidate.
- Find (or invent) a command that could be slow, and make it `deferReply()` first. To feel the difference, `await sleep(5000)` (your Module 01 practice) before replying, with and without the defer.

## Make it yours

- Pick your bot's colour and use it in every embed. Keep the value in one place (`src/lib/style.ts`), so changing it later is one edit.
- Give `/help` some structure: group commands with fields, add a footer with your bot's version, or show the options each command takes (they're in `toJSON().options`).
- Write your error messages in your bot's voice. Make the generic one apologetic, and the user ones helpful.

## Check your work

```sh
node check.ts 3
```

The checker runs `/roll dice:banana` and expects one ephemeral reply. It runs `/roll` with the option missing and expects your handler to answer privately, with nothing escaping the listener. And it runs `/help` and checks the embed mentions every command in `src/commands/`.

## Stuck?

- **"escaped your interactionCreate listener"** from the checker: an error got past your `try`/`catch`. Usually a missing `await` before `command.execute(...)`, or a reply inside your `catch` that failed.
- **`Property 'replied' does not exist on type ...`**: in the `catch`, narrow `interaction` first, with `if (!interaction.isRepliable()) return;`.
- **`/help` misses commands**: build the text from `ctx.commands`, not a list you typed. If it's still missing one, is that command's file in `src/commands/`?
- **`Invalid Form Body ... embeds`**: a field `value` (or `name`) is empty, or something is over its length limit.
- **The error reply appears but the bot also crashes**: something after the `catch` (or in it) threw. Look at the stack trace in the terminal.

<details><summary>Hint 1: the handler's shape</summary>

```ts
client.on(Events.InteractionCreate, async (interaction) => {
  try {
    // everything that was in the listener before
  } catch (error) {
    console.error(error);
    // tell the user
  }
});
```

</details>

<details><summary>Hint 2: telling the user</summary>

```ts
if (!interaction.isRepliable()) return;
const message = { content: "Something went wrong.", flags: MessageFlags.Ephemeral } as const;
```

then `followUp(message)` or `reply(message)` depending on `interaction.replied || interaction.deferred`.

</details>

<details><summary>Hint 3: the last safety net</summary>

```ts
try {
  if (interaction.replied || interaction.deferred) await interaction.followUp(message);
  else await interaction.reply(message);
} catch (inner) {
  console.error("Couldn't tell the user either:", inner);
}
```

</details>

## Resources

- [discord.js Guide: Embeds](https://discordjs.guide/popular-topics/embeds.html): everything `EmbedBuilder` can do, with a picture of which part is which.
- [Discord's Markdown guide](https://support.discord.com/hc/en-us/articles/210298617): the formatting that works in messages and embed descriptions.
- [MDN: Error](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Error): including how to write custom error classes.

## Challenges (optional)

- Add a `UserError` class to your bot. Let commands `throw new UserError("...")` for problems the user can fix, and have the handler show that message instead of the generic one.
- Log errors with useful context: which command, which options, which user, and how long it ran.
- Make `/help command:roll` show the details of one command, with an autocomplete list of command names.

## Next

Continue to [Module 04: Tests and Structure](../04-tests-and-structure/).
