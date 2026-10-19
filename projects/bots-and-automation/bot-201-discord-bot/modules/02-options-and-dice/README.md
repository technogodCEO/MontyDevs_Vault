# Module 02: Options and Dice

**Goal:** a `/roll` command that understands dice like `3d8+2`, built on a dice module that reports bad input as a value instead of throwing, plus a command of your own that takes options.

## Concepts

### Command options

Options are the boxes Discord shows after a command's name. You declare them on the builder, and Discord checks their type before your bot ever sees them:

```ts
new SlashCommandBuilder()
  .setName("repeat")
  .setDescription("Say something several times")
  .addStringOption((option) =>
    option.setName("text").setDescription("What to say").setRequired(true))
  .addIntegerOption((option) =>
    option.setName("times").setDescription("How many times").setMinValue(1).setMaxValue(5));
```

In `execute`, you read them from `interaction.options`:

```ts
const text = interaction.options.getString("text", true);   // string
const times = interaction.options.getInteger("times");       // number | null
```

The second argument, `true`, means "this option is required". The type is then `string`, and discord.js throws if it's somehow missing. Without it, you get `null` when the user left the option out, and TypeScript makes you deal with that (`times ?? 1`).

| Builder method | Getter | Value |
| --- | --- | --- |
| `addStringOption` | `getString` | `string` (`.setChoices()` for a fixed list, `.setMaxLength()`) |
| `addIntegerOption` / `addNumberOption` | `getInteger` / `getNumber` | `number` (`.setMinValue()`, `.setMaxValue()`) |
| `addBooleanOption` | `getBoolean` | `boolean` |
| `addUserOption` | `getUser` | a `User` (Discord shows a member picker) |
| `addChannelOption`, `addRoleOption` | `getChannel`, `getRole` | a channel or role |

Required options must come before optional ones.

### Errors as values

What should `parseDice("banana")` do? It could `throw`. But "the user typed something silly" isn't a bug, it's normal, and exceptions have two problems for normal cases: nothing in a function's type says it can throw, so callers forget to catch, and every caller needs a `try`/`catch`.

Instead, return a **result** that is either a success or a failure, and let the type say so:

```ts
export type Result<T> = { ok: true; value: T } | { ok: false; error: string };
```

`|` makes a **union**: a `Result` is one shape *or* the other. The `ok` field, whose type is the literal `true` or `false`, tells them apart. That's a **discriminated union**. TypeScript won't let you read `value` until you've checked `ok`:

```ts
const result = parseDice(text);
result.value;            // error: 'value' doesn't exist on { ok: false; error: string }
if (!result.ok) {
  return result.error;   // here, result is the failure shape
}
result.value;            // here, it's the success shape
```

The compiler now reminds every caller that parsing can fail. Keep `throw` for bugs: things that should never happen.

### Randomness you can control

`Math.random()` returns a number from 0 (included) to 1 (not included). A fair roll of an `n`-sided die is `Math.floor(Math.random() * n) + 1`.

Random code is hard to test: what should a test expect? So `rollDice` will take the random number generator as a **parameter**, defaulting to `Math.random`:

```ts
export function rollDice(spec: DiceSpec, rng: () => number = Math.random) { ... }
```

The bot calls `rollDice(spec)`. A test calls `rollDice(spec, () => 0)` and knows every die shows 1. This is **dependency injection**, and Module 04 builds on it.

## Practice

### Think it through

**1. Predict the output.**

```ts
console.log(Number("12"), Number(""), Number("12abc"), parseInt("12abc"), Number(" 7 "));
```

<details><summary>Answer</summary>

`12 0 NaN 12 7`. `Number` rejects junk (`NaN`) but turns an empty string into `0`, and ignores spaces around the number. `parseInt` reads digits until it hits something else, so `"12abc"` becomes 12. When you turn a regex match into a number, think about which of these cases can reach your code. An optional part of a pattern that didn't match is `undefined`, not `""`.

</details>

**2. Spot the problem.** Why does TypeScript reject this?

```ts
const times = interaction.options.getInteger("times");
const message = "hi ".repeat(times);
```

<details><summary>Answer</summary>

`getInteger("times")` returns `number | null`, because an optional option can be left out. `repeat` needs a `number`. Either make the option required and use `getInteger("times", true)`, or give a default: `repeat(times ?? 1)`.

