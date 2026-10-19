# Tree-Walking Interpreter

> Design a programming language of your own, then write the interpreter that runs it: a scanner, a parser and an evaluator, with variables, loops, functions and closures.

**Difficulty:** Intermediate
**Language:** Python. Its dictionaries, classes and recursion keep the interpreter short, so you can spend your time on how languages work rather than on memory management. Every idea here carries over to writing an interpreter in any language.
**Estimated time:** 15–25 hours across all modules, plus 15 minutes of setup

**Next step:** the Advanced project [Bytecode Virtual Machine](../02-bytecode-vm/) implements this *same* language spec again in C, compiled to bytecode and many times faster. Your `language.json` works in both, so you can carry your language over. Neither project requires the other.

## What you'll build

A working interpreter for a small language that you name. Here's a program in it, using the usual keyword spellings:

```
// Closures: each counter remembers its own count.
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

fn fib(n) {
  if (n < 2) return n;
  return fib(n - 1) + fib(n - 2);
}
print "fib(15) is " + str(fib(15));
```

```sh
python glim.py closures.glim
```

```
1
2
fib(15) is 610
```

**Yours will be different.** You choose your language's name, its file extension and how every keyword is spelled. Want `make` instead of `let`, `yeet` instead of `return`, `yes`/`no` instead of `true`/`false`? Go for it. You also decide how your interpreter is organised inside, what its error messages say, and which extra features to add once the core works.

You'll also build two tools that real language implementers use: `--tokens`, which shows how your scanner splits a program into tokens, and `--ast`, which shows the tree your parser builds.

## What you'll learn

- How source code becomes tokens (**scanning**), then a tree (**parsing**), then results (**evaluating**)
- Recursive descent parsing, and how precedence and associativity really work
- Representing programs as trees, and walking them with recursion
- Environments and lexical scope: what a variable actually *is*
- Short-circuit evaluation, and how `if` and `while` are built from it
- Functions as values, call stacks, and closures
- Writing helpful error messages, with line numbers

## Prerequisites

- You're comfortable in Python: classes, recursion, dictionaries, exceptions and reading a stack trace. If you've built a project or two with several functions and classes, you're ready.
- You don't need to have studied compilers or language theory. The modules introduce every idea you need.
- A computer you can install software on. [Module 00](modules/00-setup/) covers setup.

## Make it yours

The language's *structure* is fixed: C-style punctuation, braces for blocks, semicolons, and the behaviour described in each module. That's what the self-check tests. Everything else is up to you:

- **The name, the file extension and the keywords.** They live in your `language.json`. The self-check reads it and rewrites every test program in your spelling.
- **The design of the interpreter.** Classes or tuples for your tree, one file or several, a visitor or a big `if`. The self-check never looks inside: it runs your interpreter the way a user would and checks what comes out.
- **The error messages.** They must mention the line number. Beyond that, make them as friendly (or as dramatic) as you like.
- **Extra features.** Each module ends with challenges: `for` loops, `+=`, string escapes of your own, lists, a `break` statement. Anything extra is fine, as long as the core behaviour still matches.

## How to work through this project

1. Start with [Module 00: Setup](modules/00-setup/). It gets Python ready, has you name your language, and sets up your project folder with [`check.py`](check.py).
2. Work through the modules **in order**. Each one adds a stage to the same interpreter, and the later stages depend on the earlier ones.
3. Each lesson starts with **Practice**: questions to think through, and a `practice_NN.py` file of small problems. Copy it into your project folder and test it with `python check.py practice 1` (using the module's number).
4. Each lesson's **Steps** say exactly what your interpreter must do. They show code for the tricky parts (the shape of a class, the pattern a function follows) and leave the rest to you. Read all the steps before you start coding.
5. At the end of each module, check your work from your project folder:
   ```sh
   python check.py 1      # use the module's number
   ```
6. Stuck? Each module's **Stuck?** section has common problems and hints you reveal one at a time. There are no solutions to copy: working it out is the point.

[*Crafting Interpreters*](https://craftinginterpreters.com/) by Robert Nystrom, free to read online, inspired this project and makes a great companion. Each module links the chapters that cover its ideas. Its language, Lox, is close to ours but not the same, so when they disagree, follow the module's spec.

## Modules

| # | Module | What you'll do |
| --- | --- | --- |
| 00 | [Setup](modules/00-setup/) | Name your language, choose its keywords, and make your project folder |
| 01 | [Scanning](modules/01-scanning/) | Split source code into tokens, and show them with `--tokens` |
| 02 | [Parsing Expressions](modules/02-parsing-expressions/) | Build a tree from the tokens with a recursive descent parser, and show it with `--ast` |
| 03 | [Evaluating Expressions](modules/03-evaluating-expressions/) | Work out values, run `print` statements, and report runtime errors |
| 04 | [Variables and Scope](modules/04-variables-and-scope/) | Add variables, assignment and blocks, with environments |
| 05 | [Control Flow](modules/05-control-flow/) | Add `if`, `while`, `and` and `or` |
| 06 | [Functions](modules/06-functions/) | Add functions, `return`, recursion, closures and built-ins |

## Going further

Finished? Your language can already compute anything a computer can. Here's where to take it next:

- **Lists and indexing**: `[1, 2, 3]`, `xs[0]`, and built-ins like `push` and `len` for them.
- **Classes and objects**: *Crafting Interpreters* chapters 12–13 add classes, methods and inheritance to Lox.
- **A resolver**: chapter 11 fixes a subtle closure bug and catches more mistakes before the program runs.
- **A standard library**: file reading, string functions, `input()`, random numbers.
- **Better errors**: report every syntax error in a file, not just the first, and show the line of code with a `^` under the problem.
- **Speed**: the [Bytecode Virtual Machine](../02-bytecode-vm/) project rebuilds this language in C, as a compiler to bytecode and a virtual machine that runs it, with a garbage collector. Part III of *Crafting Interpreters* covers the same ground.
- **Share it**: write a README with example programs, put it on GitHub, and get a friend to write a program in your language.
