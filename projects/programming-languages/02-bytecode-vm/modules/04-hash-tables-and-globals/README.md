# Module 04: Hash Tables and Globals

**Goal:** your own hash table, used twice: to **intern** strings, so two equal strings are always the same object, and to store **global variables**. `let`, assignment and undefined-variable errors all work.

## Concepts

### Hash tables, from scratch

C has no dictionary type, so you'll write one. A hash table is an array of **entries** (slots). To find a key, **hash** it to a number, and use that number (modulo the capacity) as the index to look at first.

Two keys can land on the same slot: a **collision**. This VM uses **open addressing with linear probing**: if the slot is taken by another key, try the next one, then the next, wrapping around at the end, until you find the key or an empty slot. Everything lives in one flat array, which is fast because neighbouring slots share a cache line.

**Load factor.** As the table fills, probe sequences get long. When `count / capacity` would pass a limit (0.75 is the usual choice), allocate a bigger array and re-insert every entry: their positions all change, since they depend on the capacity.

**Deleting needs tombstones.** If you empty a slot in the middle of a probe sequence, every key after it becomes unreachable: a search stops at the first empty slot. So deleting leaves a **tombstone**: a slot that's empty for inserting but not for searching. Tombstones count toward the load factor, or a table full of them would make searches loop forever.

