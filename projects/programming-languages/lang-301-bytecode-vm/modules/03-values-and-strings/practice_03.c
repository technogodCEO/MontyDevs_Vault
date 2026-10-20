// Practice for Module 03: Values and Strings.
//
// Fill in each function, then test them all from your project folder:
//
//     python3 check.py practice 3
//
// Replace each "Your code here" comment with your code. The checker compiles
// this file with the sanitizers on. Don't add a main() function.

#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// A tagged union: `kind` says which member of `as` is in use.
typedef enum { V_NIL, V_BOOL, V_NUMBER, V_STRING } Kind;

typedef struct {
  Kind kind;
  union {
    bool boolean;
    double number;
    const char *string;
  } as;
} Val;

// 1. Are two values equal? Values of different kinds never are. Two nils
//    are. Strings are equal when their TEXT is the same, even if they're at
//    different addresses.
bool values_equal(Val a, Val b) {
  // Your code here
  return false;
}

// 2. Write a number as text into `buffer` (which has room for `size` bytes),
//    the way your language prints numbers:
//      - a whole number has no decimal point: 3, -6, 12345678
//      - any other number uses the SHORTEST text that reads back as exactly
//        the same double: 2.5, 0.30000000000000004 (for 0.1 + 0.2)
//    snprintf(buffer, size, "%.*g", precision, n) writes n with `precision`
//    significant digits, and strtod() reads text back into a double. Try
//    precisions from 1 up to 17 (17 always reads back exactly).
void format_number(double n, char *buffer, size_t size) {
  // Your code here
}

// 3. Return a new string (from malloc) holding `a` followed by `b`, ending
//    with a NUL. The caller frees it.
char *concat(const char *a, const char *b) {
  // Your code here
  return NULL;
}

// 4. FIX THE BUG: repeat("ab", 3) should return a new string "ababab".
//    It looks right, but the sanitizer disagrees. Why?
char *repeat(const char *s, int times) {
  size_t length = strlen(s);
  char *out = malloc(length * times);
  for (int i = 0; i < times; i++) {
    memcpy(out + i * length, s, length);
  }
  return out;
}
