// Practice for Module 07: Closures.
//
// Fill in each function, then test them all from your project folder:
//
//     python3 check.py practice 7
//
// Replace each "Your code here" comment with your code. The checker compiles
// this file with the sanitizers on. Don't add a main() function.

#include <stdlib.h>

// An upvalue points at a variable. While the variable is still on the stack
// it's "open" and `location` points at the stack slot. When it's "closed",
// the value moves into `closed` and `location` points there instead.
typedef struct Upvalue {
  double *location;
  double closed;
  struct Upvalue *next;   // the next open upvalue
} Upvalue;

// The open upvalues form a linked list sorted by slot address, HIGHEST
// address first (the top of the stack first).

// 1. Return the open upvalue for `slot`. If there's one already, return it,
//    so every closure shares the same variable. Otherwise make a new one with
//    malloc (closed = 0), insert it at the right place in the sorted list,
//    and return it.
Upvalue *capture(Upvalue **open, double *slot) {
  // Your code here
  return NULL;
}

// 2. Close every open upvalue whose slot is at `last` or above: copy the
//    value into `closed`, point `location` at `closed`, and take it off the
//    open list. (Don't free them: closures still use them.)
void close_upvalues(Upvalue **open, double *last) {
  // Your code here
}

// 3. FIX THE BUG: free every upvalue in a list. The sanitizer reports a
//    heap-use-after-free. Why?
void free_upvalues(Upvalue *head) {
  for (Upvalue *u = head; u != NULL; u = u->next) {
    free(u);
  }
}
