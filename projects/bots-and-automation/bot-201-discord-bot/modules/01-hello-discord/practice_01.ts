/*
 * Practice for Module 01: Promises and async/await.
 *
 * Copy this file into your bot's folder (next to check.ts), fill in each
 * function, and test your answers with:
 *
 *     node check.ts practice 1
 *
 * Replace each `throw new Error("TODO")` with your code. The checker also
 * type-checks this file, so a TypeScript error counts as "not yet".
 * Hints are in the lesson, under "Try it in code".
 */

// 1. Return a promise that resolves after `ms` milliseconds.
//    `await sleep(500)` should pause for half a second.
export function sleep(ms: number): Promise<void> {
  // Your code here
  throw new Error("TODO");
}

// 2. Resolve with the promise's value if it settles within `ms` milliseconds.
//    If it takes longer, reject with an Error instead (any message).
//    If the promise itself rejects, reject with its error.
//    withTimeout(fetchSomething(), 2000)
export function withTimeout<T>(promise: Promise<T>, ms: number): Promise<T> {
  // Your code here
  throw new Error("TODO");
}

// 3. Call fetchOne for every id AT THE SAME TIME, and resolve with all the
//    results in the same order as `ids`. Three 100 ms fetches should take
//    about 100 ms in total, not 300.
export async function fetchAll<T>(ids: string[], fetchOne: (id: string) => Promise<T>): Promise<T[]> {
  // Your code here
  throw new Error("TODO");
}

// 4. FIX THE BUG: this should add up the lengths of every page's text.
//    TypeScript already knows what's wrong. Run `node check.ts practice 1`
//    and read its message.
export async function totalLength(urls: string[], fetchText: (url: string) => Promise<string>): Promise<number> {
  let total = 0;
  for (const url of urls) {
    const text = fetchText(url);
    total += text.length;
  }
  return total;
}
