# Module 03: Evaluating Expressions

**Goal:** your language runs programs. It evaluates expressions to values, runs `print` statements, and reports runtime errors with line numbers. The REPL runs code too.

## Concepts

### A tree-walking interpreter

To **evaluate** a node, evaluate its children, then combine them. A `Binary` node for `+` evaluates its left side, then its right side, then adds them. A `Literal` just returns its value. That's a recursive function over the tree, and it's the whole idea behind a **tree-walking interpreter**.

### Your values, in Python

Each value in your language needs a Python value to stand for it. The simplest choice is to reuse Python's:

| Your language | Python |
| --- | --- |
| `nil` | `None` |
| `true`, `false` | `True`, `False` |
| numbers | `float` |
| strings | `str` |

But your language's *rules* aren't Python's, and that's where the bugs hide:

- **Truthiness.** In your language only `false` and `nil` are falsy. `0` and `""` are **truthy**, unlike in Python. So never write `if value:` in your interpreter. Write a `truthy(value)` function and use it everywhere.
- **Equality.** In Python, `1.0 == True` is `True`. In your language, values of different types are never equal, so `1 == true` is `false`.
- **Printing.** Python prints `3.0`. Your language prints `3`. Python prints `None`. Your language prints `nil`.

### Statements and expressions

An **expression** produces a value (`1 + 2`). A **statement** does something (`print 1 + 2;`). From this module on, a program is a list of statements, each ending with `;`, run in order:

```
program    → statement* EOF
statement  → printStmt | exprStmt
printStmt  → PRINT expression ";"
exprStmt   → expression ";"
```

An expression statement evaluates the expression and throws the value away. That seems pointless now, but it's how function calls and assignments will run later.

### Two kinds of errors

- A **syntax error** is found while parsing, *before* anything runs: exit code 65, and none of the program runs.
- A **runtime error** is found while running: `1 + "a"`, or dividing by zero. Everything printed before it stays printed. Exit code 70.

Both come with a line number, which is why your nodes keep their operator tokens.

## Practice

Warm up on this module's ideas before you use them in your interpreter.

### Think it through

**1. Predict the output** of this program in your language:

```
print !0;
print 1 == true;
print 10 / 4;
print "3" + "4";
print 2 * 3 == 6;
```

<details><summary>Answer</summary>

```
false
false
2.5
34
true
```

`0` is truthy, so `!0` is `false`. A number never equals a boolean. Division gives a float, printed as `2.5`. `+` on two strings joins them. `*` binds tighter than `==`.

</details>

**2. Spot the problem.** What goes wrong in this evaluator for `print nil == false;`, and for `print !0;`?

```python
if op.type == "EQUAL_EQUAL":
    return left == right
if op.type == "BANG":
    return not right
```

<details><summary>Answer</summary>

`nil == false` is fine by luck: Python's `None == False` is `False`. But `0.0 == False` is `True` in Python, so `0 == false` would print `true`. And `not 0.0` is `True` in Python, so `!0` would print `true` instead of `false`. Both need your language's rules: type-aware equality, and `not truthy(right)`.

</details>

### Try it in code

[`practice_03.py`](practice_03.py): truthiness, turning values into text, a small tree evaluator, and an equality bug.

Copy it into your project folder, fill it in, and run `python check.py practice 3`.

<details><summary>Hints</summary>

- `truthy`: compare with `is`, not `==`. `value is False` is only true for `False` itself, not for `0`.
- `stringify`: check `None`, `True` and `False` **before** checking for numbers. In Python, `isinstance(True, int)` is `True`.
- `evaluate`: look at `node[0]`, evaluate the children with `evaluate()`, and combine. A dictionary from names to functions is one tidy way.
- `equal`: two values are equal only if they're the same type *and* equal. `type(a) is type(b)` checks the first.

</details>

## Steps

Continue in your interpreter from Module 02. `--tokens` and `--ast` keep working as before.

### 1. Running a file

`python glim.py program.glim` now **runs** the program instead of printing it back:

1. Scan and parse the whole file into a list of statements. If there's a scan or syntax error, report it and exit with code 65 before running anything.
2. Run the statements in order.
3. If a runtime error happens, stop, print a message including `line N` to stderr, and exit with code **70**. Output printed before the error must still appear.

An empty file is a valid program that does nothing.

### 2. Evaluation rules

| Expression | Rule | Runtime error if... |
| --- | --- | --- |
| `-a` | negation | `a` isn't a number |
| `!a` | `true` if `a` is falsy, else `false` | never |
| `a + b` | add two numbers, or join two strings | it's anything else, like a number and a string |
| `a - b`, `a * b` | arithmetic | either isn't a number |
| `a / b` | division, always a float: `10 / 4` is `2.5` | either isn't a number, or `b` is 0 |
| `a % b` | remainder: `7 % 3` is `1` | either isn't a number, or `b` is 0 |
| `<` `<=` `>` `>=` | compare two numbers | either isn't a number |
| `a == b`, `a != b` | equal if same type and same value | never |
| `(a)` | the value of `a` | never |