</details>

**3. Predict the output.**

```ts
type Shape = { kind: "circle"; radius: number } | { kind: "square"; side: number };

function area(shape: Shape): number {
  if (shape.kind === "circle") return Math.round(Math.PI * shape.radius ** 2);
  return shape.side ** 2;
}

console.log(area({ kind: "circle", radius: 2 }), area({ kind: "square", side: 3 }));
```

<details><summary>Answer</summary>

`13 9`. Inside the `if`, TypeScript knows `shape` is the circle, so `shape.radius` is allowed. After the `return`, only the square is left, so `shape.side` is too. This is the same narrowing you'll use with `Result`, on a field called `kind` instead of `ok`.

</details>

### Try it in code

[`practice_02.ts`](practice_02.ts) has `parseDuration()`, `formatDuration()`, `parseColor()` and a **FIX THE BUG**, all using `Result`. Copy it next to `check.ts` and run `node check.ts practice 2`.

<details><summary>Hint: parseDuration()</summary>

One regular expression can do most of the work. `(\d+)` captures digits, `\s*` allows spaces, and `(?: ... )?` makes a group optional without capturing it. Something like `/^(?:(\d+)\s*h)?\s*(?:(\d+)\s*m)?\s*(?:(\d+)\s*s)?$/`, run on the trimmed, lowercased text, matches each unit at most once, in order. Then check that at least one part matched, and that the total isn't 0. An unmatched group is `undefined`, so `Number(match[1] ?? 0)`.

</details>

<details><summary>Hint: formatDuration()</summary>

Work out hours, minutes and seconds with `Math.floor` and `%`, push the non-zero ones onto an array of strings, and `join(" ")`. The special case: if the array is empty, the answer is `"0s"`.

</details>

<details><summary>Hint: parseColor()</summary>

Remove a leading `#`, lowercase, and test against `/^[0-9a-f]{6}$/`. For the 3-digit form, double each character first. `parseInt(hex, 16)` reads hexadecimal.

</details>

<details><summary>Hint: FIX THE BUG</summary>

TypeScript is right: `result` might be the failure shape. Check `result.ok` first. What should the function return when it isn't? (You can return `result` itself: it's already the right type.)

</details>

## Steps

### 1. A shared `Result` type

Create `src/lib/result.ts` with the `Result<T>` type from the concepts, exported. Everything in `src/lib/` is plain TypeScript with no discord.js in it: that's what makes it easy to test.

### 2. The dice module

Create `src/lib/dice.ts`. The self-check imports it, so use these names exactly:

```ts
export interface DiceSpec {
  count: number;      // how many dice
  sides: number;      // sides on each die
  modifier: number;   // added to the total (can be negative)
}

export function parseDice(text: string): Result<DiceSpec>;
export function rollDice(spec: DiceSpec, rng?: () => number): { rolls: number[]; total: number };
```

**`parseDice`** reads dice notation:

| Input | Result |
| --- | --- |
| `d20` | 1 die with 20 sides (the count is optional) |
| `2d6` | 2 dice with 6 sides |
| `3d8+2`, `4d10 + 3` | a modifier, with or without spaces around the sign |
| `1d4-1` | a negative modifier |
| `  2D6  ` | spaces around the outside and capital letters are fine |

Everything else returns `{ ok: false, error }` with a message a user would understand: no dice (`banana`, `d`, `2d`), a dangling sign (`2d6+`), decimals (`1.5d6`), negative counts (`-2d6`), two signs (`2d6++1`), and anything outside the limits. Limits stop people asking your bot to roll a billion dice:

- 1 to 100 dice
- 2 to 1000 sides
- a modifier from -1000 to 1000

It must **never throw**, whatever the input.

**`rollDice`** rolls each die with `Math.floor(rng() * sides) + 1`, and returns every roll plus the total (the sum of the rolls plus the modifier). `rng` defaults to `Math.random`.

