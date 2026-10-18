# Module 03: Items and Inventory

**Goal:** rooms contain items the player can `take` and `drop`, and an `inventory` command lists what they're carrying.

## Concepts

### Lists

A list holds values in order, and you can change it after it's made:

```python
items = ["lamp", "rope"]
items.append("key")      # ["lamp", "rope", "key"]
items.remove("rope")     # ["lamp", "key"]
print("lamp" in items)   # True
```

Each room will get an `"items"` list, and the player will have an `inventory` list. Taking an item means removing it from one list and appending it to the other.

### Lists can be changed inside functions

When you pass a list to a function and the function changes it (with `.append()` or `.remove()`), the change sticks: the function is working on the same list, not a copy. That's why `take()` won't need to `return` anything.

Contrast that with `current_room` in Module 02. It's a string, and assigning a new string inside a function doesn't affect the caller, so `go()` had to `return` it.

### Empty lists are "falsy"

`if room["items"]:` is `True` when the list has something in it and `False` when it's empty. It's a short way to say `if len(room["items"]) > 0:`.

## Steps

Continue in your `adventure.py` from Module 02. (Fell behind? Copy this module's `starter/adventure.py` and carry on from there.)

1. **Add items to your rooms.** Give **every** room an `"items"` list. Leave it empty (`[]`) where there's nothing:
   ```python
   "shack": {
       "name": "Fishing Shack",
       "description": "Nets and broken oars hang from the walls.",
       "exits": {"west": "beach"},
       "items": ["key", "rope"],
   },
   ```
   Item names must be lowercase, because the player's commands are lowercased.

2. **Show items in `describe()`.** Before the exits line, add:
   ```python
   if room["items"]:
       print("You see: " + ", ".join(room["items"]))
   ```

3. **Give the player an inventory.** In `main()`, next to `current_room = start_room`, add:
   ```python
   inventory = []
   ```

4. **Write `take()`.**
   ```python
   def take(current_room, item, inventory):
       room_items = rooms[current_room]["items"]
       if item == "":
           print("Take what?")
       elif item not in room_items:
           print(f"There's no {item} here.")
       else:
           room_items.remove(item)
           inventory.append(item)
           print(f"You take the {item}.")
   ```
   Add a branch for it in your loop:
   ```python
   elif verb == "take":
       take(current_room, noun, inventory)
   ```
   Run the game, walk to an item, take it, and `look`. It should be gone from the room.

5. **Your turn: write `drop()`.** It's the mirror image of `take()`. Check that the player is actually carrying the item, then move it from `inventory` into the current room's items. Wire it up to a `drop` command.

6. **Your turn: write `inventory`.** Add a command that prints everything the player is carrying, or a message like "You aren't carrying anything." when the list is empty. Make `i` work as a shortcut. (Hint: `elif verb == "inventory" or verb == "i":`)

7. **Update `help`** to mention `take`, `drop` and `inventory`.

## Make it yours

- **Pick items that belong in your world.** A space station might have a keycard, a wrench and a suspicious sandwich. The next module uses items to unlock places, so include a few that could open or reveal something.
- **Not everything has to be useful.** A few red herrings (items that do nothing) make the world feel real.
- **Item names can be more than one word**, like `"rusty key"`, because the noun keeps all the words after the verb.

## Check your work

```sh
python check.py 3
```

## Stuck?

- **`KeyError: 'items'`**: at least one room doesn't have an `"items"` list. Every room needs one, even if it's `[]`.
- **`take Key` says there's no key**: the item in your dictionary has a capital letter. Make it lowercase.
- **`ValueError: list.remove(x): x not in list`**: you're removing an item without checking that it's there first. Check with `in` before calling `.remove()`.
- **The item is in your inventory but still shows in the room**: you appended it to `inventory` but didn't remove it from `room_items`.

## Resources

- [Python docs: More on lists](https://docs.python.org/3/tutorial/datastructures.html#more-on-lists): every list method in one place. `append`, `remove` and `in` are the ones used here.
- [Ned Batchelder: Facts and myths about Python names and values](https://nedbatchelder.com/text/names.html): explains *why* changing a list inside a function sticks. It's a deeper read; the first half is enough.

## Challenges (optional)

- Add `take all` to pick up everything in the room at once.
- Give each item a description and an `examine <item>` command. (Hint: a separate `item_descriptions` dictionary.)
- Limit how much the player can carry, and give a funny message when their hands are full.

## Next

Continue to [Module 04: Locks and Winning](../04-locks-and-winning/).
