# Module 00: Setup

**Goal:** Python ready, the vault on your computer, and a project folder for your language: a name, a file extension, keyword spellings in `language.json`, and a main file that runs.

This takes about 15 minutes. If you've already done a Python project in the vault, skip to [step 3](#3-get-the-vault).

## 1. Install Python

Follow [Installing Python](../../../../../guides/installing-python.md) if you haven't, then check the version:

```sh
python --version
```

You need **3.9 or newer**.

> **macOS and Linux:** type `python3` everywhere this project says `python`. On Windows, `py` works too.

## 2. Install a code editor

Any editor works. [Setting up VS Code](../../../../../guides/vs-code.md) covers VS Code and its Python extension. You'll be juggling several files, so an editor that can jump to a function's definition (F12 in VS Code) helps.

## 3. Get the vault

Clone it with Git, or click **Code → Download ZIP** on GitHub and unzip it ([Git and GitHub basics](../../../../../guides/git-and-github.md)):

```sh
git clone https://github.com/technogodCEO/MontyDevs_Vault.git
```

## 4. Name your language

Pick three things:

- **A name.** Short and fun to say. The examples use *Glim*.
- **A file extension** for programs in your language, like `.glim`. A dot, then letters or digits. Not `.py`.
- **A main file name**: the Python file people run to use your language, like `glim.py`.

## 5. Make your project folder

Make a folder for your language **outside** the vault, and copy `check.py` into it from `MontyDevs_Vault/projects/programming-languages/01-tree-walking-interpreter/`:

```
Code/
├── MontyDevs_Vault/        # the tutorials (don't put your code in here)
└── glim/                   # your language
    ├── language.json
    ├── glim.py
    └── check.py
```

```sh
# Windows (PowerShell), from the Code folder
Copy-Item MontyDevs_Vault\projects\programming-languages\01-tree-walking-interpreter\check.py glim\

# macOS / Linux
cp MontyDevs_Vault/projects/programming-languages/01-tree-walking-interpreter/check.py glim/
```

## 6. Write `language.json`

This file describes your language, and the self-check reads it. Create `language.json` with your choices from step 4, plus a spelling for each **keyword**:

```json
{
  "name": "Glim",
  "main": "glim.py",
  "extension": ".glim",
  "keywords": {
    "let": "LET",
    "fn": "FN",
    "if": "IF",
    "else": "ELSE",
    "while": "WHILE",
    "return": "RETURN",
    "print": "PRINT",
    "true": "TRUE",
    "false": "FALSE",
    "nil": "NIL",
    "and": "AND",
    "or": "OR"
  }
}
```

`"keywords"` maps each **spelling** (on the left) to its **token type** (on the right). The twelve types are fixed, and every one needs at least one spelling. The spellings are yours: `"yeet": "RETURN"` makes `yeet` your return keyword. Two spellings can share a type (`"let"` and `"make"` both `LET`).

Keep the usual spellings for now if you like: you'll choose your own in Module 01. Each spelling must look like a name (letters, digits and underscores) and can't be `clock`, `len` or `str`, which are built-in functions in Module 06.

If you also do the [Bytecode Virtual Machine](../../../02-bytecode-vm/) project, the same `language.json` works there.

## 7. Write the main file

**A command-line interface.** For now:

- `python glim.py path/to/program.glim` reads the file and prints its contents back exactly.
- If the file doesn't exist, print a friendly message (not a Python traceback) and exit with code 66: `sys.exit(66)`.
- `python glim.py` with no file starts a **REPL** (read-eval-print loop). It shows a prompt like `> `, reads a line, and for now prints it straight back. When the input runs out, it stops cleanly with exit code 0. (Typing Ctrl+D on macOS/Linux, or Ctrl+Z then Enter on Windows, sends "end of input", which `input()` reports as an `EOFError`.)

**The main guard.** Put everything that runs in a `main()` function, called only under `if __name__ == "__main__":` at the bottom. Then other files (and tests you write) can import your code without starting the REPL.

Here's the shape, with the interesting parts left for you:

```python
import sys


def run_file(path):
    # Read the file (what if it doesn't exist?) and, for now, print it back.
    ...


def repl():
    # Loop: show a prompt, read a line, print it back. Stop at end of input.
    ...


def main():
    if len(sys.argv) > 1:
        run_file(sys.argv[1])
    else:
        repl()


if __name__ == "__main__":
    main()
```

`sys.argv` is the list of words on the command line: for `python glim.py hello.glim` it's `["glim.py", "hello.glim"]`.

## 8. Try it

Create a file `hello.glim` (with your extension) holding any text, then:

```sh
python glim.py hello.glim
python glim.py
```

The first prints your file. The second starts the REPL: type a few lines, then end the input.

## 9. Run the self-check

```sh
python check.py 0
```

`[PASS]` means your language exists. Start [Module 01](../01-scanning/).

## Optional: track it with Git

You'll be making big changes to working code, so commit at the end of each module. Then if a refactor goes wrong, you can always get back. See [Git and GitHub basics](../../../../../guides/git-and-github.md).

## Stuck?

- **`Couldn't find language.json`**: run `check.py` from your project folder (the one with `language.json`), or pass the folder: `python check.py 0 path/to/glim`.
- **`language.json isn't valid JSON`**: JSON needs double quotes around every string, commas between entries, and no comma after the last one.
- **`needs "keywords"`** or **`needs a spelling for every keyword type`**: copy the `"keywords"` block from step 6 and check that all twelve types are there, spelled in capitals.
- **`Running a file that doesn't exist crashed`**: wrap your `open()` in `try`/`except OSError`.
- **The REPL test fails with exit code 1**: catch `EOFError` around `input()` and stop the loop.
