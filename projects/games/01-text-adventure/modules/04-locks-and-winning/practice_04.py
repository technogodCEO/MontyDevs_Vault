# practice_04.py: practice problems for Module 04: Locks and Winning
#
# Fill in each function where it says "# Your code here" (delete the `pass`).
# Problems marked FIX THE BUG already have code: find what's wrong and fix it.
#
# Test your answers from your game folder with:
#
#     python check.py practice 4
#
# Each problem gets its own result, so you can do them in any order.
# Stuck? An example answer is in this module's solution/practice_04.py.


# 1. can_pass(room, direction, inventory)
# Return True if that exit isn't locked, or if the inventory has the item
# that unlocks it. Locked rooms look like:
#     {"exits": {"north": "hall"}, "locked": {"north": "key"}}
# Rooms without locks have no "locked" key at all.
def can_pass(room, direction, inventory):
    # Your code here
    pass


# 2. FIX THE BUG: lock_for(room, direction)
# This should return the item needed to go `direction`, or None if that
# exit isn't locked. It crashes for rooms without locks, and for exits that
# aren't locked.
def lock_for(room, direction):
    return room["locked"][direction]


# 3. missing_keys(rooms)
# Return a sorted list of the items that some lock needs, but that aren't in
# any room's "items". A game with missing keys can't be won!
#     If a lock needs "crowbar" and no room has one -> ["crowbar"]
# (sorted(some_list) returns a sorted copy of a list.)
def missing_keys(rooms):
    # Your code here
    pass
