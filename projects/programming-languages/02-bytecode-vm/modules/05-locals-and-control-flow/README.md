# Module 05: Locals and Control Flow

**Goal:** blocks with local variables that live in stack slots, and `if`/`else`, `while`, `and` and `or`, all compiled to jumps.

## Concepts

### Locals live on the stack

Globals are slow: every use is a hash table lookup. Locals can be fast, because the compiler knows exactly which locals exist at every point in the code. A block's locals live **on the VM's value stack**, in the order they were declared, and an instruction refers to a local by its **slot number**: `OP_GET_LOCAL 2` copies stack slot 2 to the top. No names, no hashing, at run time.

To do that, the compiler keeps its own list of the locals in scope (name and scope depth) that mirrors what the stack will look like when the code runs. Resolving a name means searching that list **from the end**, so the innermost variable with that name wins (shadowing). When a block ends, the compiler pops its locals off both lists: it emits a `POP` for each one, and forgets them.

This is the main difference from a tree-walking interpreter: scope is worked out once, at compile time, and costs nothing at run time.

### Declared but not ready

```
{
  let a = "outer";
  {
    let a = a;   // which a?
  }
}
```

In this VM, the new `a` is added to the compiler's list as soon as its name is read, but marked "not ready" until its initializer is compiled. Using a not-ready local is a **compile error**. It's simpler than the alternatives, and it's what clox does. (The Tree-Walking Interpreter allowed it; this is one of the two places the languages differ.)

### Jumps

Bytecode has no blocks or loops: just a flat list of instructions, and jumps. An `if` compiles to:

```
    <condition>
    JUMP_IF_FALSE  else     // skip the then-branch if the condition is falsy
    POP                     // drop the condition
    <then branch>
    JUMP           end      // skip the else-branch
else:
    POP
    <else branch>
end:
```

The catch: when the compiler emits `JUMP_IF_FALSE`, it hasn't compiled the then-branch yet, so it doesn't know how far to jump. So it emits the jump with a placeholder offset, remembers where it is, and **back-patches** the real offset once it gets there.

A `while` loop jumps *backward* (`LOOP`) to re-check its condition, and forward (`JUMP_IF_FALSE`) to leave. `and` and `or` are jumps too: `a and b` jumps over `b` when `a` is falsy, leaving `a` as the result. That's short-circuiting, for free.

Jump offsets are 16 bits: up to 65,535 bytes. A longer jump can't be encoded, so it's a compile error.

## Practice

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

The first assignment runs before the local `x` exists, so it changes the global to 2. Then a local `x` is declared, and the second assignment changes that one. When the block ends, the local is gone and `x` means the global again.

</details>

**2. Trace the stack.** What's in the stack slots just before `print c;` runs, and what instruction does `print c;` start with?

```
{
  let a = 1;
  let b = 2;
  {
    let c = a + b;
    print c;
  }
}
```

<details><summary>Answer</summary>

Slot 0 is whatever your VM keeps there (clox reserves it for the function being called, in Module 06), then `a` = 1, `b` = 2, `c` = 3. If you reserve slot 0, it's `GET_LOCAL 3`; if not, `GET_LOCAL 2`. Either way, the slot numbers are worked out when compiling, and nothing about names is left at run time.

</details>

**3. Spot the problem.** This compiles `while`. What goes wrong when it runs?

```c
int exit_jump = emit_jump(OP_JUMP_IF_FALSE);
int loop_start = current_chunk()->count;
emit_byte(OP_POP);
statement();
emit_loop(loop_start);
patch_jump(exit_jump);
emit_byte(OP_POP);
```

<details><summary>Answer</summary>

