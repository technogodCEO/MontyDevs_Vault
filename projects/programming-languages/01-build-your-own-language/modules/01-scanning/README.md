# Module 01: Scanning

**Goal:** a scanner that turns source code into a list of tokens, with `--tokens` to print them, and clear errors for characters and strings it can't scan.

## Concepts

### From characters to tokens

To a computer, a program is just a string of characters. The first stage of every interpreter, the **scanner** (or *lexer*), groups those characters into **tokens**: the words of the language.

```
let total = price * 2;
```

becomes

```
LET let
IDENTIFIER total
EQUAL =
IDENTIFIER price
STAR *
NUMBER 2
SEMICOLON ;
EOF
```

Each token has a **type** (what kind of word it is), its **lexeme** (the exact characters from the source), and the **line** it's on, for error messages. Strings and numbers also carry their **value**: the lexeme `"hi\n"` (six characters) has the value `hi` plus a newline (three characters). Spaces, tabs, newlines and comments don't become tokens. They only separate them.

A token class can be very small:

```python
class Token:
    def __init__(self, type, lexeme, value, line):
        self.type = type        # "NUMBER", "PLUS", "LET", ...
        self.lexeme = lexeme    # the source text: "12.5", "+", "let"
        self.value = value      # 12.5 for numbers, the text for strings, else None
        self.line = line        # 1 for the first line
```

### The scanning loop

A scanner walks through the source one character at a time, keeping track of where the current token *started* and where it is *now*. It looks at the next character and decides what kind of token is beginning:

- A single character like `(` or `;` is a whole token.
- Some characters need one more look ahead: `=` might be `=` or the start of `==`. `/` might be division, or the start of a `//` comment.
- A digit starts a number, so it keeps going while there are digits.
- A letter or `_` starts a name, so it keeps going while there are letters, digits or `_`. Then it checks whether the name is a keyword.
- A `"` starts a string, so it keeps going until the closing `"`.

Always taking the longest token you can is called **maximal munch**. It's why `>=` is one token, not two, and why `iffy` is a name rather than the keyword `if` followed by `fy`.

### Keywords are just reserved names

The scanner reads `while` exactly the way it reads `count`: as a run of letters. Only *afterwards* does it look the word up in `KEYWORDS`. If the word is there, the token gets the keyword's type. If not, it's an `IDENTIFIER`. That one lookup is what lets you spell your keywords however you like.

## Practice

Warm up on this module's ideas before you use them in your interpreter.

### Think it through

Try each one in your head first, then click **Answer** to check.

**1. How many tokens?** Count the tokens (not including `EOF`) in each line:

```
a>=b
x = y==z;// done
"a // b"
```

<details><summary>Answer</summary>

- `a>=b`: **3** (`a`, `>=`, `b`). Maximal munch makes `>=` one token, and spaces aren't needed between tokens.
- `x = y==z;// done`: **6** (`x`, `=`, `y`, `==`, `z`, `;`). The comment is dropped.
- `"a // b"`: **1** string. Inside a string, `//` is just two characters, not a comment.

</details>

**2. Spot the problem.** This scanner code handles `=` and `==`. What goes wrong with the input `x = = 1`, and with `x == 1`?

```python
elif c == "=":
    if source[i + 1] == "=":
        tokens.append(Token("EQUAL_EQUAL", "==", None, line))
    else:
        tokens.append(Token("EQUAL", "=", None, line))
    i += 1
```

<details><summary>Answer</summary>

`x = = 1` works: two `EQUAL` tokens. But for `x == 1`, after adding `EQUAL_EQUAL` it only moves forward one character, so the second `=` gets scanned *again*, as an extra `EQUAL`. It needs `i += 2` in the `==` branch.

There's a second bug: if `=` is the very last character, `source[i + 1]` is past the end and raises an `IndexError`. `source[i + 1:i + 2]` is safer, because slicing past the end gives `""`.

</details>

### Try it in code

[`practice_01.py`](practice_01.py) has four scanning helpers to write: reading a number, checking a name, a line-counting bug, and a mini tokenizer.

1. Copy `practice_01.py` into your project folder, next to `check.py`.
2. Fill in each function. The one marked **FIX THE BUG** already has code: find what's wrong and fix it.
3. Test your answers:
   ```sh
   python check.py practice 1
   ```

<details><summary>Hints</summary>

- `read_number`: two `while` loops, one for the whole part and one for the fraction. Only step past the `.` if the character after it is a digit.
- `is_identifier`: `str.isalnum()`, `str.isdigit()` and `all()` make this short. Remember the empty string.
- `line_of`: lines are counted from 1, but how many newlines come before a character on the first line?
- `split_tokens`: the same shape as your scanner. Use an index `i` and a `while i < len(text)` loop, not a `for` loop, so you can move forward by more than one character at a time.

</details>

## Steps

This is the spec your scanner must meet. How you structure the code is up to you: one file or several (a `lexer.py` is common), a class or functions.

### 1. Token types

| Type | Lexemes |
| --- | --- |
| `LEFT_PAREN` `RIGHT_PAREN` `LEFT_BRACE` `RIGHT_BRACE` | `(` `)` `{` `}` |
| `COMMA` `SEMICOLON` | `,` `;` |
| `PLUS` `MINUS` `STAR` `SLASH` `PERCENT` | `+` `-` `*` `/` `%` |
| `BANG` `BANG_EQUAL` | `!` `!=` |
| `EQUAL` `EQUAL_EQUAL` | `=` `==` |
| `LESS` `LESS_EQUAL` `GREATER` `GREATER_EQUAL` | `<` `<=` `>` `>=` |
| `NUMBER` | digits, optionally followed by `.` and more digits: `7`, `3.14`, `007`. Not `.5` or `5.` |
| `STRING` | `"` ... `"`, on one line |
| `IDENTIFIER` | a letter or `_`, then any letters, digits or `_` |
| the 12 keyword types | any identifier that's a key in your `KEYWORDS` |
| `EOF` | added once, at the end of every token list |

