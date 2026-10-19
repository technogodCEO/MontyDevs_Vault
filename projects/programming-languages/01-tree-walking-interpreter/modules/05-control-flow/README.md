# Module 05: Control Flow

**Goal:** programs that make decisions and repeat: `if`/`else`, `while` loops, and the short-circuiting `and` and `or`.

## Concepts

### Branches and loops are just evaluation choices

An `if` statement evaluates its condition, then executes *one* of its branches. A `while` loop evaluates its condition, runs its body, and goes round again. In your interpreter, each is only a few lines, built on Python's own `if` and `while`, plus your `truthy()`.

Once you have `while`, your language is **Turing complete**: given enough time and memory, it can compute anything any language can. Everything after this is about making programs easier to *write*.

### Short-circuit evaluation

`and` and `or` don't always evaluate their right side:

- `a and b`: if `a` is falsy, the answer is `a`, and `b` is never evaluated.
- `a or b`: if `a` is truthy, the answer is `a`, and `b` is never evaluated.

This matters when `b` has an effect, like an assignment or (next module) a function call. It also means they're really control flow, not arithmetic.

Notice they return one of the **operands**, not `true` or `false`. So `nil or "default"` is `"default"`, a handy way to fill in a missing value.

### Precedence and the dangling else

`or` binds more loosely than `and`, which binds more loosely than `==`. So `a or b and c` is `a or (b and c)`, and `x == 1 or y` compares first.

```
if (first) if (second) print "a"; else print "b";
```

Which `if` does the `else` belong to? The rule (in almost every language) is the **nearest** one. A recursive descent parser gets this for free: the inner `if` sees the `else` first, and takes it.

## Practice

Warm up on this module's ideas before you use them in your interpreter.

### Think it through

**1. Predict the output.**

```
print nil or "fallback";
print 0 and "zero is truthy";
print false and undefined_variable;
print true or false and false;
```

<details><summary>Answer</summary>

```
fallback
zero is truthy
false
true
```

The third line never evaluates `undefined_variable`, so there's no error. The last one is `true or (false and false)`, because `and` binds tighter, and `true or ...` stops straight away.

</details>

**2. What does this print**, and what would it print if `and` were evaluated like `+` (both sides first)?

```
let count = 0;
false and (count = count + 1);
print count;
```

<details><summary>Answer</summary>

`0`. The right side is never evaluated. If both sides were evaluated first, the assignment would run and it would print `1`, even though the result of the `and` is `false` either way.

</details>

### Try it in code

[`practice_05.py`](practice_05.py): short-circuit `and_`/`or_` using functions for the right-hand side, a `while` loop runner, and a truthiness bug in an `if`.

Copy it into your project folder, fill it in, and run `python check.py practice 5`.

<details><summary>Hints</summary>

- `and_` and `or_`: each is one line with a conditional expression. The right side is a function, so `right()` is what evaluates it. Only call it in the branch that needs it.
- `run_while` and `run_if`: Python's `while` and `if` use Python's truthiness. Wrap the condition in your language's rule.

</details>

## Steps

Continue in your interpreter from Module 04.

### 1. Grammar

```
statement  → printStmt | ifStmt | whileStmt | block | exprStmt
ifStmt     → IF "(" expression ")" statement ( ELSE statement )?
whileStmt  → WHILE "(" expression ")" statement

assignment → IDENTIFIER "=" assignment | logic_or
logic_or   → logic_and ( OR logic_and )*
logic_and  → equality ( AND equality )*
```

The brackets around the condition are required. A branch or loop body is one statement, usually a block. An `else` belongs to the nearest `if`.

### 2. Behaviour

- `if`: evaluate the condition. If it's truthy, execute the first branch. Otherwise, execute the `else` branch if there is one.
- `while`: while the condition is truthy, execute the body.
- `a and b`: evaluate `a`. If it's falsy, the result is `a`. Otherwise the result is `b`.
- `a or b`: evaluate `a`. If it's truthy, the result is `a`. Otherwise the result is `b`.
- `--ast` shows them like the other binary operators, with their lexemes: `a or b and c` prints `(or a (and b c))`, using your spellings.

### 3. Errors

Missing brackets around a condition, or an `else` with no statement after it, are syntax errors (65). Errors inside loops are reported with the line they happen on, after all the output from earlier iterations.

### 4. Your turn: design decisions

- **New node types or reuse `Binary`?** `and`/`or` evaluate differently from every other binary operator, so a separate `Logical` node keeps the evaluator honest.
- **How does your parser handle `else if`?** You don't need a rule for it: `else` followed by an `if` statement already works. Check that it does.

## Make it yours

- Write a few real programs in your language: FizzBuzz, a times table, a number guessing game (once you have `input`, in a challenge), the [Collatz sequence](https://en.wikipedia.org/wiki/Collatz_conjecture). Keep them in an `examples/` folder. They make great tests, and a great README later.
- Make an infinite loop easy to stop: catch `KeyboardInterrupt` (Ctrl+C) and print a friendly message instead of a Python traceback.

## Check your work

```sh
python check.py 5
```

## Stuck?

- **`print nil or "x";` prints `true`**: return the operand itself, not `truthy(...)` of it.
- **`if (0)` takes the `else` branch**: you used Python's `if condition:`. Use `if truthy(condition):`.
- **`print true or false and false;` prints `false`**: `and` must bind tighter. `logic_or` calls `logic_and`, which calls `equality`.
- **A `while` loop never ends**: is the condition re-evaluated each time round? Evaluate it *inside* the Python loop, not once before it.

<details><summary>Hint 1: executing if and while</summary>

`if` is three lines in your interpreter: evaluate the condition, then execute `then_branch` or (if it isn't `None`) `else_branch`. `while` is two: `while truthy(self.evaluate(stmt.condition)):` then execute the body.

</details>

<details><summary>Hint 2: evaluating and/or</summary>

```python
left = self.evaluate(node.left)
if node.operator.type == "OR":
    if truthy(left):
        return left
else:   # AND
    if not truthy(left):
        return left
return self.evaluate(node.right)
```

</details>

<details><summary>Hint 3: parsing if</summary>

After matching `IF`: expect `(`, parse an expression, expect `)`, parse a `statement()` for the branch, then, if you can `match("ELSE")`, parse another `statement()`. Because the inner `statement()` call runs first, it claims any `else` that follows, which settles the dangling else.

</details>

## Resources

- [*Crafting Interpreters*, chapter 9: Control Flow](https://craftinginterpreters.com/control-flow.html): `if`, `while`, logical operators and the dangling else. It also builds `for` out of `while` (desugaring), which is the first challenge below.
- [Wikipedia: Short-circuit evaluation](https://en.wikipedia.org/wiki/Short-circuit_evaluation): how other languages handle `and`/`or`, and the idioms that depend on it.

## Challenges (optional)

- A `for (init; condition; step) body` loop, turned into a `while` inside a block by the parser, so the interpreter doesn't change at all. (Add your own keyword for it in your code, outside `language.json`, as with `const` in Module 04.)
- `break` and `continue`. Python exceptions are one way to jump out of a loop from deep inside its body.
- A `--steps` flag that counts how many statements a program executed. Compare a loop to the same work done another way.

## Next

Continue to [Module 06: Functions](../06-functions/).
