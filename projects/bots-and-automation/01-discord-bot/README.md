# Discord Bot

> Build your own Discord bot in TypeScript: slash commands, dice, embeds, an XP system backed by a real database, and polls with buttons, all tested and type-checked.

**Difficulty:** Intermediate
**Language:** TypeScript, run directly by Node.js. TypeScript is the most common language for Discord bots, and its type checker catches whole kinds of bug (a missing `await`, a value that might be `null`, a typo in a property name) before your bot ever runs. Everything you learn here carries straight over to web development.
**Estimated time:** 10–15 hours across all modules, plus about an hour of setup.

## What you'll build

A bot that lives in your own Discord server and answers slash commands. Here's one example of a finished bot (yours will have its own name, personality and commands):

```
/roll dice:3d6+2
  Bolt: Rolled [4, 1, 6] + 2 = 13

/rank
  Bolt: Sam is level 3 with 512 XP.

/poll question:Lunch? options:pizza, tacos, sushi
  Bolt: Lunch?            [ pizza ] [ tacos ] [ sushi ]
        pizza: 2
        tacos: 1
        sushi: 0
```

Under the hood you'll write the same structure real bots use: a command handler that loads each command from its own file, a central error handler so one bug never takes the bot down, plain TypeScript modules for the logic (so you can test them), and a SQLite database for anything that has to survive a restart.

## What you'll learn

- TypeScript in strict mode: types, interfaces, generics, discriminated unions and narrowing
- Asynchronous code: Promises, `async`/`await`, and running things at the same time
- Events and the discord.js library: slash commands, options, embeds, ephemeral replies, buttons
- Structuring a project so the logic can be tested, with dependency injection
- Writing unit tests with Node's built-in test runner
- SQL with SQLite: schemas, prepared statements, UPSERT and transactions
- Keeping secrets (your bot token) out of your code

## Prerequisites

- You're comfortable programming in at least one language: variables, functions, loops, arrays/lists and objects/dictionaries. If you've finished the [Text Adventure](../../games/01-text-adventure/), you're ready.
- You don't need to know JavaScript or TypeScript already. The lessons explain the TypeScript you need, but they move quickly. If the syntax feels strange, keep [javascript.info](https://javascript.info/) open: its first part covers the JavaScript that TypeScript is built on.
- A Discord account. You'll make a private server to test your bot in, so you won't bother anyone.
- Installing Node.js and the tools is covered in [Module 00](modules/00-setup/).

## Make it yours

Your bot has its own name, avatar, personality and wording. Beyond the commands each module asks for, you choose what else it does: games, utilities, inside jokes for your friends. Each module's **Make it yours** section has ideas.

The self-check doesn't read your wording. It loads your bot, sends it pretend slash commands, button clicks and messages, and looks at what comes back: did it reply, was the error private, does the reply contain the total? Where it needs a specific name (like a `/roll` command, or a `parseDice()` function), the module says so.

## How to work through this project

1. Start with [Module 00: Setup](modules/00-setup/).
2. Work through the modules **in order**. Each one adds to the bot you built in the last.
3. Each lesson starts with concepts and **Practice** problems. Do the practice first: it's where you try the new idea on its own, before you use it in the bot.
4. Build the module's part of the bot, then run the self-check with the module's number:
   ```sh
   node check.ts 3
   ```
   It checks that module and every one before it, so you'll know if something broke.
5. Stuck? Each module has a **Stuck?** section with the usual mistakes, and hints you click to reveal. There are no solutions to copy: the hints get you there.

## Modules

| # | Module | What you'll do |
| --- | --- | --- |
| 00 | [Setup](modules/00-setup/) | Install Node, create the bot in Discord's Developer Portal, keep the token safe, and log in |
| 01 | [Hello, Discord](modules/01-hello-discord/) | Promises and events; a command handler with a typed `Command` interface; your first slash commands |
| 02 | [Options and Dice](modules/02-options-and-dice/) | Command options, a dice parser that returns results instead of throwing, `/roll` |
| 03 | [Embeds and Errors](modules/03-embeds-and-errors/) | Embeds, ephemeral replies, a central error handler, and `/help` |
| 04 | [Tests and Structure](modules/04-tests-and-structure/) | Unit tests with `node --test`, dependency injection, and testing commands with fakes |
| 05 | [XP and a Database](modules/05-xp-and-a-database/) | SQLite with `node:sqlite`, an XP system with levels and cooldowns, `/rank` and `/leaderboard` |
| 06 | [Buttons and Polls](modules/06-buttons-and-polls/) | Buttons, routing clicks by custom id, and `/poll` |

## Going further

When you've finished all the modules:

- **Host it** so it runs when your laptop is off: a small cloud server (a VPS), a Raspberry Pi at home, or a hosting platform's free tier. Keep it running with a process manager like `systemd` or `pm2`, and give it its token through the host's environment variables (never commit `.env`).
- **Call web APIs** with `fetch()`: weather, jokes, game stats. Think about rate limits, timeouts (your `withTimeout()` from Module 01) and caching.
- **Scheduled tasks:** daily reminders or a "question of the day" with `setInterval`, or a scheduler library.
- **Database migrations:** when you change a table, existing bots have old tables. Keep a `schema_version` and upgrade step by step.
- **Sharding:** past about 2,500 servers, Discord requires a bot to split into several connections. Read discord.js's guide on sharding to see how big bots are built.
- **More components:** select menus, modals (pop-up forms) and context-menu commands (right-click a user or message).
