# practice_02.py: example answers for Module 02: Rooms and Movement
#
# These are ONE way to solve each problem. If yours is different and
# `python check.py practice 2` passes, it's right too.


# 1. opposite(direction)
# Return the opposite of "north", "south", "east" or "west", and "?" for
# anything else. Try using a dictionary instead of a chain of ifs.
#     opposite("east")  -> "west"
#     opposite("up")    -> "?"
def opposite(direction):
    opposites = {"north": "south", "south": "north", "east": "west", "west": "east"}
    if direction in opposites:
        return opposites[direction]
    return "?"


# 2. split_command(text)
# Split what the player typed into a verb (the first word) and a noun (all
# the other words, joined by spaces). Return both: return verb, noun
# If there are no words, return "", "".
#     split_command("go up the stairs")  -> ("go", "up the stairs")
#     split_command("look")              -> ("look", "")
def split_command(text):
    words = text.split()
    # An empty list has no first word, so check before using words[0].
    if len(words) == 0:
        return "", ""
    return words[0], " ".join(words[1:])


# 3. follow(world, start, directions)
# Start in room `start` and follow each direction in the `directions` list.
# Skip any direction the current room has no exit for. Return the key of
# the room you end up in. Rooms look like: {"exits": {"east": "b"}}
#     follow(world, "a", ["east", "north"])  -> "c"   (with the world from the lesson)
def follow(world, start, directions):
    current = start
    for direction in directions:
        exits = world[current]["exits"]
        # Only move if this room really has an exit that way.
        if direction in exits:
            current = exits[direction]
    return current


# 4. FIX THE BUG: describe_exits(room)
# This should return something like "Exits: north, east", but it crashes.
def describe_exits(room):
    # The bug: you can't add a dictionary to a string. ", ".join() turns the
    # dictionary's keys into one string first.
    return "Exits: " + ", ".join(room["exits"])
