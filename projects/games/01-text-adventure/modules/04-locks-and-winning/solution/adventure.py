# adventure.py: The Lighthouse (Module 04 solution)
#
# This is ONE example of a finished Module 04. Your world, puzzles and
# ending should be your own.

# ---------------------------------------------------------------------------
# The world
# ---------------------------------------------------------------------------
# Every room is a dictionary, stored in `rooms` under a short key like "beach".
#   "name"        - the title shown when the player enters
#   "description" - what the player sees
#   "exits"       - which direction leads to which room (by its key)
#   "items"       - things lying around that can be picked up
#   "locked"      - (optional) exits that need an item: {direction: item}
rooms = {
    "beach": {
        "name": "Stormy Beach",
        "description": "Cold waves crash against the rocks. A lighthouse "
                       "towers to the north, and a fishing shack leans "
                       "against the wind to the east.",
        "exits": {"north": "lighthouse", "east": "shack"},
        "items": ["shell"],
        # The lighthouse door stays shut until the player has the key.
        "locked": {"north": "key"},
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
        # It's too dark to climb the stairs without a lamp.
        "locked": {"up": "lamp"},
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

# Reaching this room wins the game.
goal_room = "lantern"
win_message = ("You light the great lantern. Its beam sweeps across the "
               "water, and far out at sea a ship turns safely away from "
               "the rocks. You win!")


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------
def describe(room_key):
    """Print everything the player can see in a room."""
    room = rooms[room_key]
    print()
    print(f"== {room['name']} ==")
    print(room["description"])
    if room["items"]:
        print("You see: " + ", ".join(room["items"]))
    print("Exits: " + ", ".join(room["exits"]))


def go(current_room, direction, inventory):
    """Try to move in a direction. Returns the room the player ends up in."""
    room = rooms[current_room]

    if direction == "":
        print("Go where?")
        return current_room
    if direction not in room["exits"]:
        print("You can't go that way.")
        return current_room

    # Some exits are locked until the player carries the right item.
    # .get() gives back an empty dictionary if this room has no "locked" key,
    # so rooms without locks still work.
    locked = room.get("locked", {})
    if direction in locked:
        needed = locked[direction]
        if needed not in inventory:
            print(f"Something blocks the way {direction}. Maybe you need an item.")
            return current_room
        print(f"You use the {needed}.")

    new_room = room["exits"][direction]
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
    inventory = []
    describe(current_room)

    playing = True
    while playing:
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
            current_room = go(current_room, noun, inventory)
            # Moving is the only way to reach the goal, so check right after.
            if current_room == goal_room:
                print()
                print(win_message)
                playing = False
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
