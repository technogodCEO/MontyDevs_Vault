/*
 * Practice for Module 04: testing, and code you can test.
 *
 * Copy this file into your bot's folder (next to check.ts), fill in each
 * function, and test your answers with:
 *
 *     node check.ts practice 4
 *
 * Hints are in the lesson, under "Try it in code".
 */

import assert from "node:assert/strict";

// 1. Write the TESTS this time. `clamp(n, lo, hi)` should return n, moved
//    into the range lo..hi: clamp(15, 0, 10) is 10, clamp(-3, 0, 10) is 0,
//    clamp(4, 0, 10) is 4.
//    Use assert.equal(actual, expected) to check clamp. checkClamp must:
//    - finish without an error for a correct clamp
//    - throw (an assert fails) for each of 5 broken clamps the checker has
//    Think about which inputs a lazy or careless clamp gets wrong.
export function checkClamp(clamp: (n: number, lo: number, hi: number) => number): void {
  // Your code here
  throw new Error("TODO");
}

// 2. A cooldown that remembers when each key (for example a user id) was
//    last used. It takes the clock as a function, so a test can control time.
//    - tryUse(key): true (and start the cooldown) if the key is ready;
//      false if it was used less than `ms` milliseconds ago.
//    - remaining(key): how many ms until the key is ready again (0 if ready).
//    You'll need fields to keep `ms`, `now` and the times. Note that
//    `constructor(private ms: number)` isn't allowed here: see the lesson.
export class Cooldown {
  constructor(ms: number, now: () => number = Date.now) {
    // Your code here
    throw new Error("TODO");
  }

  tryUse(key: string): boolean {
    // Your code here
    throw new Error("TODO");
  }

  remaining(key: string): number {
    // Your code here
    throw new Error("TODO");
  }
}

// 3. A fake random number generator for tests: it returns the values in
//    order, then starts again from the first.
//    const rng = makeSequenceRng([0.1, 0.5]); rng(), rng(), rng() -> 0.1, 0.5, 0.1
export function makeSequenceRng(values: number[]): () => number {
  // Your code here
  throw new Error("TODO");
}

// 4. FIX THE BUG: every server should get its own settings. But when one
//    server adds a tag, it shows up in servers created later too.
export interface Settings {
  prefix: string;
  tags: string[];
}

const DEFAULT_SETTINGS: Settings = { prefix: "!", tags: ["new"] };

export function newSettings(): Settings {
  return { ...DEFAULT_SETTINGS };
}
