# Module 06: Buttons and Polls

**Goal:** a `/poll` command that posts a question with one button per option. Clicking a button votes (or changes your vote), and the message updates to show the counts.

## Concepts

### Buttons

Buttons are **message components**. They're sent with a message, in **action rows** (up to 5 rows, up to 5 buttons each):

```ts
const row = new ActionRowBuilder<ButtonBuilder>().addComponents(
  new ButtonBuilder().setCustomId("coin:heads").setLabel("Heads").setStyle(ButtonStyle.Primary),
  new ButtonBuilder().setCustomId("coin:tails").setLabel("Tails").setStyle(ButtonStyle.Secondary),
);

await interaction.reply({ content: "Call it!", components: [row] });
```

The `<ButtonBuilder>` after `ActionRowBuilder` is a **type argument**: it tells TypeScript this row holds buttons, so it can check what you add. (You've used generics before: `Promise<string>`, `Collection<string, Command>`.)

Styles are `Primary` (blurple), `Secondary` (grey), `Success` (green), `Danger` (red), and `Link`, which opens a URL instead of sending your bot anything.

### Clicks are interactions too

When someone clicks a button, Discord sends your bot an interaction, through the same `Events.InteractionCreate` listener as slash commands. `interaction.isButton()` narrows it to a `ButtonInteraction`, and `interaction.customId` says which button it was. Like any interaction, it must be answered within 3 seconds, once:

| Method | What it does |
| --- | --- |
| `interaction.update({...})` | edits the message the button is on (the usual answer) |
| `interaction.reply({...})` | sends a new message (make it ephemeral for "you can't do that") |
| `interaction.deferUpdate()` | "got it", with no visible change, if you'll edit the message later |

### Custom ids carry the state

A button's **custom id** is a string of up to 100 characters that comes back to you when it's clicked. It's the only thing that links a click to what it's about, so design it to carry what you need: which feature, which poll, which option.

```
poll:1300000000000000123:2
│    │                   └── option 2
│    └── which poll (the id of the /poll interaction that made it)
└── which command handles it
```

Your listener splits the id and passes the click to the command named before the first `:`. Each command handles its own buttons, the same way each command handles its own slash command.

### State that doesn't survive restarts

The votes live in a `Map` in memory, so restarting the bot forgets every poll. But the messages and their buttons are still there in Discord, and people can still click them. Your bot must answer those clicks politely ("This poll has ended"), never crash. (Saving polls in your database is a challenge at the end.)

discord.js also offers **collectors**, which listen for clicks on one message for a while. They're handy for quick things, but they die with the bot, and they're hard to test. Routing every click through your listener, by custom id, is what larger bots do, and what the self-check expects.

### One more name clash

discord.js already exports a class called `Poll`: Discord's own built-in polls. Your class is a different thing with the same name. In files that import from both, import yours under another name: `import { Poll as ButtonPoll } from "../lib/poll.ts"`.

## Practice

### Think it through

**1. Spot the problem.**

```ts
const id = `poll:${question}:${index}`;
new ButtonBuilder().setCustomId(id).setLabel(option).setStyle(ButtonStyle.Primary);
```

<details><summary>Answer</summary>

The question is user text. It can be longer than 100 characters (Discord rejects the button), it can contain `:` (which breaks your splitting), and two polls with the same question get the same ids. Use something short and unique, like the interaction's id, and keep the question in the `Poll` object.

</details>

**2. Predict what happens.** A poll was posted, then the bot restarted. Someone clicks a button. The handler is:

```ts
async handleButton(interaction, ctx) {
  const [, pollId, index] = interaction.customId.split(":");
  const poll = ctx.polls.get(pollId!)!;
  poll.vote(interaction.user.id, Number(index));
  await interaction.update({ embeds: [render(poll)] });
}
```

<details><summary>Answer</summary>

`ctx.polls.get(...)` returns `undefined` (the Map is empty after the restart), and the `!` told TypeScript to ignore that possibility. `poll.vote` throws `TypeError: Cannot read properties of undefined`. Your central error handler catches it and says "Something went wrong", which is better than a crash but not helpful. Check for the missing poll and reply ephemerally that it has ended. Every `!` is a promise that something can't be `undefined`. Here it could.

</details>

**3. Predict the output.**

```ts
const counts = [3, 7, 7, 1];
const most = Math.max(...counts);
console.log(most, counts.indexOf(most), counts.flatMap((n, i) => (n === most ? [i] : [])));
console.log(Math.max(...[]));
```

<details><summary>Answer</summary>

```
7 1 [ 1, 2 ]
-Infinity
```

`indexOf` only finds the first winner, so a tie needs `flatMap` (or a loop). And `Math.max` of nothing is `-Infinity`, an edge case to handle when nobody has voted.

</details>

### Try it in code

[`practice_06.ts`](practice_06.ts) has `encodeVote()`/`decodeVote()`, `progressBar()`, `tally()`, and a **FIX THE BUG** in `winners()`. Copy it next to `check.ts` and run `node check.ts practice 6`.

<details><summary>Hint: decodeVote()</summary>

A regular expression that matches the whole string checks everything at once: `/^vote:([^:]+):(\d+)$/`. `[^:]+` means "one or more characters that aren't a colon", and `\d+` only matches whole numbers 0 or more.

</details>

<details><summary>Hint: progressBar()</summary>

First clamp the fraction to 0..1 (and turn `NaN` into 0: `Number.isNaN`). Then `Math.round(fraction * width)` characters are `#`, and the rest `-`. `"#".repeat(n)` makes a run of characters.

</details>

<details><summary>Hint: tally()</summary>

Start with `new Array<number>(optionCount).fill(0)`, then loop over `votes.values()` and count each index that's in range.

</details>

<details><summary>Hint: FIX THE BUG</summary>

See question 3: find every index with the top count, and return `[]` when the top count is 0 (or there are no options).

</details>

## Steps

### 1. The `Poll` class

Create `src/lib/poll.ts`, exporting a class `Poll`. The checker uses it like this:

```ts
const poll = new Poll("Lunch?", ["pizza", "tacos", "sushi"]);
poll.vote("user-1", 0);     // user-1 votes for pizza
poll.vote("user-1", 2);     // ...then changes their mind: now sushi, and pizza loses the vote
poll.counts();              // [0, 0, 1]
poll.winners();             // [2] (every option tied for the most votes; [] if nobody has voted)
poll.vote("user-2", 3);     // throws: there's no option 3 (also for -1, 1.5, ...)
```

Keep `question` and `options` as public read-only fields, so the command can display them. Each user has at most one vote. `Map<string, number>`, from user id to option, makes that automatic.

Write tests for it in `tests/poll.test.ts` as you go: a fresh poll, voting, changing a vote, ties, no votes, and bad indexes.

### 2. Let commands handle buttons

Add an optional method to your `Command` interface, and the polls to your context:

```ts
export interface BotContext {
  commands: Collection<string, Command>;
  xp: XPStore;
  polls: Map<string, ButtonPoll>;   // poll id -> poll
}

export interface Command {
  data: { name: string; toJSON(): RESTPostAPIChatInputApplicationCommandsJSONBody };
  execute(interaction: ChatInputCommandInteraction, ctx: BotContext): Promise<void>;
  // Optional: answers clicks on buttons whose custom id starts with "<command name>:".
  handleButton?(interaction: ButtonInteraction, ctx: BotContext): Promise<void>;
}
```

Create the `Map` in `createBot()`.

### 3. Route clicks in your listener

Your listener currently returns early unless `interaction.isChatInputCommand()`. Restructure it to handle both kinds, still inside your `try`/`catch`:

- a slash command runs as before
- a button click: take the custom id up to the first `:`, find the command with that name, and call its `handleButton` if it has one. If nothing handles it, reply ephemerally that the button doesn't work any more.

### 4. `/poll`

Create `src/commands/poll.ts`, with two required string options: **`question`** and **`options`** (the choices, separated by commas).

- Split `options` on commas, trim each, and drop empty ones. Fewer than 2 or more than 5: refuse, ephemerally.
- Create a `Poll`, and store it in `ctx.polls` under `interaction.id`.
- Reply with the question and the current counts (an embed works well), and **one button per option**, labelled with the option, each with a custom id like `poll:<poll id>:<index>`.

Then give the command a `handleButton` that decodes the custom id (your `decodeVote` practice is close), finds the poll, records the vote, and answers with `interaction.update(...)`, showing the new counts. A missing poll gets an ephemeral "This poll has ended".

Deploy, restart, and run a poll. Vote from two accounts if you can (ask a friend), and change your vote.

### 5. Your turn: polls that close

Add an optional `minutes` option (1 to 1440, say). Once a poll's time is up:

- clicking a button tells the user, ephemerally, that it's closed, and doesn't count the vote
- bonus: the next update shows the winner and disables the buttons (`.setDisabled(true)`)

Store the closing time in the `Poll`, and pass the current time in, rather than calling `Date.now()` inside the class. Then you can test closing without waiting. Make both **optional** parameters (for example `new Poll(question, options, closesAt?)` and `vote(userId, index, now = Date.now())`), so that `new Poll(question, options)` still makes a poll that never closes: the checker creates polls that way.

## Make it yours

- Show results with your `progressBar` from the practice, and percentages.
- Emoji on buttons (`.setEmoji("🍕")`), and a different colour for the winning option.
- Anonymous polls, or polls that show who voted for what. Which suits your server?
- Use buttons elsewhere: a `/rps` rock-paper-scissors challenge, a "roll again" button under `/roll`, a confirm/cancel step for anything destructive.

## Check your work

```sh
node check.ts 6
```

The checker tests your `Poll` class directly. It runs `/poll` and checks there's one button per option, each with a short, unique custom id, labelled with its option. It tries 1 option and 6 options and expects ephemeral refusals. Then it clicks two different buttons as two different users and expects an answer each time, with the poll message changing between them. Last, it clicks a button from a poll your bot has never seen, which must not crash it.

## Stuck?

- **"This interaction failed"** after clicking: your bot didn't answer within 3 seconds. Is the click reaching `handleButton`? Log `interaction.customId` in your listener.
- **`Invalid Form Body ... custom_id`**: a custom id is over 100 characters, or two buttons share one.
- **`Type 'Poll' is missing the following properties ... channel, channelId`**: you've mixed up your `Poll` with discord.js's. Import yours under another name.
- **The counts don't change**: are you calling `update` with the *new* counts? And is each click's poll id the same one you stored?
- **Votes vanish when the bot restarts**: expected, with a `Map`. See the challenges.
- **`Cannot invoke an object which is possibly 'undefined'`** when calling `command.handleButton`: it's optional. Check it exists first, or use `command.handleButton?.(...)`.

<details><summary>Hint 1: building the buttons</summary>

`options.map((option, index) => new ButtonBuilder()...)` gives an array of buttons. `addComponents` takes an array, and 5 options fit in one row.

</details>

<details><summary>Hint 2: routing in the listener</summary>

```ts
if (interaction.isChatInputCommand()) {
  // as before
} else if (interaction.isButton()) {
  const name = interaction.customId.split(":")[0] ?? "";
  const command = ctx.commands.get(name);
  if (command?.handleButton) await command.handleButton(interaction, ctx);
  else await interaction.reply({ content: "That button doesn't work any more.", flags: MessageFlags.Ephemeral });
}
```

</details>

<details><summary>Hint 3: handleButton</summary>

```ts
async handleButton(interaction, ctx) {
  const [, pollId = "", index = ""] = interaction.customId.split(":");
  const poll = ctx.polls.get(pollId);
  if (!poll) {
    await interaction.reply({ content: "This poll has ended.", flags: MessageFlags.Ephemeral });
    return;
  }
  poll.vote(interaction.user.id, Number(index));
  await interaction.update({ embeds: [render(poll)] });
},
```

`render(poll)` is a function you write once and use both when creating the poll and on every vote.

</details>

## Resources

- [discord.js Guide: Buttons](https://discordjs.guide/interactive-components/buttons.html): building buttons and responding to clicks.
- [Discord docs: Message components](https://discord.com/developers/docs/components/overview): the limits on rows, buttons, labels and custom ids.
- [TypeScript Handbook: Generics](https://www.typescriptlang.org/docs/handbook/2/generics.html): what `ActionRowBuilder<ButtonBuilder>` and `Map<string, number>` mean.

## Challenges (optional)

- Save polls in your database, so they survive restarts. Store the poll and its votes in two tables, and load a poll when one of its buttons is clicked.
- A `/poll` with a select menu instead of buttons, allowing up to 25 options, or several choices per person.
- Close polls on a timer: when a poll's time is up, edit the message to show the result even if nobody clicks. (Think about what happens if the bot restarts while waiting.)

## You built a Discord bot

Your bot loads commands from files, reads options, keeps a database, handles buttons, and stays up when one of its commands fails. It's type-checked from top to bottom and has tests. That's the same structure real bots with thousands of servers use.

To keep going, see [Going further](../../#going-further) in the project README: hosting your bot so it runs all the time, calling web APIs, scheduled tasks and more.
