# practice_02.py: practice problems for Module 02: Parsing Expressions
#
# Fill in each function where it says "# Your code here" (delete the `pass`).
# Problems marked FIX THE BUG already have code: find what's wrong and fix it.
#
# Test your answers from your language's folder with:
#
#     python check.py practice 2
#
# Each problem gets its own result, so you can do them in any order.
# There are no answers to copy: the lesson's "Try it in code" section has hints.


# 1. balanced(text)
# Return True if every bracket in text, (), [] and {}, is closed by the
# right kind of bracket in the right order. Ignore every other character.
#     balanced("(a[b]{c})")  -> True
#     balanced("(]")         -> False
#     balanced("((")         -> False
#     balanced("")           -> True
def balanced(text):
    # Your code here
    pass


# 2. calculate(text)
# Work out a sum made of whole numbers, + - * / and brackets, with the usual
# precedence (* and / before + and -) and left-to-right order. Spaces are
# allowed. Write it as a recursive descent parser (see the lesson): don't use
# eval().
#     calculate("2+3*4")    -> 14
#     calculate("(2+3)*4")  -> 20
#     calculate("10-4-3")   -> 3
#     calculate("8/2/2")    -> 2
def calculate(text):
    # Your code here
    pass


# 3. FIX THE BUG: calc(tokens)
# tokens is a list of numbers and "+" or "-" signs, like [10, "-", 4, "-", 3].
# Return the result, working left to right: 10 - 4 - 3 is 3.
# It gets 9 instead. Why?
def calc(tokens):
    first = tokens[0]
    if len(tokens) == 1:
        return first
    rest = calc(tokens[2:])
    if tokens[1] == "-":
        return first - rest
    return first + rest


# 4. to_sexpr(tree)
# A tree is either a plain value, or a tuple of an operator and its operands.
# Return it as an S-expression string, the format --ast prints.
#     to_sexpr(("+", 1, ("*", 2, 3)))  -> "(+ 1 (* 2 3))"
#     to_sexpr(("!", True))            -> "(! True)"
#     to_sexpr(42)                     -> "42"
def to_sexpr(tree):
    # Your code here
    pass
