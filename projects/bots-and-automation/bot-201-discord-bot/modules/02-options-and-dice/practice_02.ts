/*
 * Practice for Module 02: parsing input, and discriminated unions.
 *
 * Copy this file into your bot's folder (next to check.ts), fill in each
 * function, and test your answers with:
 *
 *     node check.ts practice 2
 *
 * Hints are in the lesson, under "Try it in code".
 */

// A function that can fail returns one of these instead of throwing.
// Check `result.ok` before you touch `value` or `error`.
export type Result<T> = { ok: true; value: T } | { ok: false; error: string };

// 1. Turn a duration like "1h30m", "90s" or "1h 5m 10s" into seconds.
//    - Units are h, m and s, in that order, each at most once.
//    - Ignore spaces around and between the parts, and upper/lower case.
//    - The total must be more than 0.
//    parseDuration("1h30m")  ->  { ok: true, value: 5400 }
//    parseDuration("soon")   ->  { ok: false, error: "..." }   (your message)
export function parseDuration(text: string): Result<number> {
  // Your code here
  throw new Error("TODO");
}

// 2. The other way round: 5400 -> "1h 30m", 90 -> "1m 30s", 3600 -> "1h".
//    Leave out parts that are 0, except that 0 itself is "0s".
export function formatDuration(seconds: number): string {
  // Your code here
  throw new Error("TODO");
}

// 3. Read a hex color for an embed: "#ff8800" or "ff8800" -> 0xff8800.
//    Also accept the 3-digit form: "#fa0" means "#ffaa00".
//    Anything else is an error.
export function parseColor(text: string): Result<number> {
  // Your code here
  throw new Error("TODO");
}

// Reads one number of seconds, like "15s". (This one already works.)
export function parseSeconds(text: string): Result<number> {
  const match = /^(\d+)s$/.exec(text.trim());
  return match ? { ok: true, value: Number(match[1]) } : { ok: false, error: `"${text}" isn't a number of seconds.` };
}

// 4. FIX THE BUG: add up a list like ["10s", "5s"] -> { ok: true, value: 15 }.
//    If any item is bad, return that item's error instead.
//    TypeScript spots the bug; the checker shows you its message.
export function totalSeconds(texts: string[]): Result<number> {
  let total = 0;
  for (const text of texts) {
    const result = parseSeconds(text);
    total += result.value;
  }
  return { ok: true, value: total };
}
