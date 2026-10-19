// Practice for Module 04: Hash Tables and Globals.
//
// Fill in each function, then test them all from your project folder:
//
//     python3 check.py practice 4
//
// Replace each "Your code here" comment with your code. The checker compiles
// this file with the sanitizers on. Don't add a main() function.

#include <stdbool.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

// 1. The 32-bit FNV-1a hash of the first `length` bytes of `key`:
//      start with hash = 2166136261
//      for each byte: hash = hash XOR byte, then hash = hash * 16777619
//    Treat each byte as unsigned (0 to 255), and let the multiplication wrap
//    around (that's what uint32_t does).
uint32_t fnv1a(const char *key, int length) {
  // Your code here
  return 0;
}

// A slot in an open-addressing hash table:
//   empty:     key == NULL, tombstone == false
//   tombstone: key == NULL, tombstone == true   (something was deleted here)
//   in use:    key != NULL
typedef struct {
  const char *key;
  int value;
  bool tombstone;
} Entry;

// 2. Find where `key` lives, or where it should go. `capacity` is a power of
//    two. Start at index fnv1a(key) & (capacity - 1) and step forward one
//    slot at a time, wrapping from the last slot to slot 0:
//      - a slot holding `key` (compare with strcmp): return it
//      - a tombstone: remember the first one, and keep going
//      - an empty slot: the key isn't there. Return the first tombstone you
//        passed if there was one (so it gets reused), else this empty slot.
//    The table always has at least one empty slot.
Entry *find_entry(Entry *entries, int capacity, const char *key) {
  // Your code here
  return NULL;
}

// 3. Delete `key`: turn its slot into a tombstone. Return true if the key was
//    there. (Use find_entry().)
bool table_delete(Entry *entries, int capacity, const char *key) {
  // Your code here
  return false;
}

// 4. FIX THE BUG: slot_of() looks for `key` in a table of keys (NULL means an
//    empty slot), starting at index `start`, and returns its index, or -1 if
//    it reaches an empty slot first. It misses some keys. Which ones, and why?
int slot_of(const char **keys, int capacity, int start, const char *key) {
  int index = start;
  for (;;) {
    if (keys[index] == NULL) return -1;
    if (strcmp(keys[index], key) == 0) return index;
    index = (index + 1) % (capacity - 1);
  }
}
