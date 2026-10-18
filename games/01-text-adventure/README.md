# Text Adventure

> Build your own playable text adventure game: explore rooms, collect items, solve puzzles and save your progress, all in a world you design.

**Difficulty:** Beginner
**Language:** Python. It's beginner-friendly, needs nothing extra installed, and its dictionaries and lists map neatly onto rooms and items.
**Estimated time:** 5–8 hours across all modules, plus 15–30 minutes of setup

## What you'll build

A game played by typing commands, in the style of classics like *Zork*:

```
=== The Lighthouse ===
A storm is rolling in, and the old lighthouse has gone dark.

== Stormy Beach ==
Cold waves crash against the rocks. A lighthouse towers to the north,
and a fishing shack leans against the wind to the east.
You see: shell
Exits: north, east
> go north
Something blocks the way north. Maybe you need an item.
> go east

== Fishing Shack ==
Nets and broken oars hang from the walls. It smells of salt and old rope.
You see: key, rope
Exits: west
> take key
You take the key.
```

That's the example world from the solutions. **Yours will be different.** You choose the setting, the rooms, the items, the puzzles and the ending.

## What you'll learn

- Loops, and how a game loop drives a program
- Dictionaries and lists, and using them to model a world
- Writing and calling functions
- Parsing what a user types
- Reading and writing files with JSON
- Handling errors with `try`/`except`

## Prerequisites

- You've written a little Python before and know what variables, `if` statements and functions are. You don't need to be confident with them yet.
- A computer you can install software on. [Module 00](modules/00-setup/) walks you through installing everything else.

## Make it yours

This isn't a copy-the-code tutorial. Each module shows you the new ideas with examples from *The Lighthouse*, then hands you parts to write yourself, and every module has a **Make it yours** section with ideas for your own world. A haunted school, a heist, a pizza delivery gone wrong: anything works.

The solutions are just one way to do it. The self-check doesn't look at your story at all; it reads your rooms and items and plays your game to make sure everything works.

## How to work through this project

1. Start with [Module 00: Setup](modules/00-setup/). It gets Python installed, the vault onto your computer, and your own game folder ready with `adventure.py` and [`check.py`](check.py).
2. Work through the modules **in order**. Each one continues from the code you wrote in the last, so by the end you've built the whole game.
3. At the end of each module, check your work from your game folder:
   ```sh
   python check.py 1      # use the module's number
   ```
4. Each module has an example `solution/`. Use it as a last resort, after the module's **Stuck?** section. If your code gets badly broken, you can copy the previous module's solution and carry on from there.

## Modules

| # | Module | What you'll do |
| --- | --- | --- |
| 00 | [Setup](modules/00-setup/) | Install Python, get the vault, and make your game folder |
| 01 | [The Game Loop](modules/01-the-game-loop/) | Greet the player and keep asking for commands until they quit |
| 02 | [Rooms and Movement](modules/02-rooms-and-movement/) | Build a world of connected rooms and walk around it |
| 03 | [Items and Inventory](modules/03-items-and-inventory/) | Fill rooms with items to take, drop and carry |
| 04 | [Locks and Winning](modules/04-locks-and-winning/) | Lock exits behind items, and add a way to win |
| 05 | [Saving and Loading](modules/05-saving-and-loading/) | Save progress to a file and load it back |

## Going further

Finished? Here are bigger ideas to make the game your own:

- **Characters:** people or creatures in rooms who say things when you `talk` to them, and maybe want an item.
- **Combat or health:** hazards that hurt the player, and items that heal.
- **A world file:** move your rooms into a JSON file so anyone can write new adventures for your engine.
- **Smarter parsing:** understand `pick up the key` and `walk north`, not just `take key` and `go north`.
- **Colour:** use the [`colorama`](https://pypi.org/project/colorama/) or [`rich`](https://pypi.org/project/rich/) library to make room names and items stand out.
- **Play the classics** for inspiration: read about [*Zork*](https://en.wikipedia.org/wiki/Zork), and browse the [Interactive Fiction Database](https://ifdb.org/) for games you can play in your browser.
