# Module 01: Scanning

**Goal:** a scanner that turns source code into tokens one at a time, as the compiler asks for them, and a `--tokens` flag that prints them. Your keywords get their final spellings.

## Concepts

### Tokens

A **token** is the smallest meaningful piece of a program: a name, a number, an operator, a keyword. Scanning `let total = 12.5;` gives five tokens:

```
LET let
IDENTIFIER total
EQUAL =
NUMBER 12.5
SEMICOLON ;
EOF
```

Each token has a **type**, its **lexeme** (the exact text), and the **line** it's on, for error messages.

### Scanning on demand

A tree-walking interpreter usually scans the whole file into a list of tokens first. This VM won't: the compiler in Module 02 asks for one token at a time, and only ever looks at the current token and the one before it. So the scanner is a small machine with a position in the source, and a `scan_token()` function that returns the next token each time it's called.

That means **a token doesn't own its text**. It points into the source buffer: a `const char *start` and a `length`. No allocation, no copying, and no freeing. The catch is that the lexeme isn't a C string (there's no `'\0'` after it), so print it with `printf("%.*s", length, start)`, and compare it with `memcmp`, not `strcmp`.

```c
typedef struct {
  TokenType type;
  const char *start;   // points into the source
  int length;
  int line;
} Token;
```

### Keywords are identifiers first

Scan anything that starts with a letter or `_` as a name, then check whether that name is one of your keywords. clox uses a hand-written **trie** (a `switch` on the first letter, then the next...) so a keyword check never compares more characters than it must. With your own spellings, you can do the same, or loop over a small table and `memcmp`. Either is fine: a scanner is never the slow part of a VM.

### Errors are tokens too

When the scanner hits something it can't scan (a `@`, a string with no closing quote, `\q` in a string), it returns an **error token** whose "lexeme" is the error message. The compiler reports it with the line number. That keeps the scanner simple: it never prints or exits.

## Practice

### Think it through

**1. Spot the problem.** This prints a token's lexeme. What goes wrong?

```c
Token t = scan_token();
printf("%s %s\n", type_names[t.type], t.start);
```

<details><summary>Answer</summary>

`t.start` points into the source, which carries on past the token. `%s` prints until it finds a `'\0'`, so it prints the rest of the file from that point. Use `printf("%s %.*s\n", type_names[t.type], t.length, t.start)`.

</details>

**2. Predict the tokens.** What does `x>=1==!y<=-2` scan to?

<details><summary>Answer</summary>

`IDENTIFIER x`, `GREATER_EQUAL >=`, `NUMBER 1`, `EQUAL_EQUAL ==`, `BANG !`, `IDENTIFIER y`, `LESS_EQUAL <=`, `MINUS -`, `NUMBER 2`, `EOF`. Two-character operators win: after `>`, the scanner checks whether the next character is `=`. And `-2` is two tokens: the scanner doesn't know whether `-` means "minus" or "negative", so the compiler decides.

</details>

**3. Spot the problem.** A scanner checks for a keyword like this. Which identifiers does it get wrong?

```c
if (memcmp(start, "if", 2) == 0) return TOKEN_IF;
```

<details><summary>Answer</summary>

Any identifier that *starts* with `if`: `iffy`, `if_ready`. It also reads past the end when the identifier is shorter than 2 characters (a one-letter name at the very end of the file). Check the length first: `length == 2 && memcmp(start, "if", 2) == 0`.

</details>

### Try it in code

[`practice_01.c`](practice_01.c): measuring a name, scanning a number with `strtod`, skipping whitespace and comments while counting lines, and a memory bug to fix. Copy it into your project folder, fill it in, and run `python3 check.py practice 1`.

<details><summary>Hints</summary>

- `identifier_length`: `isalpha`, `isdigit` and `isalnum` are in `<ctype.h>`. Pass them an `unsigned char`: `isalpha((unsigned char)c)`. A negative `char` is undefined behaviour in those functions, and the sanitizer will tell you so.
- `scan_number`: count the characters yourself (so you control the `.` rule), and let `strtod(text, NULL)` work out the value.
- `skip_space`: a loop with a `switch` on the current character. For `/`, look one character ahead.
- `copy_lexeme`: how many bytes does a 5-character C string need?

</details>

## Steps

Continue in your project from Module 00. Splitting the code into files now pays off later: for example `scanner.h` and `scanner.c` for the scanner, and `main.c` for the command line. Your design.

### 1. The scanner

Spec:

- `init_scanner(source)` (or your own name) starts scanning a NUL-terminated source string.
- `scan_token()` returns the next token. After the last token it returns `EOF`, and keeps returning `EOF` if called again.
- Token types and their rules are in the [spec's token table](../../SPEC.md#tokens). Skip spaces, tabs, `\r`, newlines and `//` comments between tokens, counting lines.
- Strings: from `"` to the next `"` on the same line. The lexeme includes the quotes and the escapes exactly as written: turning `\n` into a newline happens later, in Module 03. Inside a string, `\` must be followed by `n`, `t`, `"` or `\`.
- Errors are returned as error tokens, with the line they're on: an unexpected character, an unterminated string (reaching a newline or the end of the file), or an unknown escape.
- No fixed limits: a name or string can be thousands of characters long.

### 2. Your keywords

Pick your keyword spellings if you haven't, and put them in both `language.json` and your scanner. They must match: the self-check reads `language.json` and checks that your scanner turns each spelling into the right type.

### 3. `--tokens`

`./glim --tokens file` prints every token, one per line, as `TYPE lexeme`, ending with a line that just says `EOF`. Type names are exactly those in the spec (`LEFT_PAREN`, `IDENTIFIER`, `BANG_EQUAL`, ...).

On a scan error: print an error message to stderr that includes `line N`, and exit with code 65. (What was printed before the error doesn't matter.)

Running a file normally still prints it back, for now.

## Make it yours

- **Your keywords.** This is the moment to choose: `make` for `let`? `yeet` for `return`? `yes`/`no`/`nah`? Two spellings for one keyword?
- **Your error messages.** They need the line; beyond that, they're yours. Show the bad character? Suggest a fix?
- **Your keyword matcher.** A trie in a `switch`, a sorted table with binary search, a perfect hash... Try one and time it on a big file.

## Check your work

```sh
python3 check.py practice 1
python3 check.py 1
```

The self-check scans over a dozen programs, including a 20,000-character string and a 4,000-line file, and checks your scan errors. Everything runs under the sanitizers, so reading even one byte past the end of the source is caught.

## Stuck?

- **The sanitizer reports `heap-buffer-overflow` in your scanner, reading 1 byte past the source**: something looks ahead without checking for the end. "Peek at the next character" must check that the current one isn't `'\0'` first.
- **`EOF` printed twice, or tokens after `EOF`**: `scan_token()` was called again after the end, and moved past the `'\0'`.
- **Wrong line numbers on errors**: you count newlines in `skip_whitespace` but not inside comments, or count them twice.
- **`Token 1 should be LET glim...`**: your scanner and `language.json` disagree about a spelling.

<details><summary>Hint 1</summary>

Keep three things in the scanner: `start` (where the current token began), `current` (the character being looked at) and `line`. Each call to `scan_token()` skips whitespace, sets `start = current`, then reads one token.

</details>

<details><summary>Hint 2</summary>

Helper functions make the main `switch` short: `advance()` (return the current character and move on), `peek()` (look without moving), `peek_next()`, and `match(expected)` (move on only if the current character is `expected`). Then `case '!': return make_token(match('=') ? TOKEN_BANG_EQUAL : TOKEN_BANG);`.

</details>

<details><summary>Hint 3</summary>

For strings: loop while `peek() != '"'`. Inside, if you see a newline or `'\0'`, return an "Unterminated string." error token. If you see `\`, advance, check the next character is one of `n t " \`, and advance past it. After the loop, advance past the closing quote and make a `TOKEN_STRING` from `start` to `current`.

</details>

## Resources

- [*Crafting Interpreters*, chapter 16: Scanning on Demand](https://craftinginterpreters.com/scanning-on-demand.html): the clox scanner, with the trie for keywords. Our token set differs (`%`, `let`, `fn`, no classes or `for`) and our strings have escapes, but the structure is the same.
- [Beej's Guide to C: Strings](https://beej.us/guide/bgc/html/split/strings.html): why a C string needs its `'\0'`, and what `%.*s` is for.

## Challenges (optional)

- Report **every** scan error in a file, not just the first.
- Time your scanner on a 10 MB file of random tokens. How many tokens per second?
- Add a token your language will use later: `+=`, `[` and `]`, or `**`.

## Next

Continue to [Module 02: Chunks and a Stack VM](../02-chunks-and-a-stack-vm/).
