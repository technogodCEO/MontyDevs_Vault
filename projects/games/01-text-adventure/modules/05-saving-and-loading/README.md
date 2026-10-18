# Module 05: Saving and Loading

**Goal:** a `save` command writes the player's progress to a file, and `load` brings it back, even after the game has been closed.

## Concepts

### Files

Everything in your program disappears when it stops. To keep something, you write it to a file. Python's `with open(...)` opens a file and closes it again automatically:

```python
with open("notes.txt", "w") as file:    # "w" = write (replaces the file)
    file.write("Hello!")

with open("notes.txt") as file:         # no mode = read
    text = file.read()
```

### JSON

Files hold text, but your game state is lists and dictionaries. **JSON** is a text format that looks almost exactly like Python dictionaries and lists, and Python's `json` module converts between the two:

```python
import json

data = {"room": "beach", "inventory": ["key"]}
with open("save.json", "w") as file:
    json.dump(data, file)               # Python -> file

with open("save.json") as file:
    data = json.load(file)              # file -> Python
```

Open `save.json` in your editor afterwards. It's readable text.

### Handling errors with `try` and `except`

If the player types `load` before ever saving, `open()` fails with a `FileNotFoundError` and the game crashes. `try`/`except` lets you catch that and respond instead:

```python
try:
    with open("save.json") as file:
        data = json.load(file)
except FileNotFoundError:
    print("There's no saved game yet.")
```

### What needs saving?

Only the parts of the game that **change**. Room names, descriptions and exits are written in your code, so they're the same every time. The player's room, their inventory, and the items in each room do change, so those get saved.

## Practice

Warm up on this module's ideas before you use them in your game.

### Think it through

Try each one in your head (or on paper) first, then click **Answer** to check.

**1. Predict the output.**

```python
import json
print(json.dumps({"hp": 10, "items": ["sword"], "alive": True}))
```

<details><summary>Answer</summary>

```
{"hp": 10, "items": ["sword"], "alive": true}
```

`json.dumps` turns Python data into a JSON string (`json.dump`, without the `s`, writes it to a file instead). It looks almost the same as Python, but JSON always uses double quotes and writes `True` as `true`.

</details>

**2. Predict the output.**

```python
def min_max(numbers):
    return min(numbers), max(numbers)

low, high = min_max([4, 9, 1])
print(low, high)
```

<details><summary>Answer</summary>

`1 9`. Returning two values separated by a comma gives back a tuple, and `low, high = ...` unpacks it into two variables. `load_game()` does the same thing with the room and the inventory.

</details>

### Try it in code

[`practice_05.py`](practice_05.py) has small problems to solve in Python: saving and loading settings, a bug to fix, and a high-score saver.

1. Copy `practice_05.py` into your game folder, next to `check.py`.
2. Fill in each function where it says `# Your code here`. Problems marked **FIX THE BUG** already have code: find what's wrong and fix it.
3. Test your answers:
   ```sh
   python check.py practice 5
   ```
   Each problem shows `[PASS]`, `[TODO]` (not started yet) or `[NOT YET]` with a hint, so you can do them in any order.

Stuck? Example answers are in [`solution/practice_05.py`](solution/practice_05.py).

## Steps

Continue in your `adventure.py` from Module 04. (Code badly broken, or skipped a module? Copy [Module 04's solution](../04-locks-and-winning/solution/adventure.py) into your folder and carry on from there.)

1. **Import `json`.** At the very top of your file, add:
   ```python
   import json
   ```
   And under your other settings (like `goal_room`), add the name of the save file:
   ```python
   SAVE_FILE = "savegame.json"
   ```

2. **Write `save_game()`.**
   ```python
   def save_game(current_room, inventory):
       # Each room's items can change, so save them under the room's key.
       room_items = {}
       for key in rooms:
           room_items[key] = rooms[key]["items"]

       data = {
           "current_room": current_room,
           "inventory": inventory,
           "room_items": room_items,
       }
       with open(SAVE_FILE, "w") as file:
           json.dump(data, file)
       print("Game saved.")
   ```
   Add a `save` command to your loop that calls it. Play a little, save, and open `savegame.json` to see what was written.

3. **Your turn: write `load_game()`.** It should:
   1. Open `SAVE_FILE` and read it with `json.load()`. If the file doesn't exist, print a message and `return None`.
   2. Put each room's items back: loop over `data["room_items"]` and set `rooms[key]["items"]` for each key.
   3. Return the saved room and inventory: `return data["current_room"], data["inventory"]`.

   Returning two values separated by a comma gives back a **tuple**, which you can unpack into two variables at once.

4. **Your turn: add the `load` command.** In your loop, call `load_game()`. If it didn't return `None`, unpack the result into `current_room` and `inventory`, and describe the room so the player knows where they are:
   ```python
   loaded = load_game()
   if loaded is not None:
       current_room, inventory = loaded
       describe(current_room)
   ```

5. **Test it properly.** Take an item, move somewhere, `save`, then `quit`. Start the game again, type `load`, and check your room and inventory came back. Also try `load` in a folder with no save file.

6. **Update `help`** with `save` and `load`.

That's the whole game! Read your `adventure.py` from top to bottom and add comments anywhere a friend might get lost.

## Make it yours

- **Multiple save slots:** let `save` and `load` take a name, like `save before-boss`, and use it in the file name.
- **Save anything else you've added**, such as a move counter, visited rooms or a score. Add it to the `data` dictionary and restore it in `load_game()`.
- **Share it.** Send your `adventure.py` to a friend, or put it on GitHub (see [Git and GitHub basics](../../../../../guides/git-and-github.md)).

## Check your work

```sh
python check.py 5
```

The checker plays in a temporary folder, so it won't overwrite your own save file.

## Stuck?

- **`NameError: name 'json' is not defined`**: add `import json` at the top of the file.
- **`TypeError: Object of type set is not JSON serializable`** (or similar): JSON only understands strings, numbers, `True`/`False`, `None`, lists and dictionaries. Convert anything else, like a set, to a list before saving.
- **`TypeError: cannot unpack non-iterable NoneType object`**: you unpacked the result of `load_game()` without checking for `None` first.
- **Loading puts you in the right room, but items are wrong**: make sure `load_game()` restores `room_items` into `rooms`, not just the player's inventory.
- **Can't find `savegame.json`**: it's created in the folder your terminal is in when you run the game, which might not be your game's folder.

## Resources

- [Python docs: Reading and writing files](https://docs.python.org/3/tutorial/inputoutput.html#reading-and-writing-files): the official guide. Read the part about `with`, and the section on saving structured data with `json`.
- [Python docs: Handling exceptions](https://docs.python.org/3/tutorial/errors.html#handling-exceptions): how `try`/`except` works, with more examples.
- [JSON.org](https://www.json.org/json-en.html): the whole JSON format on one page.

## Challenges (optional)

- Save automatically every time the player moves, so they never lose progress.
- Move your world out of the code: put `rooms` in a `world.json` file and load it at the start. Now you can write new adventures without touching Python.
- Make your game fully replayable: when the player wins, ask whether they'd like to play again.

## You did it!

You've built a complete text adventure: a game loop, a world, items, puzzles, a win condition and save files. Those same ideas, state and a loop that updates it, are at the core of almost every game.

Want to keep going? See [Going further](../../README.md#going-further) for ideas, or pick another project from the [vault](../../../../../README.md).
