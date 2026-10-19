// Practice for Module 01: Scanning.
//
// Fill in each function, then test them all from your project folder:
//
//     python3 check.py practice 1
//
// Each function says what it should do. Replace the "Your code here" comment
// and the placeholder return with your code. The checker compiles this file
// with the sanitizers on, so reading past the end of a string, or forgetting
// to free memory, counts as a failure even if the answer looks right.
//
// Don't add a main() function: the checker brings its own.

#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

// 1. How many characters at the start of `text` make up a name?
//    A name starts with a letter or _, and goes on with letters, digits or _.
//    Return 0 if `text` doesn't start with a name.
//
//    identifier_length("score = 1") is 5
//    identifier_length("_x2+y")     is 3
//    identifier_length("2x")        is 0
int identifier_length(const char *text) {
  // Your code here
  return 0;
}

// 2. Scan a number at the start of `text`: digits, then optionally a '.'
//    followed by at least one more digit. Store its value in *value and
//    return how many characters it used. If `text` doesn't start with a
//    digit, return 0 and leave *value alone.
//
//    scan_number("12.5x", &v)   returns 4, v = 12.5
//    scan_number("7.", &v)      returns 1, v = 7   (a '.' with no digit after isn't part of it)
//    scan_number("3.14.15", &v) returns 4, v = 3.14
//    scan_number(".5", &v)      returns 0
//
//    strtod() from <stdlib.h> turns text into a double, and it stops by
//    itself at the first character that can't be part of a number.
int scan_number(const char *text, double *value) {
  // Your code here
  return 0;
}

// 3. Skip whitespace and comments. Return a pointer to the first character
//    that isn't a space, tab, '\r', newline, or part of a // comment (a
//    comment runs to the end of its line). Add 1 to *line for every newline
//    you skip.
//
//    skip_space("  // hi\n\tx", &line) returns a pointer to the x, line goes up by 1
//    skip_space(" / 2", &line)         returns a pointer to the /  (one / isn't a comment)
const char *skip_space(const char *text, int *line) {
  // Your code here
  return text;
}

// 4. FIX THE BUG: copy_lexeme() should return a new, NUL-terminated copy of
//    the `length` characters starting at `start`. The caller frees it.
//    Run the checker to see what the sanitizer says, then fix it.
char *copy_lexeme(const char *start, int length) {
  char *copy = malloc(length);
  memcpy(copy, start, length);
  copy[length] = '\0';
  return copy;
}
