# Module 04: Variables and Scope

**Goal:** variables you can declare with `let`, change with `=`, and nest in blocks `{ }`, with inner variables hiding outer ones and disappearing when their block ends.

## Concepts

### Environments

A variable is a name bound to a value. An **environment** is the dictionary that holds those bindings: `{"total": 12.0, "name": "Ana"}`. Declaring a variable adds a key, reading it looks the key up, and assigning changes its value.

### Scope, and environments in a chain

Blocks make new **scopes**:

```
let a = "global";
{
  let a = "inner";
  print a;        // inner
}
print a;          // global
```

Each block gets its own environment, which points to the environment around it: its **parent**. Looking a name up searches the current environment, then its parent, then *its* parent, up to the global environment at the end of the chain. The first match wins, so an inner `a` **shadows** an outer one. When the block ends, the interpreter goes back to the parent, and the inner environment, with everything declared in it, is gone.

```
global:  { a: "global" }
   ↑ parent
block:   { a: "inner" }      ← current environment while inside the block
```

This is **lexical scope**: you can tell which variable a name refers to just by reading the code, by looking outward through the braces.

### Declaring versus assigning

`let x = 1;` *creates* a variable in the current scope. `x = 2;` *changes* the nearest existing `x`, wherever in the chain it lives. Assigning to a name that was never declared is an error. That catches typos that would otherwise silently create a new variable.

### Assignment is an expression

`x = 2` produces a value: the value assigned. So `a = b = 3` sets both, and `print c = 5;` prints `5`. It's the lowest-precedence expression, and right-associative: `a = b = 3` is `a = (b = 3)`.

Parsing it has a twist. When the parser reaches `=`, it has *already* parsed the left side as an expression. It then checks that the left side is a plain variable. `1 = 2` and `(a) = 2` are syntax errors.

## Practice

Warm up on this module's ideas before you use them in your interpreter.

### Think it through

**1. Predict the output.**

```
let x = 1;
{
  x = x + 1;
  let x = 10;
  x = x + 1;
  print x;
}
print x;
```

<details><summary>Answer</summary>

```
11
2
```

The first `x = x + 1` runs before the inner `x` exists, so it changes the global `x` to 2. Then `let x = 10` declares a new `x` in the block. The second assignment changes *that* one to 11. When the block ends, the global `x` is still 2.

</details>

**2. Spot the problem.** This interpreter runs blocks like this. What goes wrong if a runtime error happens inside a block in the REPL, and the next line typed uses a global variable?

```python
def run_block(self, statements, environment):
    previous = self.environment
    self.environment = environment
    for statement in statements:
        self.execute(statement)
    self.environment = previous
```

<details><summary>Answer</summary>

If a statement raises an error, the last line never runs, so the interpreter stays in the block's environment. In the REPL, the next line would run inside a scope that should have ended. Wrap the loop in `try`/`finally` so the environment is always restored. Functions in Module 06 will need this too, because `return` will jump out of blocks.

</details>

### Try it in code

[`practice_04.py`](practice_04.py): an `Environment` class with `define`, `get` and `assign`, and a shadowing bug.

Copy it into your project folder, fill it in, and run `python check.py practice 4`.

<details><summary>Hints</summary>

- `get` and `assign` follow the same pattern: if the name is in `self.values`, use it here. Otherwise, if there's a parent, ask the parent. Otherwise raise `NameError`. A loop or recursion both work.
- `lookup`: which scope should be searched *first*? `reversed()` might help.

</details>

## Steps

Continue in your interpreter from Module 03.

### 1. Grammar

```
program     → declaration* EOF
declaration → letDecl | statement
letDecl     → LET IDENTIFIER ( "=" expression )? ";"
statement   → printStmt | block | exprStmt
block       → "{" declaration* "}"

expression  → assignment
assignment  → IDENTIFIER "=" assignment | equality
```

The rules from `equality` down are unchanged from Module 02.

### 2. Behaviour

- `let name = value;` evaluates the value, then defines `name` in the **current** scope. `let name;` defines it as `nil`. Declaring a name that already exists in the same scope just replaces it.
- A variable expression evaluates to the value from the nearest scope that has the name. If no scope has it: runtime error, "undefined variable", on the name's line.
- `name = value` evaluates the value, changes the nearest existing `name`, and evaluates to the value. If no scope has the name: runtime error.
- A block runs its declarations in a **new** scope whose parent is the current one. The scope ends when the block does.
- `--ast` shows assignment as `(= name value)`: `a = b = 1` prints `(= a (= b 1))`.

