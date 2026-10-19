# Module 00: Setup

**Goal:** a C compiler with working sanitizers, the vault on your computer, and a project for your language: a name, a file extension and keyword spellings in `language.json`, a `Makefile`, and a `main.c` that reads files and runs a REPL that echoes.

This takes about 30 minutes, most of it installing tools.

## 1. Install the tools

Follow [Installing a C compiler](../../../../../guides/installing-a-c-compiler.md). It covers Linux, macOS, and Windows through **WSL**, and ends by checking that `cc`, `make`, `python3` and the sanitizers all work.

**On Windows, use WSL.** The self-check needs AddressSanitizer, UndefinedBehaviorSanitizer and Unix process limits, which native Windows compilers don't fully support. Inside WSL you get exactly the same tools as Linux. Do every step from here on in the Ubuntu terminal.

For an editor, [Setting up VS Code](../../../../../guides/vs-code.md) works well with the **C/C++** extension (and the **WSL** extension on Windows).

## 2. Get the vault

Clone it in your terminal ([Git and GitHub basics](../../../../../guides/git-and-github.md)):

```sh
git clone https://github.com/technogodCEO/MontyDevs_Vault.git
```

## 3. Name your language

Pick:

- **A name.** The examples use *Glim*.
- **A file extension** for its programs, like `.glim`: a dot, then letters or digits.
- **Keyword spellings**, if you want your own now. You can also keep the usual ones until Module 01.

If you did the [Tree-Walking Interpreter](../../../01-tree-walking-interpreter/), use your language from there. Its `language.json` works here as it is (this project ignores its `"main"` entry).

## 4. Make your project folder

Make a folder for your language **outside** the vault, with a `src/` folder for your C code, and copy `check.py` into it:

```
code/
├── MontyDevs_Vault/       # the tutorials (don't put your code in here)
└── glim/                  # your language
    ├── language.json
    ├── Makefile
    ├── check.py
    └── src/
        └── main.c
```

```sh
mkdir -p glim/src
cp MontyDevs_Vault/projects/programming-languages/02-bytecode-vm/check.py glim/
```

## 5. Write `language.json`

The self-check reads this file to learn your language's name, extension and keywords:

```json
{
  "name": "Glim",
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

`"keywords"` maps each **spelling** (left) to its **token type** (right). The twelve types are fixed and each needs at least one spelling; the spellings are yours (`"yeet": "RETURN"`). Spellings must look like names, and can't be `clock`, `len` or `str`, the built-in functions from Module 06.

Your C scanner will have these spellings built in (Module 01). The self-check reads `language.json`, writes every test program in your spelling, and checks that your scanner agrees with the file.

## 6. Write a Makefile

`make` rebuilds your VM with one command. Make `Makefile` (no extension) in your project folder. Every command line under a target **must start with a tab**, not spaces:

```make
# Build the VM with `make`, or a sanitizer build with `make debug`.
NAME   = glim
CFLAGS = -std=c11 -Wall -Wextra -Wno-unused-parameter
SRC    = $(wildcard src/*.c)
HDR    = $(wildcard src/*.h)

$(NAME): $(SRC) $(HDR)
	$(CC) $(CFLAGS) -O2 $(SRC) -o $@ -lm

debug: $(SRC) $(HDR)
	$(CC) $(CFLAGS) -g -fsanitize=address,undefined $(SRC) -o $(NAME)-debug -lm

clean:
	rm -f $(NAME) $(NAME)-debug

.PHONY: debug clean
```

`make` builds `./glim`; `make debug` builds `./glim-debug`, which stops with a report the moment your code touches memory it shouldn't. Use the debug build while you're working: it turns the worst C bugs (the ones that "work" until they don't) into an error message with a line number.

The self-check doesn't use your Makefile. It compiles `src/*.c` itself with the same flags, so your `Makefile` is yours to change.

## 7. Write `src/main.c`

Spec for this module:

- `./glim path/to/file` reads the **whole** file and prints its contents exactly. Files can be any size, so read the size first and allocate a buffer to fit, rather than using a fixed-size array.
- If the file can't be opened, print a message to **stderr** saying which file, and exit with code **66**.
- `./glim` with no arguments starts a **REPL**: print a prompt like `> `, read a line, and for now print it back. At end of input (Ctrl+D), exit with code 0.
- Any other arguments: print a usage message to stderr and exit with code 64.
- Free everything you allocate. The checked build includes a leak checker (on Linux and WSL).
- No warnings, with `-Wall -Wextra`.

The C library pieces you need: `fopen` and `fclose`, `fseek`/`ftell`/`rewind` to find a file's size, `malloc`, `fread`, `fgets` for reading a line, `fputs` or `printf`, and `exit` (all in `<stdio.h>` and `<stdlib.h>`). `argc` and `argv` hold the command line: for `./glim hello.glim`, `argc` is 2 and `argv[1]` is `"hello.glim"`.

<details><summary>Hint: reading a whole file</summary>

Open it in binary mode (`"rb"`) so nothing changes the bytes. `fseek(file, 0, SEEK_END)` then `ftell(file)` gives its size; `rewind(file)` goes back to the start. Allocate size + 1 bytes, `fread` into it, and put a `'\0'` after the last byte read, so the rest of your VM can treat the source as one C string.

</details>

<details><summary>Hint: the REPL</summary>

`fgets(line, sizeof line, stdin)` returns `NULL` at end of input. Call `fflush(stdout)` after printing the prompt, so it shows before the program waits for input.

</details>

## 8. Ignore build files

If you keep your project in Git (recommended), make a `.gitignore` so builds don't get committed:

```
glim
glim-debug
```

## 9. Check your setup

```sh
make && ./glim language.json
python3 check.py 0
```

The first prints your `language.json` back. The self-check compiles your code in both builds, runs it on a few files and the REPL, and should end with:

```
[PASS] Everything up to module 00 works. Glim is coming along!
```

## Stuck?

- **`Makefile:7: *** missing separator. Stop.`**: the command lines under a target start with spaces. They must start with a tab. (In VS Code, the bottom bar says "Spaces" or "Tab Size"; click it to change that file to tabs.)
- **`[NOT YET] Your VM compiled, but with warnings`**: fix them all. A common one here: `unused variable`, or comparing `size_t` (unsigned) with `int`.
- **The checker says the REPL never stopped**: your loop doesn't notice end of input. Check what `fgets` returns.
- **A leak report mentioning `readFile` or `main`**: you didn't `free` the buffer you read the file into.
- **`[WARN] Couldn't build with -fsanitize=address,undefined`**: your compiler can't use the sanitizers. On Linux, install `gcc` (`sudo apt install gcc`); the checker picks it automatically. See the [guide](../../../../../guides/installing-a-c-compiler.md#check-it-works).

## Next

Continue to [Module 01: Scanning](../01-scanning/).
