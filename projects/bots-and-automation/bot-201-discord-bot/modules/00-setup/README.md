# Module 00: Setup

**Goal:** Node.js installed, a bot account in Discord's Developer Portal, the bot invited to a private test server, and a TypeScript project of your own that logs the bot in.

This takes about an hour the first time, mostly clicking through Discord's pages. Already done another Node project in the vault? Skim steps 1–3.

## 1. Install Node.js

Follow [Installing Node.js](../../../../../guides/installing-node.md), then check the version in a new terminal:

```sh
node --version
```

You need **v22.18 or newer** (v24 LTS is best). From 22.18 on, Node can run TypeScript files directly, so there's no build step in this project.

New to the terminal? Read [Terminal basics](../../../../../guides/terminal-basics.md) first.

## 2. Install a code editor

Follow [Setting up VS Code](../../../../../guides/vs-code.md). VS Code understands TypeScript out of the box: it underlines type errors as you type, and hovering over anything shows its type. You don't need extra extensions for this project.

## 3. Get the vault

You need the vault for this project's `check.ts` and the practice files.

- **With Git:** `git clone https://github.com/technogodCEO/MontyDevs_Vault.git` in the folder where you keep projects. (`git pull` in that folder gets updates later. See [Git and GitHub basics](../../../../../guides/git-and-github.md).)
- **Without Git:** on the vault's GitHub page, click **Code → Download ZIP** and unzip it.

## 4. Make a test server

Bots live in servers. Make your own, so you can test without bothering anyone:

1. In Discord, click the **+** at the bottom of your server list, then **Create My Own → For me and my friends**. Call it something like "Bot Lab".
2. Turn on Developer Mode, which lets you copy ids: **User Settings → Advanced → Developer Mode**.
3. Right-click your new server's icon and choose **Copy Server ID**. Paste it into a text file for now. This is your **guild id** ("guild" is what Discord's API calls a server).

## 5. Create the bot in the Developer Portal

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications) and sign in.
2. Click **New Application**, give it your bot's name, agree to the terms and click **Create**.
3. On the **General Information** page, copy the **Application ID** into your text file. This is your **client id**. You can also set the bot's avatar and description here.
4. In the menu on the left, open **Bot**. Click **Reset Token**, confirm, and copy the token into your text file.

   > **Your token is your bot's password.** Anyone who has it can control your bot, and people run scripts that search GitHub for leaked tokens within minutes. Never paste it into code, a chat or a screenshot. If it ever leaks, come back here and click **Reset Token**: the old one stops working at once.

5. Still on the **Bot** page, leave the three **Privileged Gateway Intents** switched off. This bot doesn't need them.
6. Open **OAuth2** in the menu, and find the **OAuth2 URL Generator**. Tick the scopes **`bot`** and **`applications.commands`**. Under **Bot Permissions** that appears below, tick **View Channels**, **Send Messages** and **Embed Links**.
7. Copy the **Generated URL** at the bottom, open it in your browser, choose your test server, and click **Authorize**.

Your bot now appears in the server's member list, offline. Next you'll write the code that brings it online.

## 6. Make your project folder

Make a folder for **your** bot, **outside** the vault, for example `my-bot` next to `MontyDevs_Vault`:

```
Code/
├── MontyDevs_Vault/        # the tutorials (don't put your code in here)
└── my-bot/                 # your bot
```

Open `my-bot` in VS Code (*File → Open Folder...*) and open its terminal (*Terminal → New Terminal*). Then create the project and install what it needs:

```sh
npm init -y
npm install discord.js
npm install --save-dev typescript @types/node
```

- `npm init -y` makes `package.json`.
- **discord.js** is the library that talks to Discord.
- **typescript** gives you `tsc`, the type checker. **@types/node** describes Node's built-in modules to it.

Now open `package.json` and make two changes: add `"type": "module"` (so Node treats your files as modern ES modules with `import`/`export`), and replace the `"scripts"` section. The top of the file should look like this (keep the versions npm put in `dependencies`):

```json
{
  "name": "my-bot",
  "version": "1.0.0",
  "private": true,
  "type": "module",
  "scripts": {
    "start": "node --env-file=.env src/index.ts",
    "deploy": "node --env-file=.env src/deploy-commands.ts",
    "typecheck": "tsc",
    "test": "node --test"
  },
```

`npm start` will run your bot. `--env-file=.env` tells Node to read your secrets from a file called `.env` (step 8) into `process.env`.

## 7. Configure TypeScript

Create `tsconfig.json` in `my-bot`:

```json
{
  "compilerOptions": {
    "target": "es2022",
    "module": "nodenext",
    "moduleResolution": "nodenext",
    "strict": true,
    "noEmit": true,
    "allowImportingTsExtensions": true,
    "erasableSyntaxOnly": true,
    "verbatimModuleSyntax": true,
    "skipLibCheck": true,
    "types": ["node"]
  },
  "include": ["src", "tests"]
}
```

What the important ones do:

