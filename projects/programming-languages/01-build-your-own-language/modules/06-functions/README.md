# Module 06: Functions

**Goal:** functions you can declare, call, pass around and return, with recursion, closures, and a few built-in functions. After this, your language is a real one.

## Concepts

### Calls are just another expression

`add(1, 2)` is an expression: a **callee** (here the variable `add`) followed by arguments in brackets. A call binds tighter than anything else, even unary minus, and calls can chain: `adder(2)(3)` calls `adder(2)`, then calls whatever that returns with `3`. The callee doesn't have to be a name. It's any expression that evaluates to something callable.

### Functions are values

`fn add(a, b) { ... }` creates a **function value** and stores it in a variable called `add`, just as `let` would. That means functions can be passed to other functions, returned from them, and stored in variables: they're **first-class**.

A function value needs to remember two things: its **declaration** (parameters and body), and the **environment it was declared in**.

### Calling a function

To call a function:

1. Evaluate the callee, then the arguments, left to right.
2. Check the callee is a function, and that the number of arguments matches its parameters (its **arity**).
3. Make a **new environment** whose parent is the function's *saved* environment, and define each parameter in it with its argument.
4. Run the body in that environment.
5. The call's value is whatever `return` gave, or `nil` if the body finished without one.

### Closures

Step 3 says the parent is the environment where the function was **declared**, not where it's called. That one choice gives you **closures**:

```
fn makeCounter() {
  let count = 0;
  fn counter() {
    count = count + 1;
    return count;
  }
  return counter;
}
let tick = makeCounter();
print tick();   // 1
print tick();   // 2
```

`makeCounter` has returned, but `counter` still holds on to the environment with `count` in it. Each call to `makeCounter` makes a fresh environment, so each counter has its own `count`.

### Return jumps out

`return` can sit deep inside loops and blocks, and must leave all of them at once. In a tree-walking interpreter the neatest way is to **raise a Python exception** carrying the value, and catch it where the function was called. (The `finally` you added to `run_block` in Module 04 makes sure every environment is restored on the way out.)

### Built-in functions

Some functions can't be written in your language itself, like reading the clock. **Native** functions are Python functions wrapped up to look like your language's functions, defined in the global environment before the program starts.

## Practice

Warm up on this module's ideas before you use them in your interpreter.

### Think it through

**1. Predict the output.**

```
let x = "global";
fn show() {
  print x;
}
fn test() {
  let x = "local";
  show();
}
test();
```

<details><summary>Answer</summary>

`global`. `show` was declared at the top level, so its environment's parent is the global one. Where it's *called* from doesn't matter. That's lexical scope. (A language where this printed `local` would have *dynamic* scope.)

</details>

**2. How deep does Python go?** Each call in your language makes several nested Python calls in your interpreter (`execute`, `evaluate`, `call`, ...). Python stops with a `RecursionError` at about 1000 nested calls by default. What happens if a program in your language recurses 300 levels deep?

<details><summary>Answer</summary>

It probably crashes with a Python `RecursionError`, even though 300 is a small number, because each level of *your* language uses several levels of Python. You can raise the limit with `sys.setrecursionlimit(10000)` at the start of `main()`, and catching `RecursionError` to report a friendly "stack overflow" runtime error is even better. The self-check stays well within the default limit.

</details>

### Try it in code

[`practice_06.py`](practice_06.py): closures in Python itself, composing functions, the famous loop-closure bug, and checking arity.

Copy it into your project folder, fill it in, and run `python check.py practice 6`.

<details><summary>Hints</summary>

- `make_counter`: define a function inside `make_counter` that changes a variable from the outer function. Python needs `nonlocal` to assign to it.
- `compose`: return a new function (`def` or `lambda`) that calls `g`, then `f`.
- `make_adders`: every lambda looks up `i` when it's *called*, after the loop has finished. A default argument (`lambda x, i=i: ...`) captures the value at the time each lambda is made. Your language's closures capture *variables*, the same way Python's do.
- `checked_call`: compare `len(args)` with `arity` before calling `function(*args)`.

</details>

## Steps

Continue in your interpreter from Module 05.

### 1. Grammar

```
declaration → fnDecl | letDecl | statement
fnDecl      → FN IDENTIFIER "(" parameters? ")" block
parameters  → IDENTIFIER ( "," IDENTIFIER )*
statement   → printStmt | ifStmt | whileStmt | returnStmt | block | exprStmt
returnStmt  → RETURN expression? ";"

unary       → ( "!" | "-" ) unary | call
call        → primary ( "(" arguments? ")" )*
arguments   → expression ( "," expression )*
```

Functions can be declared anywhere a `let` can, including inside other functions.

### 2. Behaviour

- **Declaring** a function defines a variable with its name in the current scope, holding a function value that remembers the current environment.
- **Calling** works as described in the concepts above.
- `return value;` ends the current function call with that value. `return;` returns `nil`. A function that ends without `return` returns `nil`.
- Recursion works: a function can call itself, and functions declared at the top level can call each other in any order, as long as both exist by the time the call runs.
- **Printing** a function shows `<fn name>`. Printing a built-in shows `<native fn>`.
- `--ast` shows a call as `(call callee arguments...)`: `f(1, 2 + 3)` prints `(call f 1 (+ 2 3))`, `f()` prints `(call f)`, and `f(1)(2)` prints `(call (call f 1) 2)`.

### 3. Built-ins

Define these in the global environment:

