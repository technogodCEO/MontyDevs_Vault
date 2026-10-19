# Module 03: Values and Strings

**Goal:** your VM handles every kind of value: booleans, `nil`, numbers and strings. Strings live on the heap, `+` joins them, comparisons and `!` work, type errors are runtime errors, and every byte allocated is freed.

## Concepts

### A tagged union

A value can now be one of several types, so each `Value` carries a **tag** saying which, plus a **union** holding the data:

```c
typedef enum { VAL_BOOL, VAL_NIL, VAL_NUMBER, VAL_OBJ } ValueType;

typedef struct {
  ValueType type;
  union {
    bool boolean;
    double number;
    Obj *obj;      // anything that lives on the heap
  } as;
} Value;
```

A union's members share the same memory, so a `Value` is 16 bytes however many types you add. Reading the wrong member is a bug C won't catch for you, so wrap access in small macros or `static inline` functions (`IS_NUMBER(v)`, `AS_NUMBER(v)`, `NUMBER_VAL(n)`), and check the tag before every `AS_`.

### Objects on the heap

Numbers fit inside a `Value`. Strings don't: they can be any length. So a string is an **object** allocated on the heap, and the `Value` holds a pointer to it. Every object starts with a shared header, so any object can be handled through an `Obj *`:

```c
typedef struct Obj {
  ObjType type;
  struct Obj *next;   // every object, in one linked list
} Obj;

typedef struct {
  Obj obj;            // must be first, so an ObjString * is also an Obj *
  int length;
  char *chars;
} ObjString;
```

Putting `Obj` first is C's version of inheritance: a pointer to a struct can be converted to a pointer to its first member, and back.

### Owning memory

Who frees a string? For now: the VM, at exit. Every object goes on the VM's linked list when it's allocated, and freeing the VM walks the list and frees each one. In Module 08, the garbage collector will free objects much sooner, using the same list.

### Strings in the source

The scanner left a string's lexeme exactly as written: `"two\nlines"` is 12 characters, with quotes and a backslash. The compiler turns it into the real string: strip the quotes, and turn each escape (`\n`, `\t`, `\"`, `\\`) into the character it stands for.

## Practice

### Think it through

**1. Predict the output.**

```
print !0;
print 1 == true;
print "3" + "4";
print nil == false;
print !!"";
```

<details><summary>Answer</summary>

```
false
false
34
false
true
```

Only `false` and `nil` are falsy, so `!0` is `false` and `""` is truthy. Values of different types are never equal. `+` on two strings joins them.

</details>

**2. Spot the problem.** This compares two values. Which programs give the wrong answer?

```c
bool values_equal(Value a, Value b) {
  return memcmp(&a, &b, sizeof(Value)) == 0;
}
```

<details><summary>Answer</summary>

Two problems. A `Value` has **padding** bytes between `type` and the union, and unused bytes in the union (a `bool` uses 1 of 8), and those bytes can hold anything, so two equal booleans can compare unequal. And two strings with the same text, in different objects, have different pointers, so `"ab" + "c" == "abc"` would be `false`. Compare by type, then by the right member, and compare strings by their characters (until Module 04 gives you something better).

</details>

**3. Spot the problem.** This joins two strings for `+`. What's wrong?

```c
char chars[256];
memcpy(chars, a->chars, a->length);
memcpy(chars + a->length, b->chars, b->length);
return make_string(chars, a->length + b->length);
```

<details><summary>Answer</summary>

Two strings longer than 256 characters in total overflow the stack array (the self-check joins two 30,000-character strings). And if `make_string` keeps the pointer instead of copying, it's keeping a pointer to a stack array that's gone when the function returns. Allocate exactly `length + 1` bytes on the heap, and add the `'\0'`.

</details>

### Try it in code

[`practice_03.c`](practice_03.c): equality on a tagged union, printing numbers the way your language does, joining strings, and a missing-terminator bug. Copy it into your project folder and run `python3 check.py practice 3`.

<details><summary>Hints</summary>

- `values_equal`: `switch` on the kind once you know both kinds match.
- `format_number`: check for a whole number first (`n == floor(n)`, for numbers small enough to print exactly). Otherwise loop `precision` from 1 to 17 and stop at the first that reads back as `n`.
- The FIX: what does `strlen` (or `strcmp`) look for at the end of a string?

</details>

## Steps

Continue from Module 02.

### 1. Values

Make the stack and the constant pool hold tagged-union `Value`s. Add `nil`, `true` and `false` (as instructions like `OP_NIL`, `OP_TRUE`, `OP_FALSE`, or as constants: your call).