- **`strict`** turns on every safety check. In particular, a value that might be `null` or `undefined` can't be used until you've checked it. This catches more bugs than anything else in TypeScript, and the self-check requires it.
- **`noEmit`**: `tsc` only *checks* your code. Node runs the `.ts` files itself, by deleting the types as it loads them ("type stripping").
- **`erasableSyntaxOnly`**: because Node just deletes the types, your code can't use the few TypeScript features that aren't plain types (`enum`, `namespace`, and constructor parameters like `constructor(private x: number)`). This setting makes `tsc` reject them, instead of Node failing later.
- **`allowImportingTsExtensions`**: you import your own files with their real name, `./bot.ts`, which is what Node needs.
- **`verbatimModuleSyntax`**: imports that are only types must say so: `import type { Client } from "discord.js"`. Node then knows it can delete them.

## 8. Keep secrets out of your code

Create a file called `.env` in `my-bot` with the three values from your text file (no quotes, no spaces around `=`):

```
DISCORD_TOKEN=paste-your-token-here
CLIENT_ID=paste-your-application-id-here
GUILD_ID=paste-your-server-id-here
```

Then create `.gitignore`, which lists files Git must never save:

```
node_modules/
.env
*.db
```

If you ever put this project on GitHub, `.env` stays on your computer. (`node_modules` is ignored because `npm install` recreates it; `*.db` will be your database in Module 05.) You can delete the text file with your token in it now.

## 9. Write the bot

Create a folder `src` with two files. First, `src/bot.ts`, which **builds** the bot:

```ts
import { Client, Events, GatewayIntentBits } from "discord.js";

// Builds the bot and sets up what it does, without connecting to Discord.
// Keeping this separate from logging in means tests (and check.ts) can
// create the bot without a token.
export async function createBot(): Promise<Client> {
  // Intents say which events Discord should send us. Guilds is enough for
  // slash commands.
  const client = new Client({ intents: [GatewayIntentBits.Guilds] });

  // Runs once, when the connection is ready. `ready` is the logged-in client.
  client.once(Events.ClientReady, (ready) => {
    console.log(`Ready as ${ready.user.tag}`);
  });

  return client;
}
```

Then `src/index.ts`, the only file that **connects**:

```ts
import { createBot } from "./bot.ts";

const client = await createBot();
await client.login(process.env.DISCORD_TOKEN);
```

Notice `await` at the top level of the file, outside any function. ES modules allow that.

Hover over `client` in VS Code: its type is `Client`. Hover over `process.env.DISCORD_TOKEN`: it's `string | undefined`, because the variable might not be set. `login()` accepts `undefined` (it then reports a missing token), so this type-checks. You'll see a lot more of `| undefined` soon.

## 10. Run it

In the terminal:

```sh
npm start
```

After a second or two you should see `Ready as YourBot#1234`, and your bot shows as online in your server. Press **Ctrl+C** to stop it. It goes offline again.

Then check the types:

```sh
npx tsc
```

No output means no errors. Run it often: VS Code shows errors in open files, but `tsc` checks everything.

## 11. Run the self-check

Copy `check.ts` from `MontyDevs_Vault/projects/bots-and-automation/bot-201-discord-bot/` into `my-bot` (drag it across, or from the `Code` folder):

```sh
# Windows (PowerShell)
Copy-Item MontyDevs_Vault\projects\bots-and-automation\bot-201-discord-bot\check.ts my-bot\

# macOS / Linux
cp MontyDevs_Vault/projects/bots-and-automation/bot-201-discord-bot/check.ts my-bot/
```

Then, in `my-bot`:

```sh
node check.ts 0
```

`[PASS]` means you're ready for [Module 01](../01-hello-discord/). The checker never logs in: it loads `src/bot.ts`, calls `createBot()`, and inspects what it gets back. That's why `src/bot.ts` must never call `login()` itself.

## Optional: track your bot with Git

Run `git init` in `my-bot`, then commit at the end of each module. Before your first commit, run `git status` and make sure `.env` and `node_modules` are **not** listed. [Git and GitHub basics](../../../../../guides/git-and-github.md) shows the rest.

## Stuck?

- **`An invalid token was provided`** or **`TokenInvalid`**: the token in `.env` is wrong or was reset. Reset it again in the Developer Portal and paste the new one, with no quotes or spaces. Check the file is called exactly `.env` (not `.env.txt`; Windows hides extensions by default).
- **`node: .env: not found`**: `.env` isn't in the folder you ran `npm start` from. Run commands from `my-bot`.
- **`SyntaxError: Cannot use import statement outside a module`**: `"type": "module"` is missing from `package.json`.
- **`Unknown file extension ".ts"`** or **`ERR_UNKNOWN_FILE_EXTENSION`**: your Node is older than 22.18. Check `node --version` and update.
- **`Cannot find module './bot'`**: imports of your own files need the extension: `./bot.ts`.
- **`'npm' is not recognized`, or PowerShell says running scripts is disabled**: see [Installing Node.js](../../../../../guides/installing-node.md#windows).
- **`Used disallowed intents`**: you asked for a privileged intent (like `MessageContent`) that's switched off in the portal. This project doesn't need any; use the code in step 9.
- **The bot logs in but doesn't appear in your server**: it wasn't invited. Redo step 5.6–5.7, and pick the right server.
- **`seems to contain a bot token`** from the checker: your token is in a source file. Move it to `.env`. If that file was ever shared or pushed anywhere, reset the token first.
