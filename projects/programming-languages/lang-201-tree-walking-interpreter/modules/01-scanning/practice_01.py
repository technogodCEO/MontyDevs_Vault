# practice_01.py: practice problems for Module 01: Scanning
#
# Fill in each function where it says "# Your code here" (delete the `pass`).
# Problems marked FIX THE BUG already have code: find what's wrong and fix it.
#
# Test your answers from your language's folder with:
#
#     python check.py practice 1
#
# Each problem gets its own result, so you can do them in any order.
# There are no answers to copy: the lesson's "Try it in code" section has hints.


# 1. read_number(text, i)
# text[i] is a digit. Read the whole number that starts there: digits, then
# optionally a "." followed by more digits. Return a tuple of the number's
# value (as a float) and the index just after it.
#     read_number("x = 42;", 4)  -> (42.0, 6)
#     read_number("3.14)", 0)    -> (3.14, 4)
#     read_number("7.", 0)       -> (7.0, 1)   (a dot must be followed by a digit)
#     read_number("1.5.2", 0)    -> (1.5, 3)
def read_number(text, i):
    # Your code here
    pass


# 2. is_identifier(word)
# Return True if word is a valid name: one or more letters, digits or
# underscores, not starting with a digit.
#     is_identifier("score")  -> True
#     is_identifier("_x")     -> True
#     is_identifier("2x")     -> False
#     is_identifier("")       -> False
#     is_identifier("a-b")    -> False
def is_identifier(word):
    # Your code here
    pass


# 3. FIX THE BUG: line_of(text, index)
# Return the line number (starting from 1) that the character at text[index]
# is on. It's always one line too low. Why?
#     line_of("one\ntwo\nthree", 0)  -> 1
#     line_of("one\ntwo\nthree", 4)  -> 2
def line_of(text, index):
    return text.count("\n", 0, index)


# 4. split_tokens(text)
# Split text into a list of tokens:
#   - a run of letters, digits and underscores is one token ("x1", "42")
#   - any other character that isn't whitespace is a token on its own ("=", "(")
#   - whitespace separates tokens and is dropped
#   - "//" starts a comment that runs to the end of the line, and is dropped
#     split_tokens("x1 = (3+42)")    -> ["x1", "=", "(", "3", "+", "42", ")"]
#     split_tokens("a // comment\nb") -> ["a", "b"]
def split_tokens(text):
    # Your code here
    pass