**The hash function.** [FNV-1a](https://en.wikipedia.org/wiki/Fowler%E2%80%93Noll%E2%80%93Vo_hash_function) is short, fast and good enough: start from a fixed number, and for each byte, XOR it in and multiply by a prime. Compute each string's hash **once**, when the string is made, and store it in the string object.

**Power-of-two capacities** let you replace `hash % capacity` with `hash & (capacity - 1)`, which is much cheaper. (Only for powers of two!)

### String interning

If the VM keeps every string in a table, and *always* looks a string up before making a new one, then there's only ever one object for each piece of text. Then:

- string equality is **pointer** equality: one comparison, however long the strings,
- and looking up a variable by name can compare pointers too.

That's **interning**. The cost: every new string (from a literal or `+`) is hashed and looked up first.

### Global variables

Globals are a hash table from name (an interned string) to value. Because globals are looked up when the code **runs**, not when it's compiled, a function can use a global that's defined later in the file. That's late binding, and it's why the instructions for globals carry the **name** (as a constant), not a slot number.

## Practice

### Think it through

**1. Spot the problem.** A table deletes keys by setting the slot's key to `NULL`. The keys `"a"`, `"b"` and `"c"` all hash to slot 3, and were inserted in that order, so they're in slots 3, 4 and 5. What happens after deleting `"b"`?

<details><summary>Answer</summary>

Looking up `"c"` starts at slot 3 (`"a"`, not it), moves to slot 4, finds it empty, and stops: "not found", though `"c"` is right there in slot 5. That's why deletion leaves a tombstone instead.

</details>

**2. Predict the output.**

```
let a = 1;
let a = a + 1;
print a;
b = 5;
```

<details><summary>Answer</summary>

`2`, then a runtime error on line 4: assigning to `b`, which was never declared. Redeclaring a global replaces it, and the initializer `a + 1` reads the *old* `a` before the new one is defined. An assignment never creates a variable.

</details>

**3. Spot the problem.** With interning, a VM compares strings with `==` on their pointers. A student's `+` builds the joined string with `malloc` and makes an `ObjString` from it directly, without going through the strings table. What breaks?

<details><summary>Answer</summary>

`"ab" + "c" == "abc"` becomes `false`: the joined string is a new object, not the interned `"abc"`. And looking up a global by a name made at runtime would fail. Every way of making a string must go through the table.

</details>

### Try it in code

[`practice_04.c`](practice_04.c): FNV-1a, a probing `find_entry` with tombstones, deleting, and a wraparound bug. Copy it into your project folder and run `python3 check.py practice 4`.

<details><summary>Hints</summary>

- `fnv1a`: cast each byte to `uint8_t` before XORing it in. A `char` above 127 is negative on most machines, and would XOR in a sign-extended value.
- `find_entry`: loop forever (the table always has an empty slot); `return` from inside. Keep a `Entry *tombstone = NULL` for the first one you pass.
- The FIX: write out the slot numbers the loop visits for a table of 8, starting at 6.

</details>

## Steps

Continue from Module 03.

### 1. The hash table

Write a hash table from string keys to `Value`s, with open addressing, linear probing and tombstones. Operations: get, set (returning whether the key is new), and delete. Spec:

- It grows when it would go past a load factor of your choosing (0.75 is a good start), and growing re-inserts every live entry (dropping the tombstones).
- It works for any number of entries: the self-check keeps 1,000 globals and 600 strings.
- Each string stores its hash, computed once with FNV-1a (or another hash function you justify to yourself).

### 2. Interning

Keep every string in a VM-wide strings table. Before making a string, look its text up there (by length, hash and characters), and reuse the existing object if there is one. Then make string equality a pointer comparison.

### 3. Globals

| Code | Behaviour |
| --- | --- |
| `let x = v;` | defines the global `x`. Redefining one that exists replaces it. |
| `let x;` | defines `x` as `nil` |
| `x` | its value, or a runtime error if `x` isn't defined |
| `x = v` | sets `x` and has the value `v`. A runtime error if `x` isn't defined. Right-associative: `a = b = 3` sets both. |

Compile errors: a `let` without a name, or without its `;`; an invalid assignment target: `1 = 2`, `(a) = 2`, `a + b = 3`. That last one is subtle in a single-pass compiler: by the time it sees `=`, it has already compiled `a + b`. Only allow `=` when the expression so far is a lone variable name, which in a Pratt parser means passing a "can assign" flag down to the prefix rule.

In the REPL, globals last from one line to the next, even after an error.

## Make it yours

- **Your table's tuning.** Load factor, growth rate, minimum capacity. Measure lookups per second with different settings.
- **Probing.** Linear probing is simple. Quadratic probing or Robin Hood hashing spread clusters out. Try one.
- **Your hash function.** FNV-1a, or something else (djb2, a SipHash, ...). The self-check doesn't care.

## Check your work

```sh
python3 check.py practice 4
python3 check.py 4
```

## Stuck?

- **The program hangs** (the checker reports a timeout): `find_entry` loops forever, because the table has no empty slots. Is the load factor check using the count *including* tombstones?
- **A global "disappears" after many more are defined**: growing the table copied entries to the old positions instead of re-finding each one in the new array, or kept tombstones as if they were live.
- **`heap-use-after-free` right after the table grows**: you're holding an `Entry *` from before the array was reallocated.
- **`"ab" + "c" == "abc"` is false**: see Think it through, question 3.

<details><summary>Hint 1</summary>

Keep `count` as "live entries plus tombstones". Then `set` only increases it when it fills a truly empty slot (not when it reuses a tombstone), and the load factor check stays honest.

</details>

<details><summary>Hint 2</summary>

Interning needs a lookup that compares *text*, since there's no string object yet to compare pointers with: something like `table_find_string(table, chars, length, hash)`. Everywhere else (globals), the keys are already interned, so `find_entry` can compare pointers.

</details>

<details><summary>Hint 3</summary>

In `parse_precedence`, compute `bool can_assign = precedence <= PREC_ASSIGNMENT;`, pass it to the prefix rule, and after the infix loop, `if (can_assign && match(TOKEN_EQUAL)) error("Invalid assignment target.");`. The variable rule only consumes the `=` when `can_assign` is true. Then `a + b = 3` leaves the `=` unconsumed, and the error fires.

</details>

## Resources

- [*Crafting Interpreters*, chapter 20: Hash Tables](https://craftinginterpreters.com/hash-tables.html): the clox table, tombstones and interning, step by step.
- [Chapter 21: Global Variables](https://craftinginterpreters.com/global-variables.html): `let` (clox's `var`), and the `canAssign` trick.
- [Wikipedia: Open addressing](https://en.wikipedia.org/wiki/Open_addressing): linear, quadratic and double-hash probing compared.

## Challenges (optional)

- Make global lookups faster: give each global name an index at compile time, and store global values in an array (clox's chapter 21 challenge 2). Look-ups still need to fail at runtime for undefined names.
- Write a benchmark of a million table insertions and lookups, and compare two load factors.
- Add `const` declarations whose reassignment is a compile error.

## Next

Continue to [Module 05: Locals and Control Flow](../05-locals-and-control-flow/).
