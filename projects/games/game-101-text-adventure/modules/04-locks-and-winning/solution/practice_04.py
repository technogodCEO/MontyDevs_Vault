# practice_04.py: example answers for Module 04: Locks and Winning
#
# These are ONE way to solve each problem. If yours is different and
# `python check.py practice 4` passes, it's right too.


# 1. can_pass(room, direction, inventory)
# Return True if that exit isn't locked, or if the inventory has the item
# that unlocks it. Locked rooms look like:
#     {"exits": {"north": "hall"}, "locked": {"north": "key"}}
# Rooms without locks have no "locked" key at all.
def can_pass(room, direction, inventory):
    # .get() gives back an empty dictionary when the room has no locks.
    locked = room.get("locked", {})
    if direction not in locked:
        return True
    return locked[direction] in inventory


# 2. FIX THE BUG: lock_for(room, direction)
# This should return the item needed to go `direction`, or None if that
# exit isn't locked. It crashes for rooms without locks, and for exits that
# aren't locked.
def lock_for(room, direction):
    # The bug: [] raises a KeyError for missing keys. .get() returns a
    # default instead: {} for a missing "locked", None for a missing direction.
    return room.get("locked", {}).get(direction)


# 3. missing_keys(rooms)
# Return a sorted list of the items that some lock needs, but that aren't in
# any room's "items". A game with missing keys can't be won!
#     If a lock needs "crowbar" and no room has one -> ["crowbar"]
# (sorted(some_list) returns a sorted copy of a list.)
def missing_keys(rooms):
    # First collect every item that's lying around somewhere.
    available = []
    for key in rooms:
        available = available + rooms[key]["items"]

    # Then look at every lock and note the ones nobody can open.
    missing = []
    for key in rooms:
        for needed in rooms[key].get("locked", {}).values():
            if needed not in available and needed not in missing:
                missing.append(needed)
    return sorted(missing)
