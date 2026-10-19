# practice_02.py: practice problems for Module 02: Options and Dice
#
# Fill in each function where it says "# Your code here" (delete the `pass`).
# Problems marked FIX THE BUG already have code: find what's wrong and fix it.
#
# Test your answers from your bot's folder with:
#
#     python check.py practice 2
#
# Each problem gets its own result, so you can do them in any order.
# Stuck? The lesson has hints for each problem.


# 1. parse_duration(text)
# Turn a duration like "1h30m" into a number of seconds. It can use d (days),
# h (hours), m (minutes) and s (seconds), in any combination, with or without
# spaces, in upper or lower case. Raise ValueError for anything else,
# including a number with no unit.
#     parse_duration("45s")       -> 45
#     parse_duration("1h30m")     -> 5400
#     parse_duration("1h 5m 3s")  -> 3903
#     parse_duration("10")        -> ValueError
def parse_duration(text):
    # Your code here
    pass


# 2. split_options(text)
# Split comma-separated options into a list, without the extra spaces, and
# skip any that are empty.
#     split_options("pizza, tacos ,, sushi")  -> ["pizza", "tacos", "sushi"]
#     split_options(" , ")                    -> []
def split_options(text):
    # Your code here
    pass


# 3. parse_color(text)
# Turn a hex colour like "#ff8800" into a number (the kind discord.Embed's
# color= wants). The # is optional, and spaces around it don't matter. Raise
# ValueError unless it's exactly 6 hex digits.
#     parse_color("#ff8800")  -> 16746496   (which is 0xFF8800)
#     parse_color("red")      -> ValueError
def parse_color(text):
    # Your code here
    pass


# 4. FIX THE BUG: average(numbers_text)
# This should return the average of comma-separated numbers, but it crashes.
#     average("3, 4, 5")  -> 4.0
def average(numbers_text):
    parts = numbers_text.split(",")
    total = 0
    for part in parts:
        total += part
    return total / len(parts)
