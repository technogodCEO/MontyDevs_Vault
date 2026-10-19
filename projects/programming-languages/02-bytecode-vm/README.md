# Bytecode Virtual Machine

> Build a fast, real implementation of a programming language you design, in C: a single-pass compiler that turns source code into bytecode, and a virtual machine that runs it, with your own hash tables, closures and garbage collector.

**Difficulty:** Advanced
**Language:** C. A VM is where C earns its keep: you decide exactly how every value is laid out in memory, every byte of bytecode, and when memory is freed. Nothing is hidden by a runtime, so nothing is magic. It's also how real language runtimes are built (CPython, Lua and Ruby's VM are all C).
**Estimated time:** 25–40 hours across all modules, plus 30 minutes of setup

> **Interpreter or compiler?** Both, in a sense, but not the gcc kind. You'll write a *compiler front end* that translates programs into **bytecode**, a compact instruction set you design, and a **virtual machine** that interprets that bytecode. This is how Python, Lua and Java work, in the style of clox from *Crafting Interpreters*. Turning programs into native machine code, as gcc does, is a different project (a future vault course).

## What you'll build

A complete implementation of a small language you name. Here's a program in it, using the usual keyword spellings:

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
print "fib(30) is " + str(fib(30));
```

```sh
./glim closures.glim
```

```
1
2
fib(30) is 832040
```

That last line takes a tenth of a second in a good VM. The same program in a tree-walking interpreter written in Python takes minutes.

You'll also build the tools VM writers rely on: `--tokens` shows how the scanner splits a program, and `--disassemble` prints the bytecode your compiler produced:

```
== <script> ==
0000    1 OP_CONSTANT         0 '1'
0003    | OP_CONSTANT         1 '2'
0006    | OP_ADD
0007    | OP_PRINT
```

**Yours will be different.** You choose the language's name, its file extension and how every keyword is spelled. Every design decision inside the VM is yours too: how values are represented, the instruction set and its encoding, how the hash table probes, when the collector runs, and what the error messages say.

## What you'll learn

- How a compiler turns source text into bytecode in a single pass, with a **Pratt parser**
- How a **stack-based virtual machine** executes instructions, and why it's fast
- C at the level real systems are written: dynamic arrays, tagged unions, pointer arithmetic, `realloc`, and owning every byte you allocate
- Writing your own **hash table** (open addressing, tombstones, FNV-1a) and string interning
- How local variables become stack slots, and how `if`, `while`, `and` and `or` become jumps
- Call frames, and how closures capture variables that outlive their function (**upvalues**)
- A **mark-sweep garbage collector**, and how to find every root
- Using **AddressSanitizer** and **UndefinedBehaviorSanitizer** to find memory bugs the moment they happen

## Prerequisites

- You're comfortable programming in a C-like language (C, C++, Java, C#, JavaScript): loops, functions, structs or classes, recursion.
- You know what a pointer is, or you're ready to learn fast. [Beej's Guide to C](https://beej.us/guide/bgc/) covers pointers, `malloc` and `free` well; read its chapters on pointers and manual memory allocation before Module 02 if they're new.
- **Strongly recommended, not required:** the Intermediate project [Tree-Walking Interpreter](../01-tree-walking-interpreter/), which implements the same language in Python. Doing it first means you know *what* to build, and can focus here on *how* to build it fast. Your `language.json` from that project works here unchanged.
- Linux, macOS, or Windows with **WSL**. [Module 00](modules/00-setup/) covers setup, and why native Windows isn't supported.

## Make it yours

The language's *behaviour* is fixed: C-style punctuation, the semantics in [the spec](SPEC.md), and the command-line flags. That's what the self-check tests. Everything else is yours:

- **The name, the file extension and the keywords.** They live in `language.json`. The self-check reads it, rewrites every test program in your spelling, and checks that your scanner agrees.
- **The VM's design.** Value representation, opcodes, operand encodings, how constants are indexed, the hash table's probing, the GC's tuning. The self-check never looks inside your code: it compiles it, runs it like a user would, and checks the output, the exit codes, the memory and the speed.
- **The error messages and the disassembler's format.** Errors must mention the line number; beyond that, write them your way.
- **Extra features.** Each module ends with challenges, and the [Going further](#going-further) list has bigger ones.

## How it's checked

`check.py` compiles your `src/*.c` itself, with `-std=c11 -Wall -Wextra`, in two builds:

- a **checked build** with AddressSanitizer and UndefinedBehaviorSanitizer, which runs every test program. A buffer overflow, use-after-free, leak or undefined behaviour fails the check even when the output looked right.
- a **fast build** with `-O2`, used for the speed and memory tests in Module 08.

**A warning counts as a failure.** In C, most warnings are bugs that haven't happened yet, and a VM is exactly the kind of program where they bite.

## How to work through this project

1. Start with [Module 00: Setup](modules/00-setup/). It installs the tools, has you name your language, and sets up your project with a `Makefile` and [`check.py`](check.py).
2. Work through the modules **in order**. Each one adds to the same VM.
3. Each lesson starts with **Practice**: questions to think through, and a `practice_NN.c` file of small C problems on that module's techniques. Copy it into your project folder and test it with `python3 check.py practice 1` (using the module's number).
4. Then build that module's part of the VM from the **spec** in the lesson. The lessons tell you *what* to build and explain the ideas; designing the code is up to you.
5. When you've finished a module, run `python3 check.py N` from your project folder. It checks that module and every module before it.
6. Stuck? Each module has a **Stuck?** section with hints you click to reveal, from a gentle nudge to an almost complete answer. There's no solution code: the hints and the linked chapters of *Crafting Interpreters* are your help.

## Modules

| # | Module | What you'll do |
| --- | --- | --- |
| 00 | [Setup](modules/00-setup/) | Install the tools, name your language, and write a `main.c` that reads files |
| 01 | [Scanning](modules/01-scanning/) | Scan source code into tokens on demand, with `--tokens` |
| 02 | [Chunks and a Stack VM](modules/02-chunks-and-a-stack-vm/) | Bytecode, a stack VM, a disassembler, and a Pratt compiler for arithmetic |
| 03 | [Values and Strings](modules/03-values-and-strings/) | Tagged-union values, heap-allocated strings, and freeing every byte |
| 04 | [Hash Tables and Globals](modules/04-hash-tables-and-globals/) | Your own hash table, string interning, and global variables |
| 05 | [Locals and Control Flow](modules/05-locals-and-control-flow/) | Stack-slot locals, block scope, and jumps for `if`, `while`, `and`, `or` |
| 06 | [Functions and Calls](modules/06-functions-and-calls/) | Function objects, call frames, recursion, and native functions |
| 07 | [Closures](modules/07-closures/) | Upvalues, so functions can capture variables that outlive them |
| 08 | [Garbage Collection](modules/08-garbage-collection/) | A mark-sweep collector, stress-tested, plus speed and memory checks |

The full language is described in one place in [SPEC.md](SPEC.md).

## Going further

Once all nine modules pass:

- **Classes and methods**: *Crafting Interpreters* chapters 27–29 add them to exactly this kind of VM.
- **NaN boxing**: pack every value into 8 bytes using the spare bits of a NaN double. [Chapter 30](https://craftinginterpreters.com/optimization.html) shows how, and how to measure the speed-up.
- **Faster dispatch**: computed `goto` instead of a `switch` ([Eli Bendersky's article](https://eli.thegreenplace.net/2012/07/12/computed-goto-for-efficient-dispatch-tables)), and superinstructions that fuse common pairs like `GET_LOCAL` + `ADD`.
- **Lists and maps**: new object types, new opcodes, and new roots for the collector.
- **A register VM**: Lua 5 switched from a stack VM to a register VM. Try it, and compare instruction counts and speed.
- **Native code**: compile your bytecode (or your AST) to x86-64 or ARM64 assembly. That's a compiler in the gcc sense, and a big step up.

## Credits

The design follows **clox** from Robert Nystrom's [*Crafting Interpreters*](https://craftinginterpreters.com/) (free to read online), which is the best book there is on this subject. Our language, spec, modules and self-checks are our own, so read the book alongside the lessons, not instead of them.
