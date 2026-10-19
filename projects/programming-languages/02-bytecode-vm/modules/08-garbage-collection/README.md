# Module 08: Garbage Collection

**Goal:** a mark-sweep garbage collector, so programs that make far more garbage than fits in memory run in a few megabytes. It survives being run on every single allocation, and your VM passes its speed tests.

## Concepts

### Reachability

Until now, objects were freed only at exit. A loop that joins strings a million times keeps every one of them. A **garbage collector** frees objects the program can no longer use. Which ones? The ones it can't **reach**: an object is live if the program can get to it by following references from a **root**, and garbage otherwise.

The roots are everything the VM itself can touch directly:

- every value on the value stack,
- every call frame's closure,
- every open upvalue,
- every global variable,
- and, easy to forget, the functions the **compiler** is still building (which hold constants, and aren't reachable from anywhere else yet).

### Mark and sweep

1. **Mark** every root. A marked object goes on a **gray stack**: reached, but its own references not yet followed.
2. **Trace**: pop a gray object and mark everything it refers to (a closure's function and upvalues, a function's name and constants, a closed upvalue's value). Repeat until the gray stack is empty. This is the tri-color idea: white (not reached), gray (reached, not traced), black (reached and traced).
3. **Sweep**: walk the list of all objects. Free every unmarked one; unmark the rest, ready for next time.

### The strings table is weak

The interning table holds every string, so if it counted as a root, no string would ever be freed. It's a **weak** reference: just before sweeping, remove every unmarked string from the table (leaving tombstones: your Module 04 deletion code finally gets a workout), so the sweep can free them.

### When to collect

Collect when the bytes allocated pass a threshold, then set the next threshold to a multiple of what survived (clox doubles it). The collector's work then grows with the live data, and a program with little live data and lots of garbage stays small.

### Stress testing

The bugs in a garbage collector are **missing roots**: an object that's still in use, but that the collector can't see, gets freed, and the crash comes later, somewhere else. Such bugs hide, because collections are rare. So the VM gets a **stress mode**: compiled with `-DSTRESS_GC`, it collects on *every* allocation. Under the sanitizers, a missing root then shows up immediately as a use-after-free, pointing straight at the problem.

## Practice

### Think it through

**1. Spot the missing root.** `+` on two strings does this. Under stress GC, what goes wrong?

```c
ObjString *b = AS_STRING(pop());
ObjString *a = AS_STRING(pop());
char *chars = ALLOCATE(char, a->length + b->length + 1);   // may collect!
memcpy(chars, a->chars, a->length);
...
```

<details><summary>Answer</summary>

After the two `pop()`s, nothing refers to `a` and `b` any more: they're not on the stack. If `ALLOCATE` runs a collection, it frees them, and the `memcpy` reads freed memory. Peek at the operands instead, and only pop them after the new string is made.

</details>

**2. Spot the missing root.** A new string is made, then added to the strings table with `table_set`. Under stress GC, the program sometimes prints garbage. Why?

<details><summary>Answer</summary>

`table_set` can grow the table, which allocates, which can collect. At that moment the new string isn't on the stack or anywhere else the collector looks, so it's freed, and the table stores a pointer to freed memory. Push it on the stack around the `table_set`, then pop it.

</details>

**3. Which of these are roots?** A global holding a string; a string constant in a function that's still being compiled; a string that only the strings table refers to; a closure in the frame that's currently running.

<details><summary>Answer</summary>

All except the third. The interning table is weak, so a string only it refers to is garbage. The function being compiled isn't reachable from the VM yet, so the compiler has to mark it.

</details>

### Try it in code

[`practice_08.c`](practice_08.c): marking with a gray stack, tracing, sweeping a linked list, and a collector with a missing root. Copy it into your project folder and run `python3 check.py practice 8`.

<details><summary>Hints</summary>

- `sweep`: walk with a pointer to the previous node's `next` field (`Obj **link`), so unlinking the head is no different from unlinking any other node.
- The FIX: count the roots it marks.

</details>

## Steps

Continue from Module 07.

### 1. Track every byte

All allocation already goes through one function (Module 03). Make it keep a running total of bytes allocated, and start a collection when an allocation would push the total past the threshold. With `-DSTRESS_GC` defined at compile time, start a collection on **every** allocation that grows memory.

### 2. The collector

Mark the roots, trace through the gray stack, remove unmarked strings from the strings table, and sweep. Set the next threshold from what's left. Your design; the [concepts](#concepts) above list the roots and what each kind of object refers to.

The gray stack itself must not be allocated through your tracked allocator (or growing it could start a collection in the middle of a collection). Plain `realloc` is fine.

### 3. Find every missing root

Add a stress build to your `Makefile` (the command line starts with a tab), and add `$(NAME)-stress` to `clean`:

```make
stress: $(SRC) $(HDR)
	$(CC) $(CFLAGS) -g -fsanitize=address,undefined -DSTRESS_GC $(SRC) -o $(NAME)-stress -lm
```

Then `make stress` and run your programs with `./glim-stress`. Each `heap-use-after-free` points at an object something was still using. Usual suspects: strings being joined or interned, a closure being filled in, native functions' names and objects while they're being defined, the compiler's functions, and any value you pop before allocating.

### 4. Speed

The self-check times three programs in the fast (`-O2`) build. They should each take about a second or less on a typical laptop; the limit is 8 seconds:

- `fib(30)`: calls and arithmetic,
- a 10-million-step `while` loop: global variable access and jumps,
- a million string joins: allocation, interning, and the collector.

If one is slow, profile it: `perf` on Linux (`perf record ./glim prog.glim`, then `perf report`), or Instruments on macOS.

## Make it yours

- **Tuning.** The initial threshold and the growth factor trade memory for time. Print the number of collections and the peak memory, and find the settings you like.
- **Your stress mode**: also try collecting every *N* allocations, which finds different bugs faster.
- **GC statistics**: `--gc-log` that prints each collection, how much it freed, and how long it took.

## Check your work

```sh
python3 check.py practice 8
python3 check.py 8
```

The self-check:

1. reruns every earlier program, compiled with `-DSTRESS_GC` under the sanitizers,
2. runs two programs that make hundreds of megabytes of garbage (300,000 strings of 1 KB, and 200,000 closures) in the fast build, and measures their peak memory: it must stay under 64 MB,
3. times the three speed tests.

## Stuck?

- **Peak memory is hundreds of megabytes**: the collector never runs (is the threshold check wired into your allocator?), or the strings table is keeping every string alive (remove unmarked strings before sweeping).
- **`heap-use-after-free` in the stress build**: a missing root. The report shows where the object was freed (inside your sweep) and, more usefully, where it was *allocated*. Ask what was holding that object at the moment of the collection, and why the collector couldn't see it.
- **A collection during compilation frees constants**: mark the chain of functions the compiler is building.
- **The run is fine under stress but crashes normally**: the threshold logic allocates or collects at a bad moment that stress mode happens to avoid. Rare, but check what your allocator does when `new_size` is 0 or smaller than `old_size`.
- **Too slow**: collecting too often (is the next threshold growing?), or hashing whole strings more than once each.

<details><summary>Hint 1</summary>

Give every object an `is_marked` flag in its header. `mark_object(obj)`: if NULL or already marked, return; otherwise set the flag and push it onto the gray stack. `mark_value(v)` calls `mark_object` only for object values.

</details>

<details><summary>Hint 2</summary>

`blacken_object(obj)` switches on the type: a closure marks its function and each upvalue; a function marks its name and every constant; a closed upvalue marks its `closed` value; strings and natives have nothing to mark.

</details>

<details><summary>Hint 3</summary>

`table_remove_white(&vm.strings)` loops over the entries and deletes every key whose object isn't marked. Call it after tracing and before sweeping, so the table never holds a pointer to a freed string.

</details>

## Resources

- [*Crafting Interpreters*, chapter 26: Garbage Collection](https://craftinginterpreters.com/garbage-collection.html): roots, tri-color marking, weak tables, stress testing, and tuning. Read it before you start; it's the whole module.
- [Wikipedia: Tracing garbage collection](https://en.wikipedia.org/wiki/Tracing_garbage_collection): mark-sweep compared with copying, generational and incremental collectors.
- [Clang: AddressSanitizer](https://clang.llvm.org/docs/AddressSanitizer.html): how the sanitizer finds use-after-free, and how to read its reports.

## Challenges (optional)

- **NaN boxing**: pack every value into 8 bytes, using the spare bits of a NaN double ([*Crafting Interpreters*, chapter 30](https://craftinginterpreters.com/optimization.html)). Measure the speed-up on the three benchmarks.
- A **generational** collector: most objects die young, so collect young objects more often.
- Make the collector **incremental**, so a collection never pauses the program for long.

## You built a virtual machine

That's a complete language implementation: a scanner, a single-pass compiler to bytecode, a stack VM with call frames and closures, your own hash tables, and a garbage collector, all in C, and all checked for memory errors. It's the same architecture as the VMs inside Python and Lua.

From here, see the project's [Going further](../../README.md#going-further) ideas: classes, NaN boxing, faster dispatch, or compiling to native code.
