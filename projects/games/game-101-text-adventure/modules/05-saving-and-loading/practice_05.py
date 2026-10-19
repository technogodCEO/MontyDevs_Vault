# practice_05.py: practice problems for Module 05: Saving and Loading
#
# Fill in each function where it says "# Your code here" (delete the `pass`).
# Problems marked FIX THE BUG already have code: find what's wrong and fix it.
#
# Test your answers from your game folder with:
#
#     python check.py practice 5
#
# Each problem gets its own result, so you can do them in any order.
# Stuck? An example answer is in this module's solution/practice_05.py.


# 1. save_settings(settings, filename) and load_settings(filename)
# save_settings writes the settings dictionary to the file as JSON.
# load_settings reads it back and returns it, or returns {} if the file
# doesn't exist yet.
import json


def save_settings(settings, filename):
    # Your code here
    pass


def load_settings(filename):
    # Your code here
    pass


# 2. FIX THE BUG: load_scores(filename)
# This should return the list saved in the file, or [] if there's no file
# yet. It works once the file exists, but crashes the very first time.
def load_scores(filename):
    try:
        with open(filename) as file:
            scores = json.load(file)
    except FileNotFoundError:
        print("No scores yet.")
    return scores


# 3. save_score(name, score, filename)
# Load the list of scores from the file (or start with [] if there's no file),
# add {"name": name, "score": score} to it, and write the list back.
def save_score(name, score, filename):
    # Your code here
    pass