### 3. Errors

| Program | Error |
| --- | --- |
| `print y;` (never declared) | runtime, exit 70 |
| `z = 1;` (never declared) | runtime, exit 70 |
| `{ let inner = 1; } print inner;` | runtime, exit 70: `inner` ended with its block |
| `let = 3;`, `let 1x = 2;` | syntax, exit 65 |
| `1 = 2;`, `(a) = 2;` | syntax, exit 65: "invalid assignment target" |
| `{ print 1;` with no `}` | syntax, exit 65 |

### 4. The REPL keeps its variables

Use one interpreter (and one global environment) for the whole REPL session, so a variable declared on one line can be used on the next.

### 5. Your turn: design decisions

- **What does your `Environment` class look like?** Here's the skeleton. The bodies are the practice file's job, and then yours:

  ```python
  class Environment:
      def __init__(self, parent=None):
          self.values = {}        # the names declared in THIS scope
          self.parent = parent    # the scope around this one (None for globals)

      def define(self, name, value):
          # Always in this scope: that's what makes shadowing work.
          ...

      def get(self, name_token):
          # This scope, then the parent, then ITS parent... or a runtime error.
          ...

      def assign(self, name_token, value):
          # Change the nearest existing variable. Never create one.
          ...
  ```

  Passing the whole name *token* to `get` and `assign`, rather than the name, gives them the line number for the error.
- **How does the interpreter know the current environment?** Most interpreters keep `self.environment` and swap it while running a block.
- **Should `let x = x;` see the outer `x`?** With the order in the spec (evaluate, then define) it does. *Crafting Interpreters* makes it an error inside blocks. Both are reasonable. Ours is simpler.

## Make it yours

- **Constants**: add a second declaration keyword (say `const`) for variables that can't be reassigned, with a runtime error if someone tries. (The self-check only allows the twelve types from the spec in `language.json`, so keep the new keyword in your own code, in a separate dictionary.)
- **"Did you mean...?"**: when a variable is undefined, suggest a similar name that does exist. Python's `difflib.get_close_matches` does the hard part.

## Check your work

```sh
python check.py 4
```

## Stuck?

- **Variables from a block are still there after it ends**: you defined them in the parent environment, or never created a new one for the block.
- **Assigning inside a block creates a new variable**: assignment must search up the chain and change the existing variable, never `define`.
- **`a = b = 3` is a syntax error**: in `assignment`, after the `=`, call `assignment()` again (not `equality()`) for the value.
- **After an error in the REPL, variables seem to vanish or come back**: restore the environment in a `finally` block (see question 2 above).

<details><summary>Hint 1: parsing assignment</summary>

Parse the left side as an ordinary expression first. If the next token is `=`, then parse the value, and check what you got on the left.

</details>

<details><summary>Hint 2: almost the whole rule</summary>

```python
def assignment(self):
    expr = self.equality()
    if self.match("EQUAL"):
        equals = self.previous()
        value = self.assignment()
        if isinstance(expr, Variable):
            return Assign(expr.name, value)
        raise ParseError(equals.line, "Invalid assignment target.")
    return expr
```

</details>

<details><summary>Hint 3: running a block</summary>

When you see a `Block` statement, call `run_block(block.statements, Environment(self.environment))`, with the `try`/`finally` from question 2 inside `run_block`.

</details>

## Resources

- [*Crafting Interpreters*, chapter 8: Statements and State](https://craftinginterpreters.com/statements-and-state.html): global variables, assignment, and block scope with nested environments. Our spec is the same in spirit, without Lox's `var` keyword.
- [Wikipedia: Scope (computer science)](https://en.wikipedia.org/wiki/Scope_(computer_science)): lexical versus dynamic scope, with examples in several languages.

## Challenges (optional)

- Compound assignment: `x += 1`, `x -= 2`, and so on.
- Make it a syntax error to use a variable in its own initializer inside a block (`{ let a = a; }`), as Lox does.
- A `--trace` flag that prints each variable assignment as it happens, to stderr.

## Next

Continue to [Module 05: Control Flow](../05-control-flow/).
