# Module 02: Chunks and a Stack VM

**Goal:** your language runs programs for the first time. A single-pass compiler turns arithmetic and `print` statements into bytecode, a stack-based VM runs it, and `--disassemble` shows what the compiler produced.

This is the biggest module: it builds the whole pipeline, end to end. Every later module extends it.

## Concepts

### Bytecode and chunks

**Bytecode** is a list of instructions for a machine that doesn't exist: a virtual one, designed by you. Each instruction is an **opcode** (one byte) and maybe some **operand** bytes after it. A **chunk** holds a sequence of bytecode, plus:

- a **constant pool**: the values the code uses, like `3.14`. `OP_CONSTANT 2` means "push constant number 2".
- a **line number for every byte**, so runtime errors can say where they happened.

All three are **dynamic arrays**: a pointer, a count and a capacity. When the array is full, `realloc` it to double the capacity. Doubling makes adding an element take constant time on average (amortized), however big the array gets.

### A stack machine

The VM keeps a **value stack**. Instructions pop their operands and push their results. `1 + 2 * 3` compiles to:

```
OP_CONSTANT 0   (1)       stack: 1
OP_CONSTANT 1   (2)       stack: 1 2
OP_CONSTANT 2   (3)       stack: 1 2 3
OP_MULTIPLY               stack: 1 6
OP_ADD                    stack: 7
OP_PRINT                  stack: (empty), prints 7
```

The VM's heart is a loop: read an opcode, `switch` on it, do it, repeat. Keep the **instruction pointer** (`ip`) as a `uint8_t *` into the code, not an index: it's one less addition per instruction, and this loop runs billions of times.

### A single-pass compiler

A tree-walking interpreter parses into a tree, then walks the tree. This compiler parses and **emits bytecode as it goes**, with no tree at all. That's possible because a stack machine's code comes out in the same order a parser finishes each piece: compile the left operand, compile the right operand, then emit the operator.

The parser is a **Pratt parser**. Each token type has a row in a table:

| Token | Prefix rule (starts an expression) | Infix rule (continues one) | Precedence as infix |
| --- | --- | --- | --- |
| `NUMBER` | `number` | | |
| `(` | `grouping` | | |
| `-` | `unary` | `binary` | TERM |
| `+` | | `binary` | TERM |
| `*` `/` `%` | | `binary` | FACTOR |