Evaluate the left operand before the right. The line in a runtime error is the operator's line.

### 3. Printing values

`print` writes a value's text, then a newline:

| Value | Printed as |
| --- | --- |
| `nil`, `true`, `false` | your spelling of the keyword |
| a whole number | no decimal point: `3`, `-6`, `12345678` |
| any other number | as Python shows it: `2.5`, `0.25` |
| a string | its text, without quotes |

### 4. The REPL

Running with no file now runs each line you type as a program. If a line has an error, report it and **keep going**: one typo shouldn't end the session. Stop with exit code 0 when the input ends.

### 5. Your turn: design decisions

- **How will your evaluator choose what to do for each node?** One big `if`/`elif` on the node type, a method on each node class (`node.evaluate()`), a dictionary from node type to function, or the **visitor pattern** from *Crafting Interpreters*. Pick one and stick with it.
- **How will a runtime error reach `main()`?** A `RuntimeError`-style exception carrying the token is a good fit. (Python already has a class called `RuntimeError`, so give yours a different name.)
- **Where does the line between the parser and the interpreter go?** The parser shouldn't print anything or run anything. It hands back statements, and the interpreter runs them.

## Make it yours

- **Error messages with context**: `Can't add a number and a string.` is better than `Operands must be two numbers or two strings.` Show the types involved.
- **A REPL that's nice to use**: a welcome banner with your language's name, or printing the value of a bare expression like `1 + 2` (without needing `print`) when typed into the REPL.
- **Decide what `"ab" * 3` does.** The spec says it's a runtime error. That's what the checker tests, so keep the error, but you could suggest the fix in the message.

## Check your work

```sh
python check.py 3
```

The checker runs programs and compares their output, checks that runtime errors keep earlier output and give the right line, and that syntax errors stop the program before anything runs.

## Stuck?

- **`print 1 == true;` prints `true`**: Python's `1.0 == True` is `True`. Check the types first.
- **`print !0;` prints `true`**: you used Python's truthiness. Use your `truthy()`.
- **`print true;` prints `1`, or `print 3;` prints `true`**: in `stringify`, check for `True`/`False` before numbers. `isinstance(True, (int, float))` is true in Python.
- **The output before a runtime error is missing**: are you collecting output and only printing at the end? Print as you go. (If you buffer anything yourself, flush before exiting.)
- **A syntax error on line 2 still prints line 1's output**: parse the *whole* program into statements first, then run them.

<details><summary>Hint 1: the evaluator's shape</summary>

```python
def evaluate(self, node):
    if isinstance(node, Literal):
        return node.value
    if isinstance(node, Grouping):
        return self.evaluate(node.inner)
    if isinstance(node, Unary):
        right = self.evaluate(node.operand)
        ...
    if isinstance(node, Binary):
        left = self.evaluate(node.left)
        right = self.evaluate(node.right)
        ...
```

Change the names to match your node classes.

</details>

<details><summary>Hint 2: checking operand types</summary>

A helper like `number_operands(operator, left, right)` that raises your runtime error (with `operator.line`) unless both are floats keeps the arithmetic short. Note that `isinstance(True, float)` is `False`, so booleans won't sneak through, but check for `bool` explicitly if you ever store numbers as `int`.

</details>

<details><summary>Hint 3: exit codes in main()</summary>

```python
try:
    statements = parse(scan(source))
except YourSyntaxError as error:
    print(error, file=sys.stderr)
    sys.exit(65)
try:
    interpreter.run(statements)
except YourRuntimeError as error:
    print(error, file=sys.stderr)
    sys.exit(70)
```

Use the same `try` blocks in the REPL, but print the error and carry on instead of exiting.

</details>

## Resources

- [*Crafting Interpreters*, chapter 7: Evaluating Expressions](https://craftinginterpreters.com/evaluating-expressions.html): values, truthiness, equality and runtime errors. Our rules differ in places (division by zero is an error here, and we have `%`), so follow the table above.
- [*Crafting Interpreters*, chapter 8: Statements and State](https://craftinginterpreters.com/statements-and-state.html): read the first part, on statements, now. The rest is Module 04.
- [Wikipedia: Read–eval–print loop](https://en.wikipedia.org/wiki/Read%E2%80%93eval%E2%80%93print_loop): where REPLs came from, and why every serious language has one.

## Challenges (optional)

- Let `+` join a string with a number (`"score: " + 10`), and decide how the number is printed. (This changes the spec, so do it on a branch, and expect check 3 to complain.)
- Add a `--time` flag that prints how long the program took to run, to stderr.
- Show the source line under each error message, with a `^` under the operator.

## Next

Continue to [Module 04: Variables and Scope](../04-variables-and-scope/).
