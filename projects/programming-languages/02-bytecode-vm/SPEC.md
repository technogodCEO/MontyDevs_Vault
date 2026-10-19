# The language spec

Everything your VM must do, in one place. Each module's lesson specifies its own part in more detail; this page is for looking things up. Programs here use the usual keyword spellings: yours come from `language.json`.

If you did the [Tree-Walking Interpreter](../01-tree-walking-interpreter/), this is the same language, with two differences, both because a single-pass compiler decides where each variable lives as it reads the code:

- Reading a **local** variable in its own initializer (`{ let x = x + 1; }`) is a compile error here.
- There's no `--ast`. You get `--disassemble` instead.

## The command line

| Command | What it does |
| --- | --- |
| `vm file` | Compile and run the program in `file` |
| `vm` | Start a REPL: show a prompt, read a line, run it, repeat until end of input, then exit with code 0 |
| `vm --tokens file` | Print the file's tokens, one per line, as `TYPE lexeme`, ending with `EOF` |
| `vm --disassemble file` | Compile the file and print its bytecode, without running it |

(`vm` is whatever you call your binary.)

**Exit codes:**

| Code | Meaning |
| --- | --- |
| 0 | Success |
| 64 | Wrong command-line arguments |
| 65 | Scan or compile error. Nothing in the program runs. |
| 66 | The file couldn't be opened |
| 70 | Runtime error. Output printed before the error still appears. |

Error messages go to **stderr** and must include `line N`, the line the error is on. The rest of the wording is yours.

In the REPL, an error is reported and the REPL carries on. Global variables and functions last from one line to the next.

## Tokens

| Type | Lexemes |
| --- | --- |
| Punctuation | `LEFT_PAREN (` `RIGHT_PAREN )` `LEFT_BRACE {` `RIGHT_BRACE }` `COMMA ,` `SEMICOLON ;` |
| Operators | `PLUS +` `MINUS -` `STAR *` `SLASH /` `PERCENT %` `BANG !` `BANG_EQUAL !=` `EQUAL =` `EQUAL_EQUAL ==` `LESS <` `LESS_EQUAL <=` `GREATER >` `GREATER_EQUAL >=` |
| `NUMBER` | digits, optionally followed by `.` and more digits: `0`, `007`, `3.14`. Not `.5` or `5.` |
| `STRING` | `"..."` on one line. Escapes: `\n` `\t` `\"` `\\`. Any other escape is an error. |
| `IDENTIFIER` | a letter or `_`, then letters, digits or `_` |
| Keywords | `LET` `FN` `IF` `ELSE` `WHILE` `RETURN` `PRINT` `TRUE` `FALSE` `NIL` `AND` `OR`, spelled as in your `language.json` |
| `EOF` | the end of the input |

Spaces, tabs, `\r` and newlines separate tokens. `//` starts a comment that runs to the end of the line. Any other character is a scan error. `--tokens` prints a token's lexeme exactly as written (a string with its quotes and escapes), and just the type for `EOF`.

## Grammar

```
program     → declaration* EOF
declaration → fnDecl | letDecl | statement
fnDecl      → FN IDENTIFIER "(" parameters? ")" block
parameters  → IDENTIFIER ( "," IDENTIFIER )*
letDecl     → LET IDENTIFIER ( "=" expression )? ";"
statement   → printStmt | ifStmt | whileStmt | returnStmt | block | exprStmt
printStmt   → PRINT expression ";"
ifStmt      → IF "(" expression ")" statement ( ELSE statement )?
whileStmt   → WHILE "(" expression ")" statement
returnStmt  → RETURN expression? ";"
block       → "{" declaration* "}"
exprStmt    → expression ";"
```

Expressions, from lowest precedence to highest:

| Precedence | Operators | Associativity |
| --- | --- | --- |
| Assignment | `=` | right |
| Or | `or` | left |
| And | `and` | left |
| Equality | `==` `!=` | left |
| Comparison | `<` `<=` `>` `>=` | left |
| Term | `+` `-` | left |
| Factor | `*` `/` `%` | left |
| Unary | `!` `-` (prefix) | right |
| Call | `f(args)` | left |
| Primary | numbers, strings, `true`, `false`, `nil`, names, `( expression )` | |

