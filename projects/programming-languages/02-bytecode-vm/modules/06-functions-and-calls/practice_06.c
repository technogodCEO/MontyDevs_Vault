// Practice for Module 06: Functions and Calls.
//
// Fill in each function, then test them all from your project folder:
//
//     python3 check.py practice 6
//
// Replace each "Your code here" comment with your code. The checker compiles
// this file with the sanitizers on. Don't add a main() function.

#include <stdbool.h>
#include <stdio.h>
#include <string.h>

// A call stack with a fixed number of frames, like your VM's.
#define FRAMES_MAX 8

typedef struct {
  const char *name;   // the function's name, or NULL for the top-level script
  int return_ip;
  int slot_base;
} Frame;

typedef struct {
  Frame frames[FRAMES_MAX];
  int count;
} CallStack;

// 1. Push a new frame, or return false if the stack is full (a stack
//    overflow). Pop the top frame into *out, or return false if the stack is
//    empty.
bool push_frame(CallStack *stack, const char *name, int return_ip, int slot_base) {
  // Your code here
  return false;
}

bool pop_frame(CallStack *stack, Frame *out) {
  // Your code here
  return false;
}

// 2. Write a stack trace into `buffer` (room for `size` bytes, including the
//    NUL), innermost call first, one line each:
//        in inner()
//        in outer()
//        in script
//    If it doesn't fit, write as much as fits and end with a NUL: never
//    write past the end. An empty stack gives "".
void format_trace(const CallStack *stack, char *buffer, size_t size) {
  // Your code here
}

// 3. FIX THE BUG: arity_message() writes a message like
//        add() expected 2 arguments but got 3.
//    into `buffer`, which has room for `size` bytes. A long function name
//    writes past the end. Fix it so a message that's too long is cut short.
void arity_message(char *buffer, size_t size, const char *name, int expected, int got) {
  sprintf(buffer, "%s() expected %d arguments but got %d.", name, expected, got);
}
