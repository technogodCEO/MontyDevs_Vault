# practice_01.py: example answers for Module 01: The Game Loop
#
# These are ONE way to solve each problem. If yours is different and
# `python check.py practice 1` passes, it's right too.


# 1. clean(command)
# Return the command with spaces removed from both ends, in lowercase.
#     clean("  QUIT ")   -> "quit"
#     clean("Go North")  -> "go north"
def clean(command):
    # .strip() removes spaces at both ends, then .lower() lowercases it.
    return command.strip().lower()


# 2. countdown(start)
# Use a while loop to build and return a list counting down from start to 1.
#     countdown(3)  -> [3, 2, 1]
#     countdown(0)  -> []
# (Start with an empty list, and add to it with .append(number).)
def countdown(start):
    numbers = []
    count = start
    # Keep going while there's still a number above zero to add.
    while count > 0:
        numbers.append(count)
        count = count - 1
    return numbers


# 3. FIX THE BUG: are_we_there_yet()
# This should keep asking until the answer is "yes" (any capitals, any spaces),
# then print "Finally!". Instead it never stops. Why?
def are_we_there_yet():
    answer = ""
    while answer != "yes":
        # The bug: input()'s result was thrown away, so answer never changed.
        answer = input("Are we there yet? ").strip().lower()
    print("Finally!")


# 4. password_door()
# Keep asking "Password: " until the player types "open sesame" (any
# capitals, any spaces). Then print "The door opens."
def password_door():
    password = ""
    while password != "open sesame":
        password = input("Password: ").strip().lower()
    print("The door opens.")
