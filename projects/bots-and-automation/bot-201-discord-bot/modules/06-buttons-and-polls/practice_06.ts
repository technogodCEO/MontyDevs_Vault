/*
 * Practice for Module 06: button ids and showing results.
 *
 * Copy this file into your bot's folder (next to check.ts), fill in each
 * function, and test your answers with:
 *
 *     node check.ts practice 6
 *
 * Hints are in the lesson, under "Try it in code".
 */

// 1. Every button carries a custom id (a string of up to 100 characters).
//    Encode a vote as "vote:<pollId>:<index>", and decode it again.
//    encodeVote("42", 1)    ->  "vote:42:1"
//    decodeVote("vote:42:1") ->  { pollId: "42", index: 1 }
//    decodeVote must return null for anything encodeVote would never make:
//    other prefixes, a missing or empty part, extra parts, an index that isn't
//    a whole number 0 or more.
export function encodeVote(pollId: string, index: number): string {
  // Your code here
  throw new Error("TODO");
}

export function decodeVote(customId: string): { pollId: string; index: number } | null {
  // Your code here
  throw new Error("TODO");
}

// 2. Draw a bar `width` characters wide, with `#` for the filled part
//    (rounded to the nearest character) and `-` for the rest.
//    progressBar(0.5) -> "#####-----"     progressBar(0.25, 8) -> "##------"
//    Treat anything below 0 (or NaN) as 0, and above 1 as 1.
export function progressBar(fraction: number, width = 10): string {
  // Your code here
  throw new Error("TODO");
}

// 3. Count the votes. `votes` maps each user id to the option they chose.
//    Ignore votes for options that don't exist.
//    tally(new Map([["u1", 0], ["u2", 2], ["u3", 0]]), 3)  ->  [2, 0, 1]
export function tally(votes: Map<string, number>, optionCount: number): number[] {
  // Your code here
  throw new Error("TODO");
}

// 4. FIX THE BUG: return the index of every option with the most votes
//    (more than one if there's a tie), or [] if nobody has voted.
//    winners([4, 1, 4]) -> [0, 2]       winners([0, 0]) -> []
export function winners(counts: number[]): number[] {
  const most = Math.max(...counts);
  return [counts.indexOf(most)];
}
