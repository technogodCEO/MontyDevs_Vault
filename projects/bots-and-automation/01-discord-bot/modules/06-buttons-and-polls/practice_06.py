# practice_06.py: practice problems for Module 06: Buttons and Polls
#
# Fill in each function where it says "# Your code here" (delete the `pass`).
# Problems marked FIX THE BUG already have code: find what's wrong and fix it.
#
# Test your answers from your bot's folder with:
#
#     python check.py practice 6
#
# Each problem gets its own result, so you can do them in any order.
# Stuck? The lesson has hints for each problem.


# 1. progress_bar(fraction, width)
# Draw a bar `width` characters wide: "#" for the filled part and "-" for
# the rest. Round to the nearest character, and treat fractions below 0 as 0
# and above 1 as 1.
#     progress_bar(0.5, 10)   -> "#####-----"
#     progress_bar(0.26, 10)  -> "###-------"
#     progress_bar(1.7, 5)    -> "#####"
def progress_bar(fraction, width):
    # Your code here
    pass


# 2. tally(votes, options)
# `votes` maps each user's id to the option they picked. Return how many
# votes each option got, as a list in the same order as `options`.
#     tally({101: "tea", 102: "coffee", 103: "tea"}, ["coffee", "tea", "juice"])
#       -> [1, 2, 0]
def tally(votes, options):
    # Your code here
    pass


# 3. winners(options, counts)
# Return every option with the most votes (more than one if there's a tie),
# in their original order. If nobody voted, return [].
#     winners(["a", "b", "c"], [4, 1, 4])  -> ["a", "c"]
#     winners(["a", "b"], [0, 0])          -> []
def winners(options, counts):
    # Your code here
    pass


# 4. FIX THE BUG: percentages(counts)
# This should turn vote counts into whole-number percentages. It works until
# a poll has no votes yet. Then every option should get 0.
#     percentages([1, 1, 2])  -> [25, 25, 50]
#     percentages([0, 0])     -> [0, 0]
def percentages(counts):
    total = sum(counts)
    return [round(100 * count / total) for count in counts]
