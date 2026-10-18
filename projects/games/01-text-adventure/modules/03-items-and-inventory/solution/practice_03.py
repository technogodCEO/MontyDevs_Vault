# practice_03.py: example answers for Module 03: Items and Inventory
#
# These are ONE way to solve each problem. If yours is different and
# `python check.py practice 3` passes, it's right too.


# 1. move_item(item, source, target)
# If item is in the source list, move it to the target list and return True.
# Otherwise, change nothing and return False.
def move_item(item, source, target):
    if item not in source:
        return False
    # Changing the lists here changes them for the caller too.
    source.remove(item)
    target.append(item)
    return True


# 2. FIX THE BUG: add_to_bag(item, bag)
# This should add item to the bag list that was passed in. But after calling
# it, the bag outside the function hasn't changed. Why?
def add_to_bag(item, bag):
    # The bug: `bag + [item]` builds a NEW list, and `bag = ...` only changes
    # this function's own variable. .append() changes the original list.
    bag.append(item)


# 3. count_items(rooms)
# Return how many items there are across all the rooms put together.
# Each room looks like: {"items": ["lamp", "rope"]}
def count_items(rooms):
    total = 0
    # Looping over a dictionary gives its keys.
    for key in rooms:
        total = total + len(rooms[key]["items"])
    return total


# 4. describe_items(items)
# Return "You see: " followed by the items joined with ", ", or
# "There's nothing here." if the list is empty.
#     describe_items(["lamp", "rope"])  -> "You see: lamp, rope"
def describe_items(items):
    # An empty list counts as False.
    if items:
        return "You see: " + ", ".join(items)
    return "There's nothing here."
