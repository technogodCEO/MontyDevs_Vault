# practice_04.py: practice problems for Module 04: Cogs and Tests
#
# Fill in each function where it says "# Your code here" (delete the `pass`).
# Problems marked FIX THE BUG already have code: find what's wrong and fix it.
#
# Test your answers from your bot's folder with:
#
#     python check.py practice 4
#
# Each problem gets its own result, so you can do them in any order.
# Stuck? The lesson has hints for each problem.


# 1. test_clamp()
# clamp(value, low, high) keeps a value between two limits:
#     clamp(5, 1, 10)   -> 5
#     clamp(-3, 1, 10)  -> 1
#     clamp(99, 1, 10)  -> 10
# This one already works. Your job is to write test_clamp(): a test, with
# assert statements, that would catch a broken clamp(). The checker runs
# your test against this clamp() (it should pass) and against several
# broken versions (it should fail for every one of them). Think about the
# edges too: what should happen to a value that's exactly on a limit?
def clamp(value, low, high):
    return max(low, min(value, high))


def test_clamp():
    # Your code here
    pass


# 2. FIX THE BUG: add_tag(tag, tags=[])
# This should add a tag to a list and return the list. If no list is given,
# it should start a new one. But the second call remembers the first call's
# tag:
#     add_tag("fun")     -> ["fun"]
#     add_tag("games")   -> ["fun", "games"]   (should be ["games"])
def add_tag(tag, tags=[]):
    tags.append(tag)
    return tags


# 3. class Cooldown
# Cooldown(seconds) remembers when each user last did something.
# ready(user_id, now) returns True (and remembers `now` as that user's last
# time) if they've never done it, or if at least `seconds` have passed since
# their last time. Otherwise it returns False and changes nothing.
#     cool = Cooldown(10)
#     cool.ready(1, 0)    -> True
#     cool.ready(1, 5)    -> False   (only 5 seconds later)
#     cool.ready(2, 5)    -> True    (user 2 is separate)
#     cool.ready(1, 10)   -> True    (10 seconds after their last time)
class Cooldown:
    def __init__(self, seconds):
        # Your code here
        pass

    def ready(self, user_id, now):
        # Your code here
        pass


# 4. extension_names(filenames)
# Given the filenames in a cogs folder, return the extension names to load,
# sorted: only .py files, skipping any that start with an underscore.
#     extension_names(["fun.py", "__init__.py", "notes.txt", "levels.py"])
#       -> ["cogs.fun", "cogs.levels"]
def extension_names(filenames):
    # Your code here
    pass