Try your functions before wiring them into the bot. Make a scratch file (don't put it in `src/`), say `try.ts`:

```ts
import { parseDice, rollDice } from "./src/lib/dice.ts";

for (const text of ["d20", "3d8+2", "banana", "101d6"]) {
  console.log(text, parseDice(text));
}
console.log(rollDice({ count: 3, sides: 6, modifier: 0 }));
```

and run `node try.ts`.

### 3. `/roll`

Create `src/commands/roll.ts`: a `/roll` command with a **required string option called `dice`**. It parses the option, and replies with the rolls and the total, for example `Rolled [4, 1, 6] + 2 = 13`. If parsing failed, reply with the error message instead.

Deploy (`npm run deploy`), restart, and roll some dice.

### 4. Your turn: a command with options

Write another command of your own that takes at least one option. Use at least one feature you haven't yet: `setChoices` for a fixed list, `setMinValue`/`setMaxValue` on a number, an optional option with a default, or a user option. Some ideas:

- `/choose options:pizza, tacos, sushi` picks one at random
- `/8ball question:...` answers mysteriously
- `/coin flips:3`, with flips limited to 1–10
- `/rate thing:...` rates anything out of 10 (the same thing always gets the same score, if you're clever)
- `/hug user:@someone`

## Make it yours

- Give `/roll` some personality: celebrate a natural 20, commiserate over a 1, show each die as an emoji.
- Support more notation: `4d6kh3` (keep the highest 3), `2d20adv` (roll twice, keep the best). Make sure plain dice still work.
- Your own command is a chance to make your bot useful to your friends specifically.

## Check your work

```sh
node check.ts 2
```

The checker calls `parseDice()` with good and bad input (it expects the exact `count`, `sides` and `modifier` above), calls `rollDice()` with fake random number generators, and runs `/roll dice:3d6+100` to check the total appears in the reply. It also checks some other command takes an option.

## Stuck?

- **`'result.value' ... Property 'value' does not exist`**: check `result.ok` before using `value`. That's the point of the union.
- **`Required options must be placed before non-required options`**: reorder the `add...Option` calls.
- **The option doesn't show in Discord**: re-run `npm run deploy` after changing a command's options.
- **`parseDice("2d6") returned {"ok":true,"value":{"count":"2",...}}`**: the regex gives you strings. Convert with `Number(...)`.
- **`Cannot find module '../lib/dice'`**: import with the extension, `../lib/dice.ts`.

<details><summary>Hint 1: a pattern for dice</summary>

Trim and lowercase the text, then match it against one regular expression with three parts: optional digits for the count, `d`, digits for the sides, and an optional group for a sign and more digits. Then check the limits on the numbers.

</details>

<details><summary>Hint 2: the regex</summary>

`/^(\d*)d(\d+)\s*(?:([+-])\s*(\d+))?$/`. `^` and `$` make it match the whole string. `match[1]` is the count (`""` when it's missing, so `d20` is one die), `match[2]` the sides, `match[3]` the sign or `undefined`, `match[4]` the modifier's digits.

</details>

<details><summary>Hint 3: putting parseDice together</summary>

```ts
const match = PATTERN.exec(text.trim().toLowerCase());
if (!match) return { ok: false, error: `"${text}" isn't dice. Try something like 2d6+1.` };
const count = match[1] ? Number(match[1]) : 1;
const sides = Number(match[2]);
const modifier = match[4] ? Number(match[4]) * (match[3] === "-" ? -1 : 1) : 0;
// ...then one `if` per limit, each returning { ok: false, error: ... }
return { ok: true, value: { count, sides, modifier } };
```

</details>

## Resources

- [discord.js Guide: Slash command options](https://discordjs.guide/slash-commands/advanced-creation.html): every option type, choices, and limits.
- [TypeScript Handbook: Discriminated unions](https://www.typescriptlang.org/docs/handbook/2/narrowing.html#discriminated-unions): the pattern behind `Result`.
- [regex101](https://regex101.com/): paste your pattern and test strings, and it explains every part. Pick the "ECMAScript (JavaScript)" flavour.

## Challenges (optional)

- Add autocomplete to one of your options (`.setAutocomplete(true)`): handle `interaction.isAutocomplete()` in your listener, and answer with `interaction.respond([...])`.
- Let `/roll` take several groups at once: `2d6 + 1d4 + 3`.
- Give `parseDice` precise errors: "Dice need at least 2 sides" rather than one generic message.

## Next

Continue to [Module 03: Embeds and Errors](../03-embeds-and-errors/).
