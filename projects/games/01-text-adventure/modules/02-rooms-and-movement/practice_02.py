# practice_02.py: practice problems for Module 02: Rooms and Movement
#
# Fill in each function where it says "# Your code here" (delete the `pass`).
# Problems marked FIX THE BUG already have code: find what's wrong and fix it.
#
# Test your answers from your game folder with:
#
#     python check.py practice 2
#
# Each problem gets its own result, so you can do them in any order.
# Stuck? An example answer is in this module's solution/practice_02.py.


# 1. opposite(direction)
# Return the opposite of "north", "south", "east" or "west", and "?" for
# anything else. Try using a dictionary instead of a chain of ifs.
#     opposite("east")  -> "west"
#     opposite("up")    -> "?"
def opposite(direction):
    # Your code here
    pass


# 2. split_command(text)
# Split what the player typed into a verb (the first word) and a noun (all
# the other words, joined by spaces). Return both: return verb, noun
# If there are no words, return "", "".
#     split_command("go up the stairs")  -> ("go", "up the stairs")
#     split_command("look")              -> ("look", "")
def split_command(text):
    # Your code here
    pass


# 3. follow(world, start, directions)
# Start in room `start` and follow each direction in the `directions` list.
# Skip any direction the current room has no exit for. Return the key of
# the room you end up in. Rooms look like: {"exits": {"east": "b"}}
#     follow(world, "a", ["east", "north"])  -> "c"   (with the world from the lesson)
def follow(world, start, directions):
    # Your code here
    pass


# 4. FIX THE BUG: describe_exits(room)
# This should return something like "Exits: north, east", but it crashes.
def describe_exits(room):
    return "Exits: " + room["exits"]
