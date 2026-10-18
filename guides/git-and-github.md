# Git and GitHub basics

**Git** keeps a history of your code, so you can always go back to a version that worked. **GitHub** is a website that stores Git projects online, so you can share them and work on them from any computer.

You don't need Git to do the projects. You can download the vault as a ZIP instead. But it's worth learning, and a GitHub profile full of projects you built yourself is great to show people.

## Install Git

- **Windows:** download it from [git-scm.com](https://git-scm.com/downloads) and accept the default options.
- **macOS:** run `git --version` in a terminal. If Git isn't installed, macOS offers to install it for you.
- **Linux:** `sudo apt install git` (Ubuntu/Debian), or your system's package manager.

Then tell Git who you are (use the email from your GitHub account):

```sh
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

## Get the vault onto your computer

On the vault's GitHub page, click the green **Code** button and copy the URL. Then, in a terminal, in the folder where you keep your projects:

```sh
git clone <the URL you copied>
```

That creates a `MontyDevs_Vault` folder with every tutorial in it. Later, to get any new tutorials or fixes, go into that folder and run:

```sh
git pull
```

No Git? Click **Code → Download ZIP** and unzip it instead.

## Keep your own project in Git

Keep your project in **its own folder, outside the vault** (for example `my-adventure`). Then:

```sh
cd my-adventure
git init                       # start tracking this folder
git add .                      # stage every file for saving
git commit -m "Finish module 01"
```

Each `commit` saves a snapshot. Commit whenever something works, like at the end of each module, so you can always get back to it.

| Command | What it does |
| --- | --- |
| `git status` | Show what's changed since the last commit |
| `git add .` | Stage all changes for the next commit |
| `git commit -m "message"` | Save a snapshot with a short description |
| `git log --oneline` | List your past commits |

## Put it on GitHub

1. Make a free account at [github.com](https://github.com/).
2. Click **+** (top right) → **New repository**. Give it a name, leave "Add a README" unticked, and click **Create repository**.
3. GitHub shows you commands under "push an existing repository". Run them in your project folder. They look like this:
   ```sh
   git remote add origin https://github.com/<you>/<repo>.git
   git branch -M main
   git push -u origin main
   ```
4. After that, each time you commit, run `git push` to upload it.

The first push asks you to sign in. Follow the prompts in the browser window that opens.

## Learn more

- [GitHub Docs: Hello World](https://docs.github.com/en/get-started/start-your-journey/hello-world): GitHub's own 10-minute introduction.
- [Pro Git](https://git-scm.com/book/en/v2): the free official book. Chapter 2 covers everything you'll need day to day.