`loop_start` is recorded *after* the condition, so the loop jumps back to the body and never re-checks the condition: it runs forever (or until the condition's `POP` empties the stack). Record `loop_start` before compiling the condition. Also, where is the condition compiled? It must come between `loop_start` and the `JUMP_IF_FALSE`.

</details>

### Try it in code

[`practice_05.c`](practice_05.c): reading and writing 16-bit operands, back-patching a jump, a tiny VM with jumps, and an off-by-one in a backward jump. Copy it into your project folder and run `python3 check.py practice 5`.

<details><summary>Hints</summary>

- `write_u16`: the high byte is `(value >> 8) & 0xff`, the low byte `value & 0xff`.
- `run_counter`: keep `ip` as a pointer, read operands with `*ip++`, and remember that a distance counts from the byte *after* the operands.
- The FIX: when the VM executes the jump, where is `ip`?

</details>

## Steps

Continue from Module 04.

### 1. Blocks and locals

- `{ ... }` is a statement holding declarations, and makes a new scope.
- A `let` inside a block declares a local, visible until the end of its block. It hides any variable of the same name outside.
- Reading a local in its own initializer is a compile error (`let x = x;`, and `let a = a + 1;` inside a block).
- At least 255 locals in scope at once; more is a compile error, not a crash. (The self-check uses 200, then tries 300.)
- At the top level, `let` still declares globals.

### 2. `if`, `while`, `and`, `or`

The [spec](../../SPEC.md) has the grammar: `if (cond) stmt else stmt`, `while (cond) stmt`, and `and`/`or` with their precedence and short-circuiting. Truthiness: only `false` and `nil` are falsy. `and` and `or` return one of their operands, not a boolean: `nil or "default"` is `"default"`.

Compile errors for broken syntax: a missing `(` or `)`, a missing statement after `else`, an unclosed block (the error is at the end of the file).

### 3. Long jumps

Jump offsets are two bytes. A jump over more than 65,535 bytes must be a **compile error**. Never let it silently wrap around: the self-check compiles an `if` whose body is around 100,000 bytes. An `if` or `while` body of 3,000 statements (well under the limit) must work.

## Make it yours

- **Your jump instructions.** `JUMP_IF_FALSE` that leaves the condition on the stack (as in clox, needing a `POP` after) or one that pops it. Fewer instructions, or simpler `and`/`or`?
- **`for` loops** (see the challenges). They need no new instructions: they're a `while` in disguise.
- **Compile errors that help.** "Expect ')' after condition." is fine; "You opened a '(' on line 3 that's never closed" is better.

## Check your work

```sh
python3 check.py practice 5
python3 check.py 5
```

## Stuck?

- **`stack-buffer-overflow` or garbage values after a block**: the block's locals weren't popped at runtime, or popped twice. The number of `POP`s emitted when a scope ends must match the locals the compiler forgets.
- **An `if` without an `else` leaves an extra value on the stack**: the condition's `POP` must happen on *both* paths. Look at the bytecode in the concepts section: one `POP` after `JUMP_IF_FALSE`, one at `else:`.
- **A nested function's local gets the wrong value** (Module 06 and later): resolve names from the **end** of the locals list.
- **Big programs behave strangely instead of failing to compile**: a jump offset over 65,535 wrapped. Check the offset in `patch_jump` and `emit_loop`.

<details><summary>Hint 1</summary>

The compiler's locals list: an array of `{Token name; int depth;}`, a count, and the current scope depth. `begin_scope()` increments the depth; `end_scope()` decrements it, then pops every local whose depth is now too deep. Declaring a local appends it with depth -1 ("not ready"); after the initializer, set its depth to the current depth.

</details>

<details><summary>Hint 2</summary>

`emit_jump(op)` writes the opcode and two `0xff` placeholder bytes, and returns the offset of the first placeholder. `patch_jump(offset)` computes `jump = current_chunk()->count - offset - 2` (the distance from the end of the operand to here), checks it fits, and writes it. `emit_loop(start)` computes the distance backward from the end of its own operand to `start`.

</details>

<details><summary>Hint 3</summary>

`and`: after compiling the left operand, emit `JUMP_IF_FALSE` (keeping the value), then `POP`, compile the right operand at `PREC_AND`, and patch the jump. `or` can be built from `JUMP_IF_FALSE` and `JUMP`: if falsy, jump to the right operand, else jump to the end.

</details>

## Resources

- [*Crafting Interpreters*, chapter 22: Local Variables](https://craftinginterpreters.com/local-variables.html): the compiler's locals array, scope depth, and the uninitialized-local error.
- [Chapter 23: Jumping Back and Forth](https://craftinginterpreters.com/jumping-back-and-forth.html): `if`, `while`, `and`, `or`, and back-patching. It includes `for`, which is a challenge here.

## Challenges (optional)

- Add `for (init; condition; increment) body`, compiled into the same jumps as `while`. (You'll need a new keyword.)
- Add `break`, which needs a list of jumps to patch when the loop ends, and has to pop the loop's locals before jumping.
- Allow more than 255 locals, with a long form of `GET_LOCAL`/`SET_LOCAL`.

## Next

Continue to [Module 06: Functions and Calls](../06-functions-and-calls/).
