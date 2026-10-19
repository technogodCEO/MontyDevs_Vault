# Installing Node.js

**Node.js** runs JavaScript (and, in recent versions, TypeScript) outside the browser. It comes with **npm**, which downloads the libraries a project uses.

Projects that use Node say which version they need. The Discord Bot needs **Node 22.18 or newer**, and **Node 24 LTS** is best. ("LTS" means long-term support: the version that gets fixes for years. Pick it over the "Current" one.)

Follow the section for your computer, then [check that it worked](#check-that-it-worked).

## Windows

1. Go to [nodejs.org/en/download](https://nodejs.org/en/download) and download the **Windows Installer (.msi)** for the LTS version.
2. Run it and accept the defaults. You don't need the "Tools for Native Modules" option.
3. Close any terminals you already had open, and open a new one so it finds `node`.

> **PowerShell says "running scripts is disabled on this system" when you run `npm`?** Windows blocks the `npm.ps1` script by default. Run this once, then open a new terminal:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> ```
> It lets you run scripts you've installed yourself, and nothing changes for other users.

## macOS

Download the **macOS Installer (.pkg)** for the LTS version from [nodejs.org/en/download](https://nodejs.org/en/download), open it and follow the steps.

If you use [Homebrew](https://brew.sh/), `brew install node@24` works too (Homebrew prints one extra command to put it on your PATH; run it).

## Linux

The `nodejs` package in most distributions is too old. Use a version manager instead (below), or the official packages from [nodejs.org/en/download](https://nodejs.org/en/download), which show the commands for your system.

## Optional: a version manager

Different projects sometimes need different Node versions. A **version manager** lets you install several and switch between them, without admin rights. If you already have an old Node installed, this is the easiest way to get a new one.

- **[fnm](https://github.com/Schniz/fnm)** works on Windows, macOS and Linux. After installing it (its page shows how), run:
  ```sh
  fnm install 24
  fnm default 24
  ```
- **[nvm](https://github.com/nvm-sh/nvm)** is the classic one for macOS and Linux: `nvm install 24`. (On Windows, the similar tool is [nvm-windows](https://github.com/coreybutler/nvm-windows).)

## Check that it worked

Open a **new** terminal (see [Terminal basics](terminal-basics.md)) and run:

```sh
node --version
npm --version
```

You should see something like `v24.11.0` and `11.6.2`. For the Discord Bot, the first number must be at least **v22.18** (so v22.18.0 or later, or any v23, v24 or newer).

## npm in two minutes

Every Node project has a **`package.json`**: its name, the commands it can run, and the libraries it needs.

| Command | What it does |
| --- | --- |
| `npm init -y` | Make a new `package.json` in this folder |
| `npm install discord.js` | Download a library and list it in `package.json` under `dependencies` |
| `npm install --save-dev typescript` | The same, for tools only you need while developing (`devDependencies`) |
| `npm install` | Download everything `package.json` lists (after cloning a project, for example) |
| `npm run <name>` | Run a command from the `scripts` section of `package.json` (`npm test` and `npm start` work without `run`) |
| `npx <tool>` | Run a tool installed in this project, like `npx tsc` |

Libraries go in a **`node_modules`** folder, which can hold thousands of files. Never edit it, and never put it in Git: anyone can recreate it with `npm install`. **`package-lock.json`** records the exact version of every library installed, so everyone gets the same ones. Do keep that file in Git.

## Troubleshooting

- **`'node' is not recognized` or `command not found`**: Node isn't installed, or the terminal was open before you installed it. Open a new terminal. On Windows, restarting the computer also fixes a PATH that hasn't updated.
- **`node --version` shows an old version after you installed a new one**: an older install comes first on your PATH. Uninstall the old one (Windows: *Settings → Apps*), or use a version manager, which takes care of it.
- **`npm install` fails with `EACCES` (macOS/Linux)**: don't use `sudo`. This happens with a system-wide Node; switch to a version manager.
- **Still stuck?** Ask in the club chat, and include the exact command you typed and the message you got.
