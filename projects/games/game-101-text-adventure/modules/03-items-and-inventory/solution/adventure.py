# adventure.py: The Lighthouse (Module 03 solution)
#
# This is ONE example of a finished Module 03. Your world, rooms and
# items should be your own.

# ---------------------------------------------------------------------------
# The world
# ---------------------------------------------------------------------------
# Every room is a dictionary, stored in `rooms` under a short key like "beach".
#   "name"        - the title shown when the player enters
#   "description" - what the player sees
#   "exits"       - which direction leads to which room (by its key)
#   "items"       - things lying around that can be picked up
rooms = {
    "beach": {
        "name": "Stormy Beach",
        "description": "Cold waves crash against the rocks. A lighthouse "
                       "towers to the north, and a fishing shack leans "
                       "against the wind to the east.",
        "exits": {"north": "lighthouse", "east": "shack"},
        "items": ["shell"],
    },
    "shack": {
        "name": "Fishing Shack",
        "description": "Nets and broken oars hang from the walls. It smells "
                       "of salt and old rope.",
        "exits": {"west": "beach"},
        "items": ["key", "rope"],
    },
    "lighthouse": {
        "name": "Lighthouse Hall",
        "description": "Your footsteps echo in the round stone hall. A spiral "
                       "staircase disappears into the darkness above.",
        "exits": {"south": "beach", "up": "lantern"},
        "items": ["lamp"],
    },
    "lantern": {
        "name": "Lantern Room",
        "description": "The great lantern sits in the middle of the room, "
                       "cold and dark, surrounded by windows facing the sea.",
        "exits": {"down": "lighthouse"},
        "items": [],
    },
}

# The key of the room the player starts in.
start_room = "beach"


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------
def describe(room_key):
    """Print everything the player can see in a room."""
    room = rooms[room_key]
    print()
    print(f"== {room['name']} ==")
    print(room["description"])
    # Only mention items if there are any. An empty list counts as False.
    if room["items"]:
        print("You see: " + ", ".join(room["items"]))
    print("Exits: " + ", ".join(room["exits"]))


def go(current_room, direction):
    """Try to move in a direction. Returns the room the player ends up in."""
    exits = rooms[current_room]["exits"]

    if direction == "":
        print("Go where?")
        return current_room
    if direction not in exits:
        print("You can't go that way.")
        return current_room

    new_room = exits[direction]
    describe(new_room)
    return new_room


def take(current_room, item, inventory):
    """Move an item from the room into the player's inventory."""
    room_items = rooms[current_room]["items"]

    if item == "":
        print("Take what?")
    elif item not in room_items:
        print(f"There's no {item} here.")
    else:
        # Lists can be changed in place, so these changes stick around
        # after the function ends. No need to return anything.
        room_items.remove(item)
        inventory.append(item)
        print(f"You take the {item}.")


def drop(current_room, item, inventory):
    """Move an item from the player's inventory into the room."""
    if item == "":
        print("Drop what?")
    elif item not in inventory:
        print(f"You aren't carrying a {item}.")
    else:
        inventory.remove(item)
        rooms[current_room]["items"].append(item)
        print(f"You drop the {item}.")


def show_inventory(inventory):
    if inventory:
        print("You are carrying: " + ", ".join(inventory))
    else:
        print("You aren't carrying anything.")


def show_help():
    print("Commands:")
    print("  look          - describe where you are")
    print("  go <place>    - move, e.g. 'go north'")
    print("  take <item>   - pick something up")
    print("  drop <item>   - put something down")
    print("  inventory     - list what you're carrying (or just 'i')")
    print("  help          - show this list")
    print("  quit          - stop playing")


# ---------------------------------------------------------------------------
# The game loop
# ---------------------------------------------------------------------------
def main():
    print("=== The Lighthouse ===")
    print("A storm is rolling in, and the old lighthouse has gone dark.")
    print("Type 'help' to see what you can do.")

    current_room = start_room
    # The inventory starts empty. take() and drop() add and remove items.
    inventory = []
    describe(current_room)

    playing = True
    while playing:
        # Split the command into words: "take key" -> ["take", "key"]
        words = input("> ").lower().split()
        if len(words) == 0:
            continue

        verb = words[0]
        noun = " ".join(words[1:])

        if verb == "quit":
            print("Thanks for playing!")
            playing = False
        elif verb == "help":
            show_help()
        elif verb == "look":
            describe(current_room)
        elif verb == "go":
            current_room = go(current_room, noun)
        elif verb == "take":
            take(current_room, noun, inventory)
        elif verb == "drop":
            drop(current_room, noun, inventory)
        elif verb == "inventory" or verb == "i":
            show_inventory(inventory)
        else:
            print(f"I don't understand '{verb}'. Type 'help' for commands.")


# Only start the game when this file is run directly.
if __name__ == "__main__":
    main()
