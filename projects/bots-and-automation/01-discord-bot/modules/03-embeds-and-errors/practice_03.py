# practice_03.py: practice problems for Module 03: Embeds and Errors
#
# Fill in each function where it says "# Your code here" (delete the `pass`).
# Problems marked FIX THE BUG already have code: find what's wrong and fix it.
#
# Test your answers from your bot's folder with:
#
#     python check.py practice 3
#
# Each problem gets its own result, so you can do them in any order.
# Stuck? The lesson has hints for each problem.


# 1. safe_int(text, default)
# Turn text into an int, ignoring spaces around it. If it isn't a whole
# number, return `default` instead of crashing.
#     safe_int(" 7 ", 0)      -> 7
#     safe_int("seven", -1)   -> -1
def safe_int(text, default):
    # Your code here
    pass


# A custom exception. Because it's based on ValueError, code that catches
# ValueError catches this too.
class InvalidChoice(ValueError):
    pass


# 2. pick(options, number)
# Return option number `number`, counting from 1 like a person would. If
# there's no such option, raise InvalidChoice with a message that says which
# numbers are allowed, like "Pick a number from 1 to 2."
#     pick(["red", "blue"], 2)  -> "blue"
#     pick(["red", "blue"], 3)  -> raises InvalidChoice("Pick a number from 1 to 2.")
def pick(options, number):
    # Your code here
    pass


# 3. format_scores(scores)
# Turn a dictionary of names and scores into a ranked list, one line each,
# highest score first. Break ties alphabetically by name. If there are no
# scores, return "No scores yet."
#     format_scores({"Ana": 50, "Ben": 70, "Cy": 50})
#       -> "1. Ben - 70\n2. Ana - 50\n3. Cy - 50"
def format_scores(scores):
    # Your code here
    pass


# 4. FIX THE BUG: describe_error(text)
# This should divide 100 by the number in `text`, and give a different
# friendly message for each thing that can go wrong. It never crashes, but
# it gives the wrong message for "0" and for "four".
#     describe_error("4")     -> "25.0"
#     describe_error("0")     -> "Can't divide by zero."
#     describe_error("four")  -> "That's not a number."
def describe_error(text):
    try:
        number = int(text)
        return f"{100 / number:.1f}"
    except Exception:
        return "Something went wrong."
    except ZeroDivisionError:
        return "Can't divide by zero."
    except ValueError:
        return "That's not a number."