| Expression | Rule | Runtime error if... |
| --- | --- | --- |
| `-a` | negation | `a` isn't a number |
| `!a` | `true` if `a` is falsy (`false` or `nil`) | never |
| `a + b` | add two numbers, or join two strings | it's anything else |
| `-` `*` `/` `%` | arithmetic | either isn't a number (and `/` or `%` by 0) |
| `<` `<=` `>` `>=` | compare two numbers | either isn't a number |
| `==` `!=` | equal if same type and same value; strings by their text | never |

Runtime errors exit with code 70, with `line N` in the message; output printed before the error still appears. The REPL reports the error and carries on.

**Printing:** `true`, `false` and `nil` print as **your** spellings. Strings print their text, without quotes.

### 2. Strings

- String literals, with escapes turned into real characters.
- Strings are heap objects. Store the length, and keep a `'\0'` after the characters too, so you can hand them to C functions.
- `+` makes a new string. Any length: the self-check joins two 30,000-character strings and a chain of 500.

### 3. Free everything

Every object goes on the VM's object list, and freeing the VM frees all of them. Every chunk, every array and the source buffer are freed too. The checked build runs LeakSanitizer (on Linux and WSL), and a single leaked byte fails the check.

**Allocate through one function.** Route every `malloc`, `realloc` and `free` through one function in `memory.c`, like clox's `reallocate(pointer, old_size, new_size)`. In Module 08 the garbage collector hooks in there, and it needs to see every allocation.

## Make it yours

- **Your type errors.** "Operands must be numbers." works. "Can't add a number to a string" is friendlier. Show the values?
- **Instruction choices.** Do you add `OP_NOT_EQUAL`, `OP_LESS_EQUAL` and `OP_GREATER_EQUAL`, or compile them as two instructions (`EQUAL` + `NOT`)? Fewer instructions means a simpler VM; more means fewer dispatches. Measure it later.
- **String layout.** clox stores characters in a separate allocation. A **flexible array member** (`char chars[];` at the end of the struct) stores them in the same allocation as the object: one `malloc` instead of two (see the challenges).

## Check your work

```sh
python3 check.py practice 3
python3 check.py 3
```

## Stuck?

- **A leak report pointing at your string code**: some string is allocated but never put on the object list, or the list isn't walked when the VM is freed. Strings made by `+` are the usual culprits.
- **`heap-buffer-overflow` in `strlen` or `printf`**: a string without its `'\0'`. Allocate `length + 1` and set the last byte.
- **`runtime error: load of value 190, which is not a valid value for type 'bool'`** (UBSan): you read `as.boolean` from a value that isn't a boolean. Check the tag first.
- **The line number in a runtime error is wrong**: the line comes from the instruction that *failed*. After reading an opcode, `ip` has already moved on, so the failing instruction is at `ip - 1` (minus its operand bytes, if you index from the end).

<details><summary>Hint 1</summary>

Write `is_falsey(value)` once, and use it for `!`. Write `values_equal(a, b)` once, and use it for `==` and `!=`. Small helpers like these are where language rules live, so they're worth testing on their own.

</details>

<details><summary>Hint 2</summary>

For type errors in binary operators, **peek** at the operands before popping them: check `IS_NUMBER(peek(0)) && IS_NUMBER(peek(1))`, report the error if not, and only then pop. (In Module 08 that habit matters for another reason: values still on the stack are safe from the garbage collector.)

</details>

<details><summary>Hint 3</summary>

Two string constructors cover everything: `copy_string(chars, length)`, which allocates a new buffer and copies (for literals, whose characters live in the source), and `take_string(chars, length)`, which takes ownership of a buffer you already allocated (for `+`, which builds the result in a fresh buffer).

</details>

## Resources

- [*Crafting Interpreters*, chapter 18: Types of Values](https://craftinginterpreters.com/types-of-values.html): the tagged union and its macros.
- [Chapter 19: Strings](https://craftinginterpreters.com/strings.html): objects, the object list, and freeing at exit. clox's strings have no escapes; ours do.
- [Wikipedia: Tagged union](https://en.wikipedia.org/wiki/Tagged_union): the same idea in other languages (Rust's `enum`, TypeScript's discriminated unions).

## Challenges (optional)

- Store string characters in the same allocation as the object, with a flexible array member.
- Add a `--stats` flag that prints, at exit, how many objects and bytes your VM allocated, and the most it had at once. You'll use it in Module 08.
- Make `print` take more than one value: `print "x is", x;`.

## Next

Continue to [Module 04: Hash Tables and Globals](../04-hash-tables-and-globals/).