`parse_precedence(p)` reads one token and runs its prefix rule. Then, while the next token is an infix operator with precedence at least `p`, it runs that infix rule. `binary` parses its right operand at *one level higher* than its own operator, which is what makes `10 - 4 - 3` mean `(10 - 4) - 3`. The whole precedence table is in [the spec](../../SPEC.md#grammar).

### Errors

A **compile error** stops the program before anything runs: report it (with the line of the token where it happened), keep track that there was one, and exit with code 65 when compiling is done. A **runtime error** happens while running: report it with the line of the instruction that failed (from the chunk's line array) and exit with code 70.

## Practice

### Think it through

**1. Predict the bytecode** for `print -(5 - 2) * 4;`, as a list of instructions.

<details><summary>Answer</summary>

```
OP_CONSTANT 5
OP_CONSTANT 2
OP_SUBTRACT
OP_NEGATE
OP_CONSTANT 4
OP_MULTIPLY
OP_PRINT
```

Unary `-` binds tighter than `*`, so it applies to the group `(5 - 2)` before the multiplication. The output is `-12`.

</details>

**2. Spot the problem.** This VM gets `10 - 4` wrong. What does it print, and why?

```c
case OP_SUBTRACT: {
  double a = pop();
  double b = pop();
  push(a - b);
  break;
}
```

<details><summary>Answer</summary>

`-6`. The right operand was pushed last, so it's popped *first*. Here `a` is 4 and `b` is 10. Pop `b` first, then `a`.

</details>

**3. Spot the problem.** A chunk's code array grows like this. It works for a while, then crashes. Why?

```c
if (chunk->count == chunk->capacity) {
  chunk->capacity *= 2;
  chunk->code = realloc(chunk->code, chunk->capacity);
}
```

<details><summary>Answer</summary>

A new chunk has capacity 0, and `0 * 2` is still 0, so it never grows: the first write is out of bounds. Start at a minimum, like 8. (The same code for an array of `int` or `double` would also need `* sizeof(int)`: `realloc` counts bytes.)

</details>

### Try it in code

[`practice_02.c`](practice_02.c): a growable int array, freeing it, a tiny stack VM to finish, and a `realloc` bug. Copy it into your project folder and run `python3 check.py practice 2`.

<details><summary>Hints</summary>

- `int_array_push`: grow *before* writing when `count == capacity`. `realloc(NULL, n)` behaves like `malloc(n)`, so the first growth needs no special case.
- `run_bytes`: keep a `top` index into the stack array. Read the operand with `*code++` right after `OP_PUSH`.
- The FIX: what does `realloc`'s second argument count?

</details>

## Steps

Continue from Module 01. Some files you might add: `chunk.c/h`, `value.c/h`, `vm.c/h`, `compiler.c/h`, `debug.c/h` (the disassembler), and `memory.c/h` (one place that does all allocation; you'll be glad of it in Module 08).

### 1. Chunks

A chunk holds bytecode, a line for every byte, and a constant pool of numbers (for now). Each is a dynamic array that grows by doubling. Freeing a chunk frees all three.

**At least 65,536 constants per chunk.** One operand byte only reaches 255, which a long program blows through. Choose an encoding: two-byte operands for every constant index, or a short form plus a long form (`OP_CONSTANT` and `OP_CONSTANT_LONG`). Your design; the self-check runs a program with 2,000 constants.

### 2. The VM

A value stack (a fixed array is fine: say 256 values for now), an instruction pointer, and a run loop. Opcodes for this module: constants, `ADD`, `SUBTRACT`, `MULTIPLY`, `DIVIDE`, `MODULO`, `NEGATE`, `PRINT`, `POP`, and `RETURN` (ends the program). You can name them however you like.

`%` is C's `fmod` (from `<math.h>`, which is why the build links `-lm`). Dividing by zero, or `%` by zero, is a runtime error.

### 3. The compiler

Compile a whole program to one chunk:

```
program    → statement* EOF
statement  → "print" expression ";" | expression ";"
expression → numbers, ( ), unary -, and + - * / %
```

`print` prints a value and a newline. An expression statement evaluates its expression and discards it (`POP`). Numbers are `double`s, read with `strtod`.

**Printing numbers:** a whole number prints with no decimal point (`7`, `-6`, `12345678`). Any other number prints as the shortest text that reads back as exactly the same double: `2.5`, `0.30000000000000004` for `0.1 + 0.2`. (You'll practise this in Module 03's practice file if you want to warm up on it first; `%.17g` alone prints `2.5` as `2.5` but `0.1` as `0.10000000000000001`.)

**Compile errors** (exit 65, nothing runs): an expression missing (`print;`, `print 1 +;`), a missing `)`, two expressions in a row (`print 1 2;`), a missing `;`. The message includes `line N` for the token where the error was found; for "missing `;` at the end of the file", that's the last line.

The REPL compiles and runs each line on its own. An error on one line doesn't stop the REPL.

### 4. `--disassemble`

`./glim --disassemble file` compiles the file and prints its bytecode **without running it**. The format is yours. It must include:

- a header line with the function's name (for the whole program, call it `<script>`; functions arrive in Module 06),
- one line per instruction, with its byte offset and its source line, and its operands (show a constant's value, too: you'll thank yourself later).

On a compile error, report it and exit 65.

## Make it yours

- **Your instruction set.** Opcode names, operand sizes, whether `!=` is its own instruction or `EQUAL` followed by `NOT` (Module 03). Instruction design is the main creative decision in a VM.
- **Line numbers.** One `int` per byte is simple, and wasteful: most bytes share their line with the one before. Run-length encode them (see the challenges).
- **The disassembler's look.** Line numbers shown as `|` when they repeat, jump targets with arrows, colours.

## Check your work

```sh
python3 check.py practice 2
python3 check.py 2
```

The self-check runs arithmetic programs (precedence, grouping, formatting), a program with 2,000 constants, an expression nested 200 deep, `--disassemble`, runtime errors and compile errors.

## Stuck?

- **`10 - 4 - 3` gives 9**: your `binary` parses its right operand at the same precedence as the operator, which makes it right-associative. Use one level higher.
- **The sanitizer reports `stack-buffer-overflow` or `global-buffer-overflow` in the run loop**: the value stack over- or underflowed. Usually an instruction pops more than it should, or the compiler forgot a `POP` after an expression statement.
- **Garbage output after the first few constants, or a crash at constant 256**: your constant index is one byte, so 256 wraps to 0.
- **`0.1 + 0.2` prints `0.3`**: you're using `%g`, which rounds to 6 significant digits. Try increasing precisions until `strtod` gives back the same number.
- **The REPL dies after a compile error**: the error state (a "had error" flag, the stack) isn't reset between lines.

<details><summary>Hint 1</summary>

The compiler needs only two tokens at a time: `current` (not yet consumed) and `previous` (just consumed). Write `advance()`, `consume(type, message)` and `match(type)` around `scan_token()`, and `emit_byte()`, which writes to the chunk with `previous.line`.

</details>

<details><summary>Hint 2</summary>

The rules table is an array indexed by token type, of structs `{prefix function, infix function, precedence}`. With designated initializers it reads like the table above: `[TOKEN_MINUS] = {unary, binary, PREC_TERM},`. Every token type needs a row, even if it's `{NULL, NULL, PREC_NONE}`.

</details>

<details><summary>Hint 3</summary>

```c
static void parse_precedence(Precedence precedence) {
  advance();
  ParseFn prefix = get_rule(parser.previous.type)->prefix;
  if (prefix == NULL) { error("Expect expression."); return; }
  prefix();
  while (precedence <= get_rule(parser.current.type)->precedence) {
    advance();
    get_rule(parser.previous.type)->infix();
  }
}
```

`binary()` remembers the operator, calls `parse_precedence(rule->precedence + 1)` for the right side, then emits the instruction.

</details>

## Resources

- [*Crafting Interpreters*, chapter 14: Chunks of Bytecode](https://craftinginterpreters.com/chunks-of-bytecode.html): dynamic arrays and the disassembler. Its constants are one byte; ours must reach 65,536 (chapter 14's first challenge).
- [Chapter 15: A Virtual Machine](https://craftinginterpreters.com/a-virtual-machine.html): the run loop, the value stack, and why `ip` is a pointer.
- [Chapter 17: Compiling Expressions](https://craftinginterpreters.com/compiling-expressions.html): the Pratt parser, in detail. Its `print` statement arrives in chapter 21; ours is here from the start, so programs can run.
- [Pratt Parsers: Expression Parsing Made Easy](https://journal.stuffwithstuff.com/2011/03/19/pratt-parsers-expression-parsing-made-easy/): the same author on why Pratt parsing works, with more theory.

## Challenges (optional)

- Run-length encode the line numbers, and write `get_line(chunk, offset)`. Measure the memory saved on a big program.
- Add a `--trace` flag that prints the stack before every instruction. It's the best debugging tool a VM can have.
- Constant-fold at compile time: `print 2 * 3;` could compile to a single constant `6`.

## Next

Continue to [Module 03: Values and Strings](../03-values-and-strings/).
