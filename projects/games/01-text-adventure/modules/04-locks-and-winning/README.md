# Module 04: Locks and Winning

**Goal:** some exits stay locked until the player is carrying the right item, and reaching a goal room wins the game.

## Concepts

### Optional dictionary keys with `.get()`

Only some rooms will have locked exits. If we write `room["locked"]` for a room without one, Python raises a `KeyError`. `.get()` lets us supply a fallback instead:

```python
locked = room.get("locked", {})   # an empty dictionary if there's no "locked" key
```

### Game state

Your game now has **state**: where the player is, what they're carrying, and what's in each room. Puzzles are just rules about state: "you can only go north *if* `"key"` is in your inventory". Winning is a rule too: "if `current_room` is the goal room, the game ends".

### Designing a puzzle

A good puzzle gives the player a goal they can see (a locked door) before they have the solution (the key). Make sure the solution is always reachable: a key locked behind its own door makes the game impossible to win. The checker plays through your game to make sure it can be won.

## Steps

Continue in your `adventure.py` from Module 03. (Code badly broken, or skipped a module? Copy [Module 03's solution](../03-items-and-inventory/solution/adventure.py) into your folder and carry on from there.)

1. **Plan the puzzle on your map.** Pick a goal room the player has to reach to win. Choose at least one exit to lock and which item opens it. Then trace a route on paper: start, find the item, reach the lock, reach the goal.

2. **Lock an exit.** In the room the locked exit leaves from, add a `"locked"` dictionary that maps the direction to the item it needs. The exit stays in `"exits"` as normal:
   ```python
   "beach": {
       "name": "Stormy Beach",
       "description": "...",
       "exits": {"north": "lighthouse", "east": "shack"},
       "items": ["shell"],
       "locked": {"north": "key"},
   },
   ```

3. **Set the goal.** Under `start_room`, add:
   ```python
   goal_room = "lantern"
   win_message = "You light the great lantern. You win!"
   ```
   Use your own goal room key and write your own ending.

4. **Check locks in `go()`.** `go()` needs to know what the player is carrying, so add an `inventory` parameter: `def go(current_room, direction, inventory):`. Then, after the check that the exit exists and before moving, add:
   ```python
   locked = rooms[current_room].get("locked", {})
   if direction in locked:
       needed = locked[direction]
       if needed not in inventory:
           print(f"Something blocks the way {direction}. Maybe you need an item.")
           return current_room
       print(f"You use the {needed}.")
   ```
   Update the call in `main()` to pass the inventory: `go(current_room, noun, inventory)`.

5. **Your turn: win the game.** In `main()`, right after the player moves, check whether `current_room` is the `goal_room`. If it is, print the `win_message` and end the loop. (You've already ended the loop once, in your `quit` command.)

6. **Play your game from start to finish.** Then hand it to a friend without telling them the solution. Watch where they get stuck.

## Make it yours

- **Give each lock its own message.** "The door is locked" is fine, but "The guard dog growls. It looks hungry." tells the player what they need without saying it outright. (One way: a `"lock_messages"` dictionary in the room, mapping direction to message.)
- **Locks don't have to be doors.** A dark staircase that needs a lamp, a river that needs a boat, a bouncer who needs a ticket: they're all the same code.
- **Chain your puzzles.** The key is behind a door that needs the crowbar, which is in the room that needs the lamp. Two or three steps is plenty.
- **Write an ending worth reaching.** It's the last thing the player reads.

## Check your work

```sh
python check.py 4
```

The checker works out the shortest way to win your game and prints it. If it says your game can't be won, look for an item that's only reachable through the lock it opens.

## Stuck?

- **`TypeError: go() missing 1 required positional argument: 'inventory'`**: you added the parameter to `go()` but didn't pass `inventory` where you call it.
- **The locked exit never opens**: the item name in `"locked"` must exactly match the name in the room's `"items"`, including spaces.
- **The locked exit is never locked**: make sure the lock check comes *before* the lines that move the player and `return new_room`.
- **The game doesn't end when you reach the goal**: check you're comparing `current_room` after it's been updated by `go()`, and that `goal_room` matches the room's key (not its name).

## Resources

- [Python docs: `dict.get`](https://docs.python.org/3/library/stdtypes.html#dict.get): the one-paragraph explanation of `.get()` and its default value.
- [Wikipedia: Interactive fiction](https://en.wikipedia.org/wiki/Interactive_fiction): the history of text adventures, and famous games whose puzzles are worth borrowing ideas from.

## Challenges (optional)

- Add a way to lose, like a room that ends the game if you enter without the right item.
- Make some items get used up when they open a lock (remove them from the inventory).
- Add a move counter and show the player's score at the end: fewer moves, better score.

## Next

Continue to [Module 05: Saving and Loading](../05-saving-and-loading/).
