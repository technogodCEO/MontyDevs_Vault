# Module 02: Parsing Expressions

**Goal:** a recursive descent parser that turns the tokens of an expression into a tree, respecting precedence and grouping, with `--ast` to print the tree and clear syntax errors.

## Concepts

### Trees, not lists

Tokens are flat, but expressions aren't. `1 + 2 * 3` means "add 1 to the product of 2 and 3", which is a tree:

```
    +
   / \
  1   *
     / \
    2   3
```

This is an **abstract syntax tree** (AST). Every operator is a node, and its operands are its children. Once you have the tree, evaluating it (next module) is a simple recursion: work out the children, then apply the operator. All the hard questions, like what `-` binds to, are settled by the shape of the tree.

To print a tree on one line we'll use **S-expressions**: each node is `(operator child child)`. The tree above is `(+ 1 (* 2 3))`.

### Precedence and associativity

Two rules decide the shape:

- **Precedence**: which operators bind tighter. `*` binds tighter than `+`, so `1 + 2 * 3` is `(+ 1 (* 2 3))`.
- **Associativity**: which way operators of the *same* precedence group. Ours are all **left-associative**: `10 - 4 - 3` is `(- (- 10 4) 3)`, which is 3. Grouping the other way would give `(- 10 (- 4 3))`, which is 9.

### Grammar rules

A **grammar** writes down which sequences of tokens are valid, one rule per precedence level, lowest first:

```
expression → equality
equality   → comparison ( ( "!=" | "==" ) comparison )*
comparison → term ( ( "<" | "<=" | ">" | ">=" ) term )*
term       → factor ( ( "+" | "-" ) factor )*
factor     → unary ( ( "*" | "/" | "%" ) unary )*
unary      → ( "!" | "-" ) unary | primary
primary    → NUMBER | STRING | TRUE | FALSE | NIL | IDENTIFIER | "(" expression ")"
```

Read `term` as: "a factor, followed by any number of `+` or `-` signs, each followed by another factor". `( ... )*` means "zero or more times", and `|` means "or".

### Recursive descent

A **recursive descent** parser turns each grammar rule into a function. `term()` calls `factor()`, then loops while the next token is `+` or `-`, calling `factor()` again for each right-hand side and building a node from the left side so far and the new right side. Because the loop keeps folding the tree to the *left*, operators come out left-associative.

Lower-precedence rules call higher-precedence ones, so `*` gets grabbed deeper in the recursion than `+`, and ends up lower in the tree. Brackets work because `primary` calls all the way back up to `expression`.

## Practice

Warm up on this module's ideas before you use them in your interpreter.

### Think it through

**1. Draw the tree.** Write the S-expression for each:

```
-2 * 3
1 < 2 == true
!(a == b)
```

<details><summary>Answer</summary>

- `(* (- 2) 3)`: unary minus binds tighter than `*`.
- `(== (< 1 2) true)`: comparison binds tighter than equality.
- `(! (group (== a b)))`: brackets make a `group` node (see the spec below).

</details>

**2. What's wrong with this rule?** Someone writes `term` like this. What does `10 - 4 - 3` parse as, and why?

```python
def term(self):
    left = self.factor()
    if self.match("PLUS", "MINUS"):
        operator = self.previous()
        right = self.term()     # recursion, instead of a loop
        return Binary(left, operator, right)
    return left
```

<details><summary>Answer</summary>

`(- 10 (- 4 3))`, which is 9. Calling `term()` again for the right side makes everything to the right into one subtree, so the operators group to the right. A `while` loop that keeps updating `left = Binary(left, operator, right)` makes them group to the left. Practice problem 3 is this same bug.

</details>

### Try it in code

[`practice_02.py`](practice_02.py): checking brackets, a calculator that's a tiny recursive descent parser, an associativity bug, and printing a tree as an S-expression.

Copy it into your project folder, fill it in, and run `python check.py practice 2`.

<details><summary>Hints</summary>

- `balanced`: push each opening bracket onto a list, and pop when you see a closing one. What should happen if the list is empty when you pop, or not empty at the end?
- `calculate`: first split the text into numbers and symbols (like `split_tokens` from Module 01). Then write `expr()`, `term()` and `factor()` functions that share a position, following the grammar above with `+ -` and `* /`. `factor()` handles a number or a bracketed `expr()`.
- `calc`: replace the recursion with a loop that keeps a running total.
- `to_sexpr`: a tuple becomes `"(" + operator + each child's S-expression + ")"`, joined with spaces. Anything else is `str(tree)`. It's recursive.

</details>

## Steps

Continue in your interpreter from Module 01.

### 1. The grammar

Parse exactly the grammar above. (Later modules will add rules above `equality` and below `unary`, without changing these.) `IDENTIFIER` is a variable name, like `x`. It can't be evaluated until Module 04, but it can be parsed now.

Here's the parser's skeleton, with two of the precedence levels written out. Every other binary level follows the same pattern:

```python
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current = 0

    # --- Grammar rules: one method each ---
    def term(self):
        expr = self.factor()                     # the left side: a higher-precedence rule
        while self.match("PLUS", "MINUS"):
            operator = self.previous()           # the token match() just consumed
            right = self.factor()
            expr = Binary(expr, operator, right) # fold to the LEFT: left-associative
        return expr

    def factor(self):
        expr = self.unary()
        while self.match("STAR", "SLASH", "PERCENT"):
            operator = self.previous()
            right = self.unary()
            expr = Binary(expr, operator, right)
        return expr

    # --- Helpers every rule uses ---
    def peek(self):
        return self.tokens[self.current]

    def previous(self):
        return self.tokens[self.current - 1]

    def check(self, *types):
        return self.peek().type in types

    def match(self, *types):
        if self.check(*types):
            self.current += 1
            return True
        return False
```

