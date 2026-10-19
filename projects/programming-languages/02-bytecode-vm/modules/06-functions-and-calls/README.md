# Module 06: Functions and Calls

**Goal:** functions you can declare, call, pass around and return from, with recursion, call frames, native functions (`clock`, `len`, `str`), and a clean runtime error instead of a crash when recursion goes too deep.

## Concepts

### Functions are compiled to their own chunks

Each function gets its own **function object**: its name, its **arity** (how many parameters), and its own chunk of bytecode. The compiler now keeps a *stack* of compiler states, one per function being compiled: when it meets `fn`, it starts a fresh one, compiles the body into it, and when the body ends, the finished function object becomes a **constant** in the enclosing function's chunk. The top-level program is a function too, the implicit `<script>`.

### Call frames

The VM keeps a stack of **call frames**, one per function call in progress. Each frame remembers:

- which function it's running,
- its own instruction pointer (where to continue when the call it makes returns),
- where its **stack window** starts: the slot on the value stack where its locals begin.

The trick that makes calls cheap: the caller has already pushed the function and its arguments onto the value stack, in order. Those arguments *are* the callee's first locals. The new frame's window simply starts at the function's slot, so slot 0 is the function, and parameters are slots 1, 2, ... No copying.

```
value stack:  ... | <fn add> | 1 | 2 |
                    ^ add's frame window starts here: slot 0, a = slot 1, b = slot 2
```

Returning pops the frame, discards the window, and pushes the return value where the function was.

### Natives

A **native function** is written in C and called from your language. It's another kind of object, holding a C function pointer. Calling it doesn't push a frame: the VM calls the C function with the arguments straight from the stack, and pushes what it returns.

### Stack overflow

There's a fixed number of frames (clox uses 64). Endless recursion must stop with a runtime error saying "Stack overflow", not run off the end of the frames array and crash. The sanitizer would catch that, but your users don't have one.

## Practice

### Think it through

**1. Predict the output.**

```
fn hi() {
  print "hi";
}
print hi();
print hi;
print clock;
```

<details><summary>Answer</summary>

```
hi
nil
<fn hi>
<native fn>
```

A function without a `return` returns `nil`, so `print hi();` prints `hi` (from inside) then `nil`. Printing a function shows its name; printing a native shows `<native fn>`. (`nil` in your spelling.)

</details>

**2. Trace the stack.** `fn add(a, b) { return a + b; }` is called as `print add(1, 2);`. What's on the value stack just before `OP_CALL` runs, and what's the call instruction's operand?

<details><summary>Answer</summary>

`<fn add>`, `1`, `2`, from bottom to top, above whatever the script had. The operand is the argument count, 2, so the VM finds the function 2 slots below the top: `peek(2)`. The new frame's window starts there.

</details>

**3. Spot the problem.** This VM's run loop caches the current frame in a local variable `frame` for speed. After `OP_CALL` pushes a new frame, the loop carries on with the next instruction. What goes wrong?

<details><summary>Answer</summary>

`frame` still points at the *caller's* frame, so the VM keeps running the caller's code and never enters the function. After a call (and after a return), reload `frame = &vm.frames[vm.frame_count - 1]`.

</details>

### Try it in code

[`practice_06.c`](practice_06.c): a fixed-size call stack, writing a stack trace safely into a buffer, and a buffer overflow to fix. Copy it into your project folder and run `python3 check.py practice 6`.

<details><summary>Hints</summary>

- `format_trace`: `snprintf` returns how many characters it *would* have written, which can be more than it did. Keep track of how much of the buffer is used, and stop when it's full.
- The FIX: one function in `<stdio.h>` is `sprintf` with a size limit.

</details>

## Steps

Continue from Module 05.

### 1. Function declarations and calls

- `fn name(params) { body }` declares a function named `name`: a global at the top level, or a local inside a block or function. A function can call itself (recursion) and other globals declared later (mutual recursion).
- A call `f(a, b)` is an expression with the precedence of a call: `f(1)(2)` calls the result of `f(1)`. At most 255 arguments.
- `return expr;` returns a value; `return;` or the end of the body returns `nil`. `return` at the top level is a compile error.
- Functions are values: `print add;` prints `<fn add>`.

### 2. Errors

Runtime errors (exit 70), each with the line of the call:

- calling with the wrong number of arguments,
- calling something that isn't a function,
- recursion deeper than your frame limit: the message must include `Stack overflow`. At least 64 calls deep must work.

Compile errors: `return` outside a function, and broken syntax (a missing `(`, parameter name, `)` or `{`).

A runtime error inside a function should report the line in the function where it happened. A stack trace (one line per frame, innermost first) is optional, and recommended.

### 3. Natives

Define `clock()`, `len(s)` and `str(v)` as globals before the program runs. The [spec](../../SPEC.md#functions) has the rules. Calling a native with the wrong number of arguments is a runtime error, and so is `len` of something that isn't a string. `str(v)` gives exactly the text `print` would show, so share the code.

### 4. `--disassemble`

Show every function: the script, then each function compiled inside it (they're constants in its chunk), each with its name in its header.

### 5. The REPL

Functions declared on one line can be called on the next.

## Make it yours

- **Your calling convention.** Does slot 0 hold the function, or nothing? What does a native's C signature look like? (Returning a `bool` for success makes native errors easy.)
- **Stack traces.** What should a runtime error deep in recursion look like? Collapse repeated frames ("... 60 more calls to fib()").
- **More natives.** `input()`, `sqrt()`, `floor()`, `random()`. Each is a few lines of C.

## Check your work

```sh
python3 check.py practice 6
python3 check.py 6
```

## Stuck?

- **Locals inside functions read the wrong values**: the frame's window starts in the wrong place. It's `stack_top - arg_count - 1`, the slot holding the function.
- **`return` from a function messes up the caller's stack**: on return, set `stack_top` back to the start of the returning frame's window *before* pushing the result.
- **A crash or sanitizer report on deep recursion**: check the frame count before pushing a frame, not after.
- **`global-buffer-overflow` when a native runs**: a native reads `args[0]` when it was called with no arguments. Check the argument count before calling it.

<details><summary>Hint 1</summary>

The compiler: a `Compiler` struct holding its function object, its locals, its scope depth, a function type (script or function, so `return` can be checked), and a pointer to the enclosing `Compiler`. A global `current` points at the innermost one.

</details>

<details><summary>Hint 2</summary>

In the VM, `call(function, arg_count)` checks the arity and the frame count, then fills in the next frame: the function, `ip` at the start of its code, and `slots = vm.stack_top - arg_count - 1`. `OP_CALL` reads the argument count, calls `call_value(peek(arg_count), arg_count)`, then reloads the cached `frame`.

</details>

<details><summary>Hint 3</summary>

The value stack now has to hold every frame's locals and temporaries at once. A fixed array of `FRAMES_MAX * 256` values covers the worst case of 256 slots per frame.

</details>

## Resources

- [*Crafting Interpreters*, chapter 24: Calls and Functions](https://craftinginterpreters.com/calls-and-functions.html): function objects, the compiler stack, call frames, and natives. It's a long chapter; it covers all of this module.

## Challenges (optional)

- Cache `ip` in a local variable (a register) in the run loop, instead of going through `frame->ip`. Measure the speed-up with `fib(30)`.
- Add default parameter values, or optional arguments.
- Report a runtime error's whole stack trace, with repeated frames collapsed.

## Next

Continue to [Module 07: Closures](../07-closures/).
