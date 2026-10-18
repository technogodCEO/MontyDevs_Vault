# Module 00: Setup

**Goal:** Python and an editor installed, the vault on your computer, and a game folder of your own with an `adventure.py` that runs.

This takes 15–30 minutes the first time. If you've already done another Python project in the vault, you can skip straight to [step 4](#4-make-your-game-folder).

## 1. Install Python

Follow [Installing Python](../../../../guides/installing-python.md) for your computer, then check it worked by opening a terminal and running:

```sh
python --version
```

You need **3.9 or newer**.

> **macOS and Linux:** type `python3` everywhere this project says `python`. On Windows, `py` works too.

New to the terminal? Read [Terminal basics](../../../../guides/terminal-basics.md) first. It's short.

## 2. Install a code editor

Follow [Setting up VS Code](../../../../guides/vs-code.md), including the Python extension. Any editor works, but these instructions assume VS Code.

## 3. Get the vault

You need a copy of the vault on your computer for this project's `check.py` and the example solutions. Pick one way:

- **With Git (recommended):** in a terminal, go to the folder where you keep projects and run:
  ```sh
  git clone https://github.com/technogodCEO/MontyDevs_Vault.git
  ```
  Later, `git pull` inside that folder gets any updates. See [Git and GitHub basics](../../../../guides/git-and-github.md) if you haven't installed Git.
- **Without Git:** on the vault's GitHub page, click **Code → Download ZIP**, then unzip it somewhere you'll find it again.

## 4. Make your game folder

Make a new folder for **your** game, **outside** the vault, for example `my-adventure` next to `MontyDevs_Vault`:

```
Projects/
├── MontyDevs_Vault/        # the tutorials (don't put your code in here)
└── my-adventure/           # your game
    ├── adventure.py
    └── check.py
```

Keeping your code separate means updating the vault never touches your work.

Copy `check.py` from `MontyDevs_Vault/games/01-text-adventure/` into `my-adventure/`. You can drag it across in your file explorer, or run this from the `Projects` folder:

```sh
# Windows (PowerShell)
Copy-Item MontyDevs_Vault\games\01-text-adventure\check.py my-adventure\

# macOS / Linux
cp MontyDevs_Vault/games/01-text-adventure/check.py my-adventure/
```

## 5. Create `adventure.py`

1. In VS Code, use *File → Open Folder...* and open `my-adventure`.
2. Create a new file called `adventure.py` (*File → New File*, or the new-file icon in the sidebar).
3. Type this in. Typing it rather than pasting it helps you get used to Python's indentation:
   ```python
   # adventure.py
   # My text adventure.


   def main():
       print("Hello, adventurer!")


   # Start the game only when this file is run directly.
   # This lets check.py load your code without the game starting by itself.
   if __name__ == "__main__":
       main()
   ```
4. Save it.

## 6. Run it

Open the terminal in VS Code (*Terminal → New Terminal*). It should already be in `my-adventure`. Run:

```sh
python adventure.py
```

You should see `Hello, adventurer!`.

## 7. Run the self-check

Every module ends by running `check.py` with the module's number. Try it now:

```sh
python check.py 0
```

`[PASS]` means you're set up and ready to start [Module 01](../01-the-game-loop/).

## Optional: track your game with Git

Run `git init` inside `my-adventure` and commit at the end of each module, so you can always go back to a version that worked. [Git and GitHub basics](../../../../guides/git-and-github.md) walks you through it, including putting your finished game on GitHub.

## Stuck?

- **`python: command not found`, `'python' is not recognized`, or the Microsoft Store opens**: see the troubleshooting section of [Installing Python](../../../../guides/installing-python.md).
- **`can't open file 'adventure.py'`** or **`No such file or directory`**: your terminal is in a different folder. Run `pwd` to see where you are, then `cd` into `my-adventure`. (Opening the folder in VS Code and using its terminal avoids this.)
- **`Couldn't find .../adventure.py`** from `check.py`: the file is misnamed or in another folder. It must be called exactly `adventure.py` (watch out for `adventure.py.txt` on Windows, where file extensions may be hidden).
- **`IndentationError`**: the `print` line must be indented 4 spaces under `def main():`, and `main()` 4 spaces under the `if` line.
