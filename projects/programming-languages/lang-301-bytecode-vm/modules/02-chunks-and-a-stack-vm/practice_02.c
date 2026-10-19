// Practice for Module 02: Chunks and a Stack VM.
//
// Fill in each function, then test them all from your project folder:
//
//     python3 check.py practice 2
//
// Replace each "Your code here" comment with your code. The checker compiles
// this file with the sanitizers on, so a buffer overflow or a leak fails a
// problem even if the answer looks right. Don't add a main() function.

#include <stdint.h>
#include <stdlib.h>

// A growable array of ints, like the ones your chunk uses for its code,
// line numbers and constants.
typedef struct {
  int count;      // how many values are in use
  int capacity;   // how many values there's room for
  int *values;
} IntArray;

// Already done: an empty array has no memory yet.
void int_array_init(IntArray *array) {
  array->count = 0;
  array->capacity = 0;
  array->values = NULL;
}

// 1. Add a value to the end. When the array is full, grow it: to a capacity
//    of 8 the first time, then double it each time after that. Use realloc().
//    (After 1000 pushes, the capacity should be 1024.)
void int_array_push(IntArray *array, int value) {
  // Your code here
}

// 2. Free the array's memory and make it empty again (as int_array_init does).
//    Freeing an empty array must be safe too.
void int_array_free(IntArray *array) {
  // Your code here
}

// 3. A tiny stack VM. `code` is a list of instructions:
//      OP_PUSH n   push constants[n]  (the byte after OP_PUSH is n)
//      OP_ADD, OP_SUB, OP_MUL
//                  pop two values, push the result. The value pushed FIRST
//                  is the left operand: PUSH 10, PUSH 2, SUB gives 8.
//      OP_NEG      pop one value, push it negated
//      OP_RETURN   return the value on top of the stack
//    Use an array of 256 doubles for the stack. Programs are always correct,
//    so you don't need to check for errors.
enum { OP_PUSH, OP_ADD, OP_SUB, OP_MUL, OP_NEG, OP_RETURN };

double run_bytes(const uint8_t *code, const double *constants) {
  // Your code here
  return 0;
}

// 4. FIX THE BUG: this push for an array of doubles works for a few values,
//    then the sanitizer complains. Find out why, and fix it.
typedef struct {
  int count;
  int capacity;
  double *values;
} DoubleArray;

void double_array_push(DoubleArray *array, double value) {
  if (array->count == array->capacity) {
    array->capacity = array->capacity < 8 ? 8 : array->capacity * 2;
    array->values = realloc(array->values, array->capacity);
  }
  array->values[array->count] = value;
  array->count++;
}
