# practice_03.py: practice problems for Module 03: Items and Inventory
#
# Fill in each function where it says "# Your code here" (delete the `pass`).
# Problems marked FIX THE BUG already have code: find what's wrong and fix it.
#
# Test your answers from your game folder with:
#
#     python check.py practice 3
#
# Each problem gets its own result, so you can do them in any order.
# Stuck? An example answer is in this module's solution/practice_03.py.


# 1. move_item(item, source, target)
# If item is in the source list, move it to the target list and return True.
# Otherwise, change nothing and return False.
def move_item(item, source, target):
    # Your code here
    pass


# 2. FIX THE BUG: add_to_bag(item, bag)
# This should add item to the bag list that was passed in. But after calling
# it, the bag outside the function hasn't changed. Why?
def add_to_bag(item, bag):
    bag = bag + [item]


# 3. count_items(rooms)
# Return how many items there are across all the rooms put together.
# Each room looks like: {"items": ["lamp", "rope"]}
def count_items(rooms):
    # Your code here
    pass


# 4. describe_items(items)
# Return "You see: " followed by the items joined with ", ", or
# "There's nothing here." if the list is empty.
#     describe_items(["lamp", "rope"])  -> "You see: lamp, rope"
def describe_items(items):
    # Your code here
    pass