| Function | Returns |
| --- | --- |
| `clock()` | the time in seconds, as a number (Python's `time.time()`), for timing programs |
| `len(s)` | the number of characters in the string `s`. Runtime error if `s` isn't a string |
| `str(v)` | the text `print` would show for `v`, as a string: `str(3) + "!"` is `"3!"` |

Built-ins get the same arity checks as your own functions.

### 4. Errors

| Problem | Error |
| --- | --- |
| Calling something that isn't a function: `"hi"()`, `let x = 1; x();` | runtime, 70 |
| Wrong number of arguments | runtime, 70 |
| `len(5)` | runtime, 70 |
| `return` outside any function | syntax, 65 |
| Missing brackets, braces or a function name: `fn (a) {}`, `f(1, 2;` | syntax, 65 |

For call errors, the line is the line of the call. A runtime error *inside* a function reports the line inside the function where it happened.

### 5. Your turn: design decisions

- **What's a function value?** A class (say `Function`) holding the declaration and the closure environment, with a `call(interpreter, arguments)` method. If your built-ins are a class with the same `call` method and an `arity`, the interpreter can call both the same way without caring which is which.
- **How does `return` get out?** A `ReturnValue` exception, raised by the `return` statement and caught in `Function.call`, is the standard trick. Don't make it inherit from your runtime error class, or `main()` will report it as an error.
- **How do you spot a top-level `return`?** The parser can keep a count of how many function bodies it's inside.

## Make it yours

- **More built-ins.** Pick a few that suit your language: `input(prompt)`, `random()`, `floor(n)`, `upper(s)`, `num(s)` to turn text into a number. Built-ins are where your language gets its personality. (Keep the three above working exactly as specified.)
- **Anonymous functions**, like `fn (x) { return x * 2; }` used as an expression, so you can pass a function without naming it first.
- **A standard library file** written in your own language, loaded before every program, with functions like `max`, `min` and `abs`.
- **Write an example program you're proud of** and put it at the top of your README: a prime sieve, a recursive tree printer, a tiny text adventure.

## Check your work

```sh
python check.py 6
```

When this passes, every module passes: you've built a language.

## Stuck?

- **Every function returns `nil`**: you catch the return exception but don't use its value, or `return` doesn't evaluate its expression.
- **Recursion fails with "undefined variable"**: define the function's name in the environment *before* any call can run, when the declaration executes.
- **Counters share one `count`**: create the call's environment fresh on every call, with the *closure* as its parent.
- **`print f(1)` inside a function prints, but then nothing works**: after a `return`, the interpreter is stuck in the function's environment. Restore it in a `finally`.
- **`RecursionError` on a deep program**: see question 2 above.

<details><summary>Hint 1: parsing calls</summary>

In `call()`: parse a `primary()`, then loop while the next token is `(`. Each time, parse the arguments separated by commas (none if the next token is `)`), expect the `)`, keep that token for its line number, and wrap everything so far in a `Call` node. The loop is what makes `f(1)(2)` work.

</details>

<details><summary>Hint 2: the function value</summary>

```python
class Function:
    def __init__(self, declaration, closure):
        self.declaration = declaration
        self.closure = closure
        self.arity = len(declaration.params)

    def call(self, interpreter, arguments):
        environment = Environment(self.closure)
        for param, argument in zip(self.declaration.params, arguments):
            environment.define(param.lexeme, argument)
        ...  # run the body in this environment, and catch the return
```

</details>

<details><summary>Hint 3: evaluating a call</summary>

Evaluate the callee and every argument. If the callee isn't a `Function` or a built-in, raise a runtime error at the closing bracket's line. If `len(arguments)` isn't its `arity`, raise one too. Otherwise return `callee.call(self, arguments)`. In `Function.call`, wrap the body in `try`/`except ReturnValue as r: return r.value`, and return `None` after it.

</details>

## Resources

- [*Crafting Interpreters*, chapter 10: Functions](https://craftinginterpreters.com/functions.html): calls, native functions, `return` via exceptions, and closures. It defines functions with `fun` and has no `len` or `str`, so follow the spec above for those.
- [*Crafting Interpreters*, chapter 11: Resolving and Binding](https://craftinginterpreters.com/resolving-and-binding.html): the subtle bug that closures and global redeclaration can cause, and a static pass that fixes it. Not needed for the checks, but well worth it next.
- [Python FAQ: why do lambdas in a loop all return the same result?](https://docs.python.org/3/faq/programming.html#why-do-lambdas-defined-in-a-loop-with-different-values-all-return-the-same-result): the practice bug, explained by Python's own docs.
- [Wikipedia: Closure (computer programming)](https://en.wikipedia.org/wiki/Closure_(computer_programming)): the history, and closures in other languages.

## Challenges (optional)

- Tail-call friendly recursion: make `fn loop(n) { if (n == 0) return 0; return loop(n - 1); }` work for `n` of 100000.
- Lists as a built-in type, with `[1, 2, 3]` syntax, indexing and a `push` built-in.
- Default parameter values: `fn greet(name, greeting = "Hi") { ... }`.

## You built a language

Look at what you have: a scanner, a parser, a tree-walking interpreter, lexical scope, first-class functions and closures. Those are the same parts inside Python, JavaScript and Ruby, just smaller. You can now read how real languages are built, and know what every part is for.

Head back to the project's [Going further](../../#going-further) ideas for where to take your language next. And show someone. A language with a name, a README and a few example programs is a project people remember.