### 2. What gets skipped

- Spaces, tabs, carriage returns and newlines (each newline adds one to the line number).
- Comments: `//` to the end of the line.

### 3. Strings

- A string can't contain a line break. Reaching the end of the line or the file before the closing `"` is an "unterminated string" error.
- Inside a string, a backslash starts an **escape**: `\n` (newline), `\t` (tab), `\"` (a quote that doesn't end the string) and `\\` (one backslash). Any other character after a backslash is an error.
- The token's lexeme is the raw source, quotes and backslashes included. Its value is the text with the escapes turned into the characters they stand for.

### 4. Numbers

Store every number's value as a Python `float`, even `7`. Your language has one number type, like JavaScript.

### 5. Errors

Any other character (like `@`, `#` or `$`) is an "unexpected character" error. On any scan error:

- Print a message to **stderr** (`print(..., file=sys.stderr)`) that includes `line N`, where N is the line the problem is on. For an unterminated string, that's the line the string starts on.
- Exit with code **65**.

### 6. `--tokens`

`python glim.py --tokens program.glim` scans the file and prints each token on its own line as `TYPE lexeme`, ending with a line that says just `EOF`:

```
PRINT print
STRING "hi\n"
SEMICOLON ;
EOF
```

Running a file without `--tokens` and the REPL can stay as they were in Module 00.

### 7. Your turn: design decisions

- Where does the scanner live, and what does it return? A list of tokens is simplest.
- How will you report errors? A custom exception (say, `ScanError` with a line number) that `main()` catches is cleaner than calling `sys.exit` deep inside the scanner. You'll reuse the idea in every later module.
- Write the scanner so the keyword *spellings* only appear in `KEYWORDS`. Everything else should use the token *types*. Then renaming a keyword is a one-line change.

## Make it yours

- **Spell your keywords.** Now's the moment: rename them in `KEYWORDS` and write a few programs to see how they read. Some learners keep the usual names. Others write `make x = 1;`, `when (...)`, `yeet result;`. Every later test program uses your spellings.
- **Write error messages people like reading.** `[line 3] Unexpected character '@'.` is fine. You could also show the line itself with a `^` under the character.
- **Add more escapes** if you want, such as `\r` or `\0`. The spec only requires the four above.

## Check your work

```sh
python check.py 1
```

The checker runs `--tokens` on programs covering every token type (written with your keyword spellings) and compares the output with what it expects, token by token. Then it checks the error cases.

## Stuck?

- **Every token after a `==` or `<=` is off by one**: when you match a two-character token, move forward two characters.
- **`IndexError: string index out of range`**: you looked ahead past the end of the source. Check `i + 1 < len(source)` first, or slice (`source[i+1:i+2]`), which gives `""` at the end.
- **`NUMBER 10` instead of `NUMBER 10.0`**: print the lexeme (the original text), not the value.
- **A string's escapes break `--tokens`**: the lexeme is the raw source, so `"a\nb"` prints exactly as written, backslash and all. Only the *value* has a real newline.
- **The line number is wrong for errors near the end**: are you counting newlines inside comments? You should be.

<details><summary>Hint 1: the shape of the loop</summary>

Keep `start`, `current` and `line`. At the top of each loop, set `start = current`, read one character, and decide what to do with it. When a token is finished, its lexeme is `source[start:current]`.

</details>

<details><summary>Hint 2: two-character tokens</summary>

Write a helper `match(expected)` that checks whether the *next* character is `expected`. If it is, move past it and return `True`. Then `=` becomes `"EQUAL_EQUAL" if match("=") else "EQUAL"`, and `/` checks `match("/")` to decide whether a comment has started.

</details>

<details><summary>Hint 3: strings with escapes</summary>

Collect the string's value in a list of characters as you go. In a loop until the closing `"`: if you reach a newline or the end, raise an unterminated-string error. If the character is a backslash, look up the next character in a dictionary like `{"n": "\n", "t": "\t", '"': '"', "\\": "\\"}`, append the result and skip both. Otherwise append the character. Afterwards, the lexeme is `source[start:current]` and the value is `"".join(chars)`.

</details>

## Resources

- [*Crafting Interpreters*, chapter 4: Scanning](https://craftinginterpreters.com/scanning.html): builds a scanner step by step. Take the structure (start/current, `match`, `peek`) and the idea of reporting errors without crashing. Lox has a few different tokens (like `.` and `class`), so stick to the table above.
- [*Crafting Interpreters*, chapter 2: A Map of the Territory](https://craftinginterpreters.com/a-map-of-the-territory.html): a tour of every stage of a language implementation. Read it now to see where scanning fits.
- [Wikipedia: Lexical analysis](https://en.wikipedia.org/wiki/Lexical_analysis): the standard terms (lexeme, token, maximal munch) in one place.

## Challenges (optional)

- Report *every* bad character in a file, not just the first, before exiting.
- Allow `_` as a digit separator in numbers, so `1_000_000` is one `NUMBER`.
- Add `/* block comments */` that can span lines (and keep the line count right).

## Next

Continue to [Module 02: Parsing Expressions](../02-parsing-expressions/).