The target of `=` must be a plain variable name: `1 = 2`, `(a) = 2` and `a + b = 3` are compile errors. An `else` belongs to the nearest `if`. A call has at most 255 arguments, and a function at most 255 parameters.

## Values

| Type | Examples | Printed as |
| --- | --- | --- |
| nil | `nil` | your spelling of `nil` |
| boolean | `true`, `false` | your spellings |
| number | `3`, `2.5` | whole numbers with no decimal point (`3`, `-6`); others as the shortest text that reads back as the same double (`2.5`, `0.30000000000000004`) |
| string | `"hi"` | the text, without quotes |
| function | `fn add(a, b) {...}` | `<fn add>` |
| native function | `clock` | `<native fn>` |

Numbers are C `double`s. Strings are immutable.

**Truthiness:** `false` and `nil` are falsy. Everything else is truthy, including `0` and `""`.

## Operators

| Expression | Result | Runtime error if... |
| --- | --- | --- |
| `-a` | negation | `a` isn't a number |
| `!a` | `true` if `a` is falsy | never |
| `a + b` | sum of two numbers, or two strings joined | it's anything else |
| `a - b`, `a * b` | arithmetic | either isn't a number |
| `a / b` | division: `10 / 4` is `2.5` | either isn't a number, or `b` is 0 |
| `a % b` | remainder, with the sign of `a` (C's `fmod`): `7 % 3` is `1` | either isn't a number, or `b` is 0 |
| `<` `<=` `>` `>=` | comparison | either isn't a number |
| `a == b`, `a != b` | values of different types are never equal; strings are equal if their text is | never |
| `a and b` | `a` if it's falsy (without evaluating `b`), else `b` | never |
| `a or b` | `a` if it's truthy (without evaluating `b`), else `b` | never |
| `x = v` | sets `x`, and has the value `v` | `x` was never declared |

Operands are evaluated left to right.

## Variables and scope

- `let x = v;` declares a variable; `let x;` sets it to `nil`. At the top level it's a **global**; inside a block or function it's a **local**.
- Globals are looked up when the code runs, so a function can use a global declared after the function. Using or assigning a global that doesn't exist is a runtime error. Declaring a global that already exists replaces it.
- A block `{ ... }` makes a new scope. A local is visible from its declaration to the end of its block, and hides any variable with the same name outside the block.
- Reading a local in its own initializer is a compile error. A function can have at most 255 locals in scope at once (counting its parameters). More is a compile error.

## Functions

- `fn name(params) { body }` declares a function, as a variable called `name`. Functions are values: they can be stored, passed and returned.
- Calling with the wrong number of arguments is a runtime error. So is calling something that isn't a function.
- `return v;` returns `v`; `return;` or reaching the end returns `nil`. `return` outside a function is a compile error.
- Functions are **closures**: a function can use the variables of the functions around it, even after they've returned. Each call makes fresh variables, so two closures from two calls don't share them. Two closures from the same call do.
- At least 64 calls deep must work. Deeper recursion than your VM supports must be a runtime error whose message includes `Stack overflow`, never a crash.

**Native functions** (built in, defined as globals):

| Function | Returns | Runtime error if... |
| --- | --- | --- |
| `clock()` | seconds of processor time since the program started, as a number | |
| `len(s)` | the number of characters in the string `s` | `s` isn't a string |
| `str(v)` | `v` as a string, exactly as `print` would show it | |

## Limits your VM must handle

- Source files of any size, and names and strings of any length.
- At least 65,536 constants in one function's bytecode.
- Jumps over at least 65,535 bytes of bytecode. Code too big to jump over is a compile error, never wrong behaviour.
- Programs that make far more garbage than fits in memory (Module 08).

## Building

Your code goes in `src/`, as any number of `.c` and `.h` files. It must compile as C11 with no warnings under:

```sh
cc -std=c11 -Wall -Wextra -Wno-unused-parameter src/*.c -lm
```

both with `-g -fsanitize=address,undefined` and with `-O2 -DNDEBUG`. Compiled with `-DSTRESS_GC`, your VM must run a full garbage collection every time it allocates memory (Module 08).
