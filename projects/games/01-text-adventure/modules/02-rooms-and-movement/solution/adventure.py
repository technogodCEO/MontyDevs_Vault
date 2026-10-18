# adventure.py: The Lighthouse (Module 02 solution)
#
# This is ONE example of a finished Module 02. Your world, rooms and
# descriptions should be your own.

# ---------------------------------------------------------------------------
# The world
# ---------------------------------------------------------------------------
# Every room is a dictionary, stored in `rooms` under a short key like "beach".
#   "name"        - the title shown when the player enters
#   "description" - what the player sees
#   "exits"       - which direction leads to which room (by its key)
rooms = {
    "beach": {
        "name": "Stormy Beach",
        "description": "Cold waves crash against the rocks. A lighthouse "
                       "towers to the north, and a fishing shack leans "
                       "against the wind to the east.",
        "exits": {"north": "lighthouse", "east": "shack"},
    },
    "shack": {
        "name": "Fishing Shack",
        "description": "Nets and broken oars hang from the walls. It smells "
                       "of salt and old rope.",
        "exits": {"west": "beach"},
    },
    "lighthouse": {
        "name": "Lighthouse Hall",
        "description": "Your footsteps echo in the round stone hall. A spiral "
                       "staircase disappears into the darkness above.",
        "exits": {"south": "beach", "up": "lantern"},
    },
    "lantern": {
        "name": "Lantern Room",
        "description": "The great lantern sits in the middle of the room, "
                       "cold and dark, surrounded by windows facing the sea.",
        "exits": {"down": "lighthouse"},
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
    # Joining the exit directions gives a list like "north, east".
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

    # Look up which room this exit leads to, then show it.
    new_room = exits[direction]
    describe(new_room)
    return new_room


def show_help():
    print("Commands:")
    print("  look          - describe where you are")
    print("  go <place>    - move, e.g. 'go north'")
    print("  help          - show this list")
    print("  quit          - stop playing")


# ---------------------------------------------------------------------------
# The game loop
# ---------------------------------------------------------------------------
def main():
    print("=== The Lighthouse ===")
    print("A storm is rolling in, and the old lighthouse has gone dark.")
    print("Type 'help' to see what you can do.")

    # Remember where the player is, and show them their surroundings.
    current_room = start_room
    describe(current_room)

    playing = True
    while playing:
        # Split the command into words: "go north" -> ["go", "north"]
        words = input("> ").lower().split()
        if len(words) == 0:
            continue

        # The first word is the action (the verb). Everything after it is
        # what the action applies to (the noun), e.g. "north".
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
        else:
            print(f"I don't understand '{verb}'. Type 'help' for commands.")


# Only start the game when this file is run directly.
if __name__ == "__main__":
    main()
