// Practice for Module 08: Garbage Collection.
//
// Fill in each function, then test them all from your project folder:
//
//     python3 check.py practice 8
//
// Replace each "Your code here" comment with your code. The checker compiles
// this file with the sanitizers on. Don't add a main() function.

#include <stdbool.h>
#include <stdlib.h>

// A tiny heap: every object can point to up to 3 others, and all objects are
// on one linked list (through `next`) so the sweep can find them.
#define MAX_REFS 3

typedef struct Obj {
  bool marked;
  struct Obj *refs[MAX_REFS];   // NULL where there's no reference
  struct Obj *next;
  int id;
} Obj;

typedef struct {
  Obj *items[64];
  int count;
} GrayStack;

// 1. Mark an object: if it's NULL or already marked, do nothing. Otherwise
//    set `marked` and push it onto the gray stack, to trace later.
void mark(Obj *object, GrayStack *gray) {
  // Your code here
}

// 2. Trace: while the gray stack isn't empty, pop an object and mark()
//    everything it refers to.
void trace(GrayStack *gray) {
  // Your code here
}

// 3. Sweep: free every unmarked object, taking it out of the list. Unmark the
//    objects you keep, ready for the next collection. Return how many you
//    freed. Keep the survivors in their original order.
int sweep(Obj **objects) {
  // Your code here
  return 0;
}

// 4. FIX THE BUG: a whole (simple) collector in one function. It marks
//    everything reachable from the roots, then frees the rest. Sometimes it
//    frees objects that are still in use. Find the missing root.
static void mark_all(Obj *object) {
  if (object == NULL || object->marked) return;
  object->marked = true;
  for (int i = 0; i < MAX_REFS; i++) mark_all(object->refs[i]);
}

int collect_simple(Obj **objects, Obj **roots, int root_count) {
  for (int i = 1; i < root_count; i++) mark_all(roots[i]);

  int freed = 0;
  Obj **link = objects;
  while (*link != NULL) {
    Obj *object = *link;
    if (object->marked) {
      object->marked = false;
      link = &object->next;
    } else {
      *link = object->next;
      free(object);
      freed++;
    }
  }
  return freed;
}
