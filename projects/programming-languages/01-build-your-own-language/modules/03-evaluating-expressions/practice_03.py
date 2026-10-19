# practice_03.py: practice problems for Module 03: Evaluating Expressions
#
# Fill in each function where it says "# Your code here" (delete the `pass`).
# Problems marked FIX THE BUG already have code: find what's wrong and fix it.
#
# Test your answers from your language's folder with:
#
#     python check.py practice 3
#
# Each problem gets its own result, so you can do them in any order.
# There are no answers to copy: the lesson's "Try it in code" section has hints.
#
# These use Python values the way your interpreter will: None for nil,
# True/False for booleans, floats for numbers, str for strings.


# 1. truthy(value)
# Return True or False using YOUR language's rule: only false and nil are
# falsy. Everything else, including 0 and "", is truthy.
#     truthy(None)  -> False
#     truthy(0)     -> True
#     truthy("")    -> True
def truthy(value):
    # Your code here
    pass


# 2. stringify(value)
# Return the text `print` shows for a value.
#     stringify(None)   -> "nil"
#     stringify(True)   -> "true"
#     stringify(3.0)    -> "3"      (whole numbers have no ".0")
#     stringify(2.5)    -> "2.5"
#     stringify("hi")   -> "hi"
def stringify(value):
    # Your code here
    pass


# 3. evaluate(node)
# Work out the value of a tiny tree made of tuples:
#     ("num", n)     the number n
#     ("nil",)       nil (None)
#     ("add", a, b)  a + b        ("sub", a, b)  a - b
#     ("mul", a, b)  a * b        ("neg", a)     -a
#     ("not", a)     True if a is falsy (use truthy()), else False
#     evaluate(("mul", ("num", 2), ("add", ("num", 3), ("num", 4))))  -> 14
#     evaluate(("not", ("num", 0)))                                -> False
def evaluate(node):
    # Your code here
    pass


# 4. FIX THE BUG: equal(a, b)
# Return whether two values are equal in your language. Values of different
# types are never equal, so 1 == true is false. But Python thinks
# 1.0 == True, and this gets it wrong. Fix it.
#     equal(1.0, 1.0)   -> True
#     equal(1.0, True)  -> False
#     equal(None, False) -> False
def equal(a, b):
    return a == b
