# practice_05.py: example answers for Module 05: Saving and Loading
#
# These are ONE way to solve each problem. If yours is different and
# `python check.py practice 5` passes, it's right too.


# 1. save_settings(settings, filename) and load_settings(filename)
# save_settings writes the settings dictionary to the file as JSON.
# load_settings reads it back and returns it, or returns {} if the file
# doesn't exist yet.
import json


def save_settings(settings, filename):
    # "w" opens the file for writing, replacing what was there.
    with open(filename, "w") as file:
        json.dump(settings, file)


def load_settings(filename):
    try:
        with open(filename) as file:
            return json.load(file)
    except FileNotFoundError:
        # Nothing saved yet, so start with no settings.
        return {}


# 2. FIX THE BUG: load_scores(filename)
# This should return the list saved in the file, or [] if there's no file
# yet. It works once the file exists, but crashes the very first time.
def load_scores(filename):
    try:
        with open(filename) as file:
            scores = json.load(file)
    except FileNotFoundError:
        # The bug: when there's no file, `scores` was never created.
        # Give it a starting value here.
        scores = []
    return scores


# 3. save_score(name, score, filename)
# Load the list of scores from the file (or start with [] if there's no file),
# add {"name": name, "score": score} to it, and write the list back.
def save_score(name, score, filename):
    # Load, change, save: the same pattern your game uses.
    scores = load_scores(filename)
    scores.append({"name": name, "score": score})
    with open(filename, "w") as file:
        json.dump(scores, file)
