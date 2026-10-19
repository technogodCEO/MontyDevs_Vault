# Module 07: Closures

**Goal:** inner functions can use the variables of the functions around them, even after those functions have returned. Counters, adders, and closures created in loops all work.

## Concepts

### The problem

```
fn makeCounter() {
  let count = 0;
  fn counter() {
    count = count + 1;
    return count;
  }
  return counter;
}
```

`count` is a local of `makeCounter`, so it lives in `makeCounter`'s stack window. But `counter` is called *after* `makeCounter` has returned, when that window is gone and the slot has been reused. Where does `count` live then?

### Upvalues

A **closure** is a function plus references to the variables it captured. Each reference is an **upvalue**: a small object pointing at the variable.

- While the variable is still on the stack, the upvalue is **open**: it points at the stack slot. Code in the closure reads and writes through the pointer, so it sees the same variable as the enclosing function.
- When the variable's scope ends (its block ends, or its function returns), the upvalue is **closed**: the value is copied into the upvalue object itself, and the pointer is moved to point there. The closure carries on using the same pointer, now aimed at its private copy.

Two closures that capture the same variable must share it, so the VM keeps a list of open upvalues, sorted by stack slot, and reuses an existing upvalue for a slot instead of making a second one.

### What the compiler does

When the compiler resolves a name that isn't a local, it looks in the enclosing function's locals. If it finds it there, it marks that local as **captured**, and gives the current function an upvalue for it. If it's further out, the enclosing function gets an upvalue too, and the current one refers to that (a chain, one link per function). Every function knows its upvalues at compile time; the closure-creating instruction lists them, so the VM knows what to capture.

When a captured local goes out of scope, the compiler emits a "close upvalue" instruction instead of a plain `POP`.

## Practice

### Think it through

**1. Predict the output.**

```
fn f() {
  let x = 1;
  fn g() {
    return x;
  }
  x = 2;
  return g;
}
print f()();
```

<details><summary>Answer</summary>

`2`. Closures capture the *variable*, not the value it had when the closure was made. When `f` returns, the upvalue is closed with `x`'s value at that moment, which is 2.

</details>

**2. Predict the output.**

```
let a;
let b;
let i = 0;
while (i < 2) {
  let j = i;
  fn show() {
    return j;
  }
  if (i == 0) a = show;
  if (i == 1) b = show;
  i = i + 1;
}
print a();
print b();
```

<details><summary>Answer</summary>

`0`, then `1`. Each pass through the loop body is a new scope, so `j` is a new variable each time, and its upvalue is closed when the body ends. If your VM printed `1` and `1`, it didn't close the upvalue at the end of each pass (both closures share one open upvalue for the same slot).

</details>

**3. Spot the problem.** A VM closes upvalues when a function returns, but not when a block ends. Which programs break?

<details><summary>Answer</summary>

Any closure that captures a block-local and outlives the block, without its function returning first: like the loop in question 2, or a closure stored in a global from inside a `{ }` block at the top level. The stack slot gets reused by the next local, and the closure sees *that* value.

</details>

### Try it in code

[`practice_07.c`](practice_07.c): inserting into the sorted list of open upvalues, closing them, and a use-after-free. Copy it into your project folder and run `python3 check.py practice 7`.

<details><summary>Hints</summary>

- `capture`: walk the list while `u->location > slot`, remembering the previous node, then either reuse `u` (same slot) or insert a new node between the previous one and `u`.
- `close_upvalues`: the list is sorted highest first, so you only ever close from the head.
- The FIX: the loop reads `u->next` after `free(u)`. Save it first.

</details>

## Steps

Continue from Module 06.

Spec:

- A function can read and assign variables from any function around it, however many levels out.
- Each call makes new variables, so closures from separate calls don't share them (`makeCounter()` twice gives two independent counters). Closures from the same call do share them: two functions that both change a captured variable see each other's changes.
- Closures capture variables, not values: a change made after the closure was created is visible inside it.
- A captured variable keeps working after its scope ends, whether its block ended or its function returned, including on every pass through a loop.
- Nothing else changes: all the earlier programs still work, and the self-check runs them all again.

You'll need: closure objects (a function plus an array of upvalue pointers), upvalue objects, a list of open upvalues in the VM, compiler support for resolving upvalues, and instructions to make closures, get and set upvalues, and close them.

## Make it yours

- **Closures for every function, or only when needed?** clox wraps every function in a closure, even ones that capture nothing, which keeps calls uniform. You could skip the wrapper when a function has no upvalues. Faster, or more complicated?
- **How upvalue indexes are encoded** in the closure instruction.

## Check your work

```sh
python3 check.py practice 7
python3 check.py 7
```

## Stuck?

- **Two counters share a count**: you're capturing the function's *global* variable, or the same upvalue for both calls. Upvalues must point at the stack slot in the current call's window.
- **The loop-capture program prints the same number twice**: you're not closing the upvalue at the end of each pass. `end_scope` must emit the close instruction for captured locals.
- **`heap-use-after-free` or wrong values after a function returns**: on return, close every open upvalue at or above the frame's window *before* discarding the window.
- **`<fn inner>` instead of a value**: the closure instruction's operands are read wrong, so the VM is out of step with the bytecode.

<details><summary>Hint 1</summary>

The compiler's per-function state gets an array of upvalues: `{uint8_t index; bool is_local;}`. `is_local` means "this captures a local of the enclosing function, in slot `index`"; otherwise it captures the enclosing function's upvalue number `index`.

</details>

<details><summary>Hint 2</summary>

`resolve_upvalue(compiler, name)`: if there's no enclosing compiler, return -1. If the enclosing compiler has a local with that name, mark it captured and add an upvalue `{slot, true}`. Otherwise recurse into the enclosing compiler; if that finds an upvalue, add `{its index, false}`. Reuse an existing upvalue with the same index and kind, so a variable used twice is captured once.

</details>

<details><summary>Hint 3</summary>

In the VM, the closure instruction reads the function constant, makes the closure, **pushes it** (keep it safe on the stack), then for each upvalue reads `is_local` and `index`: if local, `capture_upvalue(frame->slots + index)`; if not, copy `frame->closure->upvalues[index]`.

</details>

## Resources

- [*Crafting Interpreters*, chapter 25: Closures](https://craftinginterpreters.com/closures.html): upvalues, open and closed, and the compiler's resolution chain. It's the hardest chapter in the book, and worth reading slowly.
- [Wikipedia: Closure (computer programming)](https://en.wikipedia.org/wiki/Closure_(computer_programming)): the idea in other languages.

## Challenges (optional)

- Skip the closure wrapper for functions without upvalues, and measure the difference on `fib(30)`.
- Lua does the same thing with "upvalues", and so does this VM. Read how [Lua 5.0's implementation paper](https://www.lua.org/doc/jucs05.pdf) describes them and compare.

## Next

Continue to [Module 08: Garbage Collection](../08-garbage-collection/).
