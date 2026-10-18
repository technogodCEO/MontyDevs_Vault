# practice_01.py: practice problems for Module 01: The Game Loop
#
# Fill in each function where it says "# Your code here" (delete the `pass`).
# Problems marked FIX THE BUG already have code: find what's wrong and fix it.
#
# Test your answers from your game folder with:
#
#     python check.py practice 1
#
# Each problem gets its own result, so you can do them in any order.
# Stuck? An example answer is in this module's solution/practice_01.py.


# 1. clean(command)
# Return the command with spaces removed from both ends, in lowercase.
#     clean("  QUIT ")   -> "quit"
#     clean("Go North")  -> "go north"
def clean(command):
    # Your code here
    pass


# 2. countdown(start)
# Use a while loop to build and return a list counting down from start to 1.
#     countdown(3)  -> [3, 2, 1]
#     countdown(0)  -> []
# (Start with an empty list, and add to it with .append(number).)
def countdown(start):
    # Your code here
    pass


# 3. FIX THE BUG: are_we_there_yet()
# This should keep asking until the answer is "yes" (any capitals, any spaces),
# then print "Finally!". Instead it never stops. Why?
def are_we_there_yet():
    answer = ""
    while answer != "yes":
        input("Are we there yet? ")
    print("Finally!")


# 4. password_door()
# Keep asking "Password: " until the player types "open sesame" (any
# capitals, any spaces). Then print "The door opens."
def password_door():
    # Your code here
    pass
