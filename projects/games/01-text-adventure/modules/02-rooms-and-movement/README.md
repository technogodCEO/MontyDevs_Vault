# Module 02: Rooms and Movement

**Goal:** a world of at least three connected rooms that the player can walk around with commands like `go north`, and a `look` command that describes where they are.

## Concepts

### Dictionaries

A dictionary stores values under keys, like words and definitions:

```python
room = {"name": "Kitchen", "description": "It smells like toast."}
print(room["name"])   # Kitchen
```

Dictionaries can hold other dictionaries. That's how we'll store the whole world: one big dictionary of rooms, where each room is its own dictionary.

```python
rooms = {
    "kitchen": {"name": "Kitchen", "exits": {"north": "hall"}},
    "hall":    {"name": "Hall",    "exits": {"south": "kitchen"}},
}
print(rooms["kitchen"]["exits"]["north"])   # hall
```

The exits are a dictionary too: each direction maps to the **key** of the room it leads to.

### Splitting commands into words

`"go north".split()` gives `["go", "north"]`. The first word is the action (the **verb**); the rest is what it acts on (the **noun**). `" ".join(words[1:])` glues the rest back together, so `go up the stairs` gives the noun `up the stairs`.

### Functions that return a value

A function can hand a result back with `return`. We'll write a `go()` function that returns the room the player ends up in, whether they moved or not.

### f-strings

An f-string puts values straight into text: `f"You can't go {direction}."`. The `f` before the quote is what makes it work.

## Practice

Warm up on this module's ideas before you use them in your game. Try each problem first, then click **Answer** to check.

**1. Predict the output.**

```python
pets = {"cat": "Mochi", "dog": "Biscuit"}
pets["fish"] = "Bubbles"
print(len(pets), pets["dog"])
```

<details><summary>Answer</summary>

`3 Biscuit`. Assigning to a new key (`"fish"`) adds it, so the dictionary has 3 entries. `pets["dog"]` looks up the value stored under `"dog"`.

</details>

**2. Predict the output.**

```python
words = "go up the stairs".split()
print(words[0])
print(" ".join(words[1:]))
print("".split())
```

<details><summary>Answer</summary>

```
go
up the stairs
[]
```

`words[1:]` is every word after the first. Splitting an empty string gives an empty list, which is why the game checks `len(words) == 0` before reading `words[0]`.

</details>

**3. Trace the map.** Starting in room `"a"`, the player types `go east`, then `go north`. Which room are they in? And what happens if the code then runs `world["c"]["exits"]["south"]`?

```python
world = {
    "a": {"exits": {"east": "b"}},
    "b": {"exits": {"west": "a", "north": "c"}},
    "c": {"exits": {}},
}
```

<details><summary>Answer</summary>

They end up in `"c"`: `east` from `a` leads to `b`, and `north` from `b` leads to `c`.

`world["c"]["exits"]["south"]` raises a `KeyError`, because `c` has no `"south"` exit. That's why `go()` checks `if direction not in exits` before looking it up.

</details>

**4. Write it.** Write a function `opposite(direction)` that returns the opposite of `north`, `south`, `east` or `west`, and `"?"` for anything else. Try it with a dictionary instead of a chain of `if`s.

<details><summary>Answer</summary>

```python
def opposite(direction):
    opposites = {"north": "south", "south": "north", "east": "west", "west": "east"}
    if direction in opposites:
        return opposites[direction]
    return "?"
```