Notice the `while` loop: it's what makes `10 - 4 - 3` group as `(- (- 10 4) 3)`. You write `expression`, `equality`, `comparison`, `unary` and `primary`, plus the node classes.

### 2. `--ast`

`python glim.py --ast expression.glim` parses the **whole file as one expression** (comments and whitespace are fine) and prints its tree as one S-expression:

| Node | Printed as | Example |
| --- | --- | --- |
| Number | its value, with no `.0` on whole numbers | `2.50` prints `2.5`, `10.0` prints `10` |
| String | exactly as written in the source, quotes included | `"hi"` |
| `true`, `false`, `nil`, a variable | the token's lexeme | `true`, `x` |
| Brackets | `(group inner)` | `(group (+ 1 2))` |
| Unary | `(operator operand)` | `(- 5)`, `(! x)` |
| Binary | `(operator left right)` | `(+ 1 (* 2 3))` |

Operators print as their lexeme (`-`, `==`, `<=`). Separate the parts with single spaces.

`--ast` will always parse a single expression, even after your language has statements, so it stays a handy tool for checking precedence.

### 3. Syntax errors

If the tokens don't fit the grammar, or there are tokens left over after the expression, that's a **syntax error**. Print a message to stderr that includes `line N` (the line of the token where the problem was found: for a missing `)` at the end of the file, the line of `EOF`) and exit with code **65**, the same as scan errors.

Examples: `1 +`, `(1 + 2`, `1 2`, `* 3`, `()`.

### 4. Your turn: design decisions

- **How will you represent tree nodes?** Classes per node type (`Binary`, `Unary`, `Literal`, `Grouping`, `Variable`) are clear and easy to extend. Python's [`dataclasses`](https://docs.python.org/3/library/dataclasses.html) make them short. Tuples like `("binary", op, left, right)` are quicker to write and harder to read later. Your call.
- **Where does printing live?** A function `to_sexpr(node)` outside the classes, or a method on each class. Next module, you'll write an evaluator with the same shape, so think about which way you'd rather have twice.
- Keep the operator **token** in each node, not just its symbol. Its line number is what makes good runtime error messages possible in Module 03.

## Make it yours

- **Make syntax errors helpful.** "Expected ')' after expression" beats "Syntax error". Include what was found: `Expected an expression, but found '*'`.
- **Add a pretty-printer** behind your own flag (say `--tree`), drawing the tree sideways with indentation. Leave `--ast` exactly as specified.

## Check your work

```sh
python check.py 2
```

The checker runs `--ast` on expressions chosen to catch precedence and associativity mistakes, then checks that broken expressions give syntax errors.

## Stuck?

- **`RecursionError`**: a rule calls itself without consuming a token first. `unary` can call `unary` only *after* matching `!` or `-`.
- **`1 2` parses without an error**: after parsing the expression, check that the next token is `EOF`.
- **Numbers print as `10.0`**: print the value without the `.0` for whole numbers (`value.is_integer()` tells you), and as Python would print it otherwise.
- **`-x * y` comes out as `(- (* x y))`**: `unary` should parse only one `primary` (or another `unary`) as its operand, not a whole `factor`.

<details><summary>Hint 1: unary is the one rule that recurses on itself</summary>

`unary` doesn't loop. If it matches `!` or `-`, it remembers the operator and calls `unary()` again for the operand (so `!!x` and `- -1` work), and builds a `Unary` node. Otherwise it returns `primary()`. Because it matched a token first, the recursion always makes progress.

</details>

<details><summary>Hint 2: one helper for four rules</summary>

`equality`, `comparison`, `term` and `factor` differ only in the token types and the next rule. A helper `binary(next_rule, *types)` that runs the `while` loop from the skeleton lets each of them be one line: `return self.binary(self.factor, "PLUS", "MINUS")`.

</details>

<details><summary>Hint 3: primary and errors</summary>

In `primary`: if the token is a `NUMBER` or `STRING`, return a literal with its value. If it's `TRUE`, `FALSE` or `NIL`, a literal of `True`, `False` or `None`. If it's an `IDENTIFIER`, a variable node. If it's `(`, parse an `expression()`, then require a `)`. Otherwise raise a parse error with `peek().line`. A helper `expect(type, message)` (advance if the type matches, otherwise raise) handles every "required token" in the grammar.

</details>

## Resources

- [*Crafting Interpreters*, chapter 5: Representing Code](https://craftinginterpreters.com/representing-code.html): how to think about grammars and syntax trees. Skip the Java code generation. Take the grammar notation and the "printing a tree" idea.
- [*Crafting Interpreters*, chapter 6: Parsing Expressions](https://craftinginterpreters.com/parsing-expressions.html): recursive descent, rule by rule. Our grammar adds `%` and leaves out Lox's comma operator. Its section on error recovery is optional for now.
- [Python docs: operator precedence](https://docs.python.org/3/reference/expressions.html#operator-precedence): Python's own precedence table. Compare it with ours.
- [Pratt Parsers: Expression Parsing Made Easy](https://journal.stuffwithstuff.com/2011/03/19/pratt-parsers-expression-parsing-made-easy/): another way to parse expressions, driven by a table of precedences. Worth reading once your parser works.

## Challenges (optional)

- Add the exponent operator `**`. It's **right**-associative and binds tighter than unary minus: `2 ** 3 ** 2` is 512, and `-2 ** 2` is -4.
- Add the ternary operator `condition ? a : b`, with the lowest precedence.
- After a syntax error, skip ahead and keep parsing, so you can report several errors at once.

## Next

Continue to [Module 03: Evaluating Expressions](../03-evaluating-expressions/).
