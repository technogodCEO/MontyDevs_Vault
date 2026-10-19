# Module 04: Tests and Structure

**Goal:** a test suite you run with `npm test`: unit tests for your dice module, and a test that runs a command with a fake interaction you build yourself.

## Concepts

### Why test a bot?

So far you've tested by hand: deploy, restart, type a command, read the reply. That's slow, and it only checks what you remember to try. An automated **test** is a small program that runs your code with known input and checks the output. A whole suite runs in a second, every time you change something, so you find out at once when a change breaks something that used to work. (That's exactly what `check.ts` has been doing for you. Now you write your own.)

### `node:test` and `assert`

Node has a test runner built in. A test file imports what it tests and describes what should happen:

```ts
import { test } from "node:test";
import assert from "node:assert/strict";
import { parseDice } from "../src/lib/dice.ts";

test("d20 is one twenty-sided die", () => {
  assert.deepEqual(parseDice("d20"), { ok: true, value: { count: 1, sides: 20, modifier: 0 } });
});
```

| Assertion | Passes when |
| --- | --- |
| `assert.equal(actual, expected)` | the two are the same value (`===`): numbers, strings, booleans |
| `assert.deepEqual(actual, expected)` | objects or arrays with the same contents |
| `assert.ok(value)` | `value` is truthy |
| `assert.match(text, /regex/)` | the text matches |
| `assert.throws(() => ...)` | the function throws |
| `await assert.rejects(promise)` | the Promise rejects (note the `await`) |

Run every file ending in `.test.ts` with `npm test` (the `node --test` script from Module 00). Tests can be `async`, and the runner waits for them.

Group related tests with `describe` and `it` (also from `node:test`) if you like. The output then reads like a list of facts about your code.

### What to test

Good tests check the cases that are easy to get wrong, not just the obvious one:

- **Edges:** the smallest and largest allowed values, and one past them (`100d6` and `101d6`).
- **Failures:** bad input gives a useful error, not a crash.
- **Each branch:** every `if` in the code has a test that goes each way.

And every test must be able to **fail**. A test that passes whatever the code does is worse than none, because it makes you trust broken code. A good habit: after writing a test, break the code on purpose and watch the test fail.

### Code you can test

Some code is hard to test: anything random, anything that depends on the time, anything that talks to Discord. The fix is the same each time: **don't let the code reach out for those things; pass them in.** That's **dependency injection**, and you've already done it once:

```ts
rollDice(spec, rng)        // the test passes a fake rng
new Cooldown(60_000, now)  // the test passes a fake clock (Module 05)
execute(interaction, ctx)  // the test passes a fake interaction and context
```

The real bot passes the real thing (`Math.random`, `Date.now`, the real interaction). The test passes something it controls.

This also explains the project's shape. **`src/lib/`** holds logic with no Discord in it, which is easy to test thoroughly. **`src/commands/`** holds thin glue: read options, call the logic, reply. Keep commands thin, and most of your bot is easy to test.

### Fakes

A **fake** is a stand-in object that has just enough of the real thing for the code under test. `/roll`'s `execute` only touches `interaction.options.getString` and `interaction.reply`, so a fake interaction needs only those two:

```ts
const replies: unknown[] = [];
const fake = {
  options: { getString: () => "1d6+100" },
  reply: async (message: unknown) => { replies.push(message); },
};
await roll.execute(fake as unknown as ChatInputCommandInteraction, ctx);
```

`fake` obviously isn't a full `ChatInputCommandInteraction` (the real type has hundreds of properties), so TypeScript refuses to pass it. `as unknown as ChatInputCommandInteraction` says "trust me". That's the right call in a test, and almost never in real code. If `execute` later uses something the fake doesn't have, the test fails, and you add it to the fake.

## Practice

### Think it through

**1. Which of these pass?**

```ts
assert.equal(2 + 2, 4);
assert.equal([1, 2], [1, 2]);
assert.deepEqual([1, 2], [1, 2]);
assert.deepEqual({ a: 1, b: 2 }, { b: 2, a: 1 });
```

<details><summary>Answer</summary>

The first, third and fourth. `equal` uses `===`, and two arrays are never `===` unless they are the same array, even with the same contents. `deepEqual` compares contents, and the order of an object's keys doesn't matter.

</details>

**2. Spot the problem.** This test passes, even though `fetchUser` never rejects. Why?

```ts
test("unknown users are rejected", () => {
  assert.rejects(fetchUser("nobody"));
});
```

<details><summary>Answer</summary>

`assert.rejects` returns a Promise, and nobody waits for it. The test function finishes straight away, so the test passes before the check has even happened. It needs `async () => { await assert.rejects(...); }`. (Node may print a warning about the failure later, attached to no test at all.)

</details>

**3. Predict the output.**

```ts
const defaults = { volume: 5, tags: ["new"] };
const copy = { ...defaults };
copy.volume = 9;
copy.tags.push("music");
console.log(defaults.volume, defaults.tags);
```

<details><summary>Answer</summary>

`5 [ 'new', 'music' ]`. The spread `{ ...defaults }` copies the object's top level only. `volume` is a number, so the copy gets its own. `tags` is an array, so the copy gets a reference to the *same* array. This is a **shallow copy**. Practice problem 4 is this bug.

</details>

### Try it in code

[`practice_04.ts`](practice_04.ts) has `checkClamp()` (you write the tests: the checker runs them against a correct clamp and five broken ones), a `Cooldown` class with an injected clock, `makeSequenceRng()`, and a **FIX THE BUG**. Copy it next to `check.ts` and run `node check.ts practice 4`.

Keep your `Cooldown` and `makeSequenceRng`: you'll use them in your bot.

<details><summary>Hint: checkClamp()</summary>

Each broken clamp gets a different thing wrong, so you need a test that catches each. Check a value above the range, below it, inside it, exactly on each edge, and one that isn't a whole number. If a broken one gets through, the checker says what it does wrong.

</details>

<details><summary>Hint: Cooldown</summary>

Keep a `Map<string, number>` of when each key was last used. `remaining(key)` is how long until `lastUsed + ms`, but never below 0 (and 0 for keys never used). `tryUse` is then "if `remaining` is 0, record `now()` and return true". Declare each field in the class body and set it in the constructor.

</details>

<details><summary>Hint: makeSequenceRng()</summary>

Return an arrow function that remembers a counter between calls (a **closure**): declare `let i = 0;` before the `return`, and use `values[i++ % values.length]` inside it. The `%` makes it wrap around.

</details>

<details><summary>Hint: FIX THE BUG</summary>

The copy is shallow (see question 3). `structuredClone(DEFAULT_SETTINGS)` makes a deep copy, or copy the array yourself: `{ ...DEFAULT_SETTINGS, tags: [...DEFAULT_SETTINGS.tags] }`.

</details>

## Steps

### 1. Test the dice

Create `tests/dice.test.ts`, with at least five tests for `src/lib/dice.ts`. Cover:

- a few kinds of good input, checking the exact `DiceSpec`
- bad input, checking `ok` is `false` (and that it doesn't throw)
- the limits, on each side of each one
- `rollDice` with a fake `rng`, checking the exact rolls and total (`makeSequenceRng` from the practice makes this easy)

Run them:

```sh
npm test
```

Then break `parseDice` on purpose (change a limit from `100` to `1000`, say) and run them again. A test should fail, and its message should tell you what went wrong. Put the code back.

### 2. Move logic out of commands

Look at the command you wrote yourself in Module 02. Is there logic in its `execute` (picking, calculating, formatting) that doesn't need Discord? Move it into a function in `src/lib/`, with any randomness passed in, and make the command call it. Then write tests for that function.

### 3. Test a command

Create `tests/roll-command.test.ts`. Build a fake interaction (see the concepts), run `/roll`'s `execute` with it, and check the reply:

```ts
import { test } from "node:test";
import assert from "node:assert/strict";
import type { ChatInputCommandInteraction } from "discord.js";
import roll from "../src/commands/roll.ts";

test("/roll replies with the total", async () => {
  // Your fake interaction here, with getString returning "1d6+100"...
  await roll.execute(fake as unknown as ChatInputCommandInteraction);
  // ...and an assert that the reply contains a number from 101 to 106.
});
```

(Since `roll` is defined with `satisfies Command`, its `execute` takes only the parameters it actually declared. If your `/roll` doesn't declare `ctx`, call it with just the interaction. Commands that use `ctx` need a fake context as well.)

### 4. Your turn: test the failure path

Add a test that runs `/roll` with nonsense dice and checks the reply is **ephemeral**. The fake records whatever `reply` was given, so check its `flags` include `MessageFlags.Ephemeral`.

## Make it yours

- Write the test names as sentences about your bot ("rolling 0 dice is refused"). `describe("parseDice", ...)` groups them nicely.
- Add tests for every command you've written, and every function in `src/lib/`.
- Try `node --test --experimental-test-coverage` to see which lines of your code no test runs.

## Check your work

```sh
node check.ts 4
```

The checker runs `node --test` and needs at least 5 passing tests and no failing ones. It also checks your tests import `src/lib/dice.ts` and at least one file in `src/commands/`.

## Stuck?

- **`npm test` finds no tests**: test files must end in `.test.ts`, and be inside the project (the checker looks in `tests/`).
- **`Cannot find module '../src/lib/dice.ts'`**: paths in `tests/` are relative to the test file, so `../src/...`.
- **`Conversion of type ... may be a mistake`**: cast through `unknown`: `fake as unknown as ChatInputCommandInteraction`.
- **`TypeError: interaction.something is not a function`** in a test: your fake is missing something `execute` uses. Add it.
- **A test passes even when you break the code**: check you `await` async assertions, and that the test actually calls the code you changed.
- **`Expected 1 arguments, but got 2`** when calling `execute`: see the note in step 3.

<details><summary>Hint 1: a fake that records replies</summary>

Push whatever `reply` is given into an array, so the test can look at it after `execute` finishes. Make `reply` `async`, because `execute` awaits it.

</details>

<details><summary>Hint 2: checking the reply</summary>

The reply might be a string or an object with `content` (or `embeds`), depending on how you wrote `/roll`. Turn it into searchable text with `JSON.stringify(replies[0])`, then `assert.match(text, /10[1-6]/)`.

</details>

<details><summary>Hint 3: checking for ephemeral</summary>

```ts
const sent = replies[0] as { flags?: number };
assert.equal(sent.flags, MessageFlags.Ephemeral);
```

If you combine flags (rare), check the bit instead: `assert.ok((sent.flags ?? 0) & MessageFlags.Ephemeral)`.

</details>

## Resources

- [Node.js docs: Test runner](https://nodejs.org/api/test.html): `test`, `describe`, hooks like `beforeEach`, mocking, and the options of `node --test`.
- [Node.js docs: Assert](https://nodejs.org/api/assert.html): every assertion, with what each one compares.
- [Martin Fowler: Mocks Aren't Stubs](https://martinfowler.com/articles/mocksArentStubs.html): the classic article on fakes, stubs and mocks. Read the first half for the vocabulary.

## Challenges (optional)

- Use `beforeEach` to build a fresh fake interaction for every test in a file.
- Write a small `makeFakeInteraction(options)` helper in `tests/helpers.ts` and reuse it across command tests.
- Test the central error handler: build the client with `createBot()`, emit a fake interaction with `client.emit(Events.InteractionCreate, fake)`, and check the error reply. (This is how `check.ts` does it.)

## Next

Continue to [Module 05: XP and a Database](../05-xp-and-a-database/).