(You'll meet a shorter way to write this, `opposites.get(direction, "?")`, in Module 04.) A function like this could check that every exit in your world has a matching way back.

</details>

## Steps

Continue in your `adventure.py` from Module 01. (Code badly broken, or skipped a module? Copy [Module 01's solution](../01-the-game-loop/solution/adventure.py) into your folder and carry on from there.)

1. **Sketch your map on paper first.** Draw at least three boxes for rooms and connect them with lines labelled with directions. Give each room a short lowercase key, like `beach` or `throne_room`. Remember that most exits go both ways: if the kitchen's `north` leads to the hall, the hall should probably have a `south` back to the kitchen.

2. **Build the `rooms` dictionary.** At the top of your file, above `def main():` and not indented, write out your map. Each room needs `"name"`, `"description"` and `"exits"`:
   ```python
   rooms = {
       "beach": {
           "name": "Stormy Beach",
           "description": "Cold waves crash against the rocks. A lighthouse "
                          "towers to the north.",
           "exits": {"north": "lighthouse"},
       },
       "lighthouse": {
           "name": "Lighthouse Hall",
           "description": "Your footsteps echo in the round stone hall.",
           "exits": {"south": "beach"},
       },
   }

   start_room = "beach"
   ```
   Use your own rooms. Two strings written next to each other inside brackets are joined into one, which is a handy way to split a long description over several lines. Directions must be lowercase, because we lowercase what the player types.

3. **Write `describe()`.** Below the rooms (and still above `main()`), add a function that prints a room:
   ```python
   def describe(room_key):
       room = rooms[room_key]
       print()
       print(f"== {room['name']} ==")
       print(room["description"])
       print("Exits: " + ", ".join(room["exits"]))
   ```
   `", ".join(...)` on a dictionary joins its keys, giving something like `north, east`.

4. **Track where the player is.** In `main()`, after your welcome message and before the loop, add:
   ```python
   current_room = start_room
   describe(current_room)
   ```

5. **Split commands into verb and noun.** Replace the `command = input(...)` line and your `if`/`elif` chain's conditions so they work on words:
   ```python
   words = input("> ").lower().split()
   if len(words) == 0:
       continue

   verb = words[0]
   noun = " ".join(words[1:])

   if verb == "quit":
       ...
   ```
   Change your other branches to check `verb` instead of `command`. The empty-input check is now the `len(words) == 0` line, so you can remove your old `""` branch.

6. **Write `go()`.** Add this function next to `describe()`:
   ```python
   def go(current_room, direction):
       exits = rooms[current_room]["exits"]
       if direction not in exits:
           print("You can't go that way.")
           return current_room
       new_room = exits[direction]
       describe(new_room)
       return new_room
   ```
   Then add a branch to your loop:
   ```python
   elif verb == "go":
       current_room = go(current_room, noun)
   ```
   Run it and walk around your world.

7. **Your turn: handle `go` with no direction.** Typing just `go` currently says "You can't go that way." Make it say something more helpful, like "Go where?", by checking for an empty `direction` at the start of `go()`.

8. **Your turn: add `look`.** Add a `look` command that describes the current room again. (You already have a function that does exactly this.) Add `look` and `go` to your `help` message too.

## Make it yours

- **Write descriptions that hint at exits.** "A door creaks open to the east" is more fun than reading the exit list.
- **Your directions don't have to be compass points.** `up`, `down`, `inside`, `portal`, `ladder` all work, because they're just dictionary keys.
- **One-way exits are allowed.** A slide, a trapdoor or a collapsing bridge can lead somewhere with no way back. Make sure the player can still reach every room. The checker will tell you if they can't.

## Check your work

```sh
python check.py 2
```

This also re-runs the Module 01 checks, to make sure nothing broke.

## Stuck?

- **`KeyError: 'hall'`**: an exit points to a room key that doesn't exist. Check the spelling. Keys must match exactly, including underscores.
- **`KeyError: 'name'`**: one of your rooms is missing a `"name"` (or `"description"`, or `"exits"`).
- **`go north` says you can't go that way, but there's an exit north**: check that the exit's direction is lowercase in your dictionary, and that you're using `noun` (not `verb`) as the direction.
- **`NameError: name 'rooms' is not defined`**: `rooms` must be at the top of the file, not indented inside a function.
- **`SyntaxError` near your rooms**: you're probably missing a comma between two entries, or a closing `}`. Every entry except the last one needs a comma after it. (A comma after the last one is fine too.)

## Resources

- [Python docs: Dictionaries](https://docs.python.org/3/tutorial/datastructures.html#dictionaries): the official introduction. The first few examples cover everything used here.
- [Python docs: Defining functions](https://docs.python.org/3/tutorial/controlflow.html#defining-functions): a refresher on `def` and `return`.
- [Real Python: f-strings](https://realpython.com/python-f-strings/): read the first section to see what else f-strings can do.

## Challenges (optional)

- Let the player type just `north` (or `n`) instead of `go north`.
- Show "You've been here before" when the player returns to a room. (Hint: keep a list of visited room keys.)
- Use Python's `textwrap` module to wrap long descriptions neatly at 70 characters.

## Next

Continue to [Module 03: Items and Inventory](../03-items-and-inventory/).
