/*
 * Practice for Module 03: errors you throw on purpose, and formatting replies.
 *
 * Copy this file into your bot's folder (next to check.ts), fill in each
 * function, and test your answers with:
 *
 *     node check.ts practice 3
 *
 * Hints are in the lesson, under "Try it in code".
 */

// An error whose message is safe to show to the user, like "You need to be
// in a server for that." (This one is done for you.)
export class UserError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "UserError";
  }
}

// 1. Decide what to tell the user when something goes wrong:
//    - a UserError: its message
//    - anything else (any other Error, a string, undefined...): "Something went wrong."
export function toReply(error: unknown): string {
  // Your code here
  throw new Error("TODO");
}

// 2. A UserError for cooldowns. new CooldownError(5) should have:
//    - message "Slow down! Try again in 5s."
//    - a `seconds` property: 5
//    - name "CooldownError"
//    (Replace the constructor's body. You'll need a `seconds` field too.)
export class CooldownError extends UserError {
  constructor(seconds: number) {
    super("");
    // Your code here
    throw new Error("TODO");
  }
}

// 3. Discord rejects messages over 2000 characters. Shorten `text` to at most
//    `max` characters, ending with "..." when anything was cut.
//    truncate("hello world", 8)  ->  "hello..."
//    truncate("hello", 10)       ->  "hello"
export function truncate(text: string, max: number): string {
  // Your code here
  throw new Error("TODO");
}

// 4. FIX THE BUG: return null if `text` is valid JSON, or the error message
//    if it isn't. It even works when you run it, but TypeScript rejects it.
export function jsonError(text: string): string | null {
  try {
    JSON.parse(text);
    return null;
  } catch (error) {
    return error.message;
  }
}
