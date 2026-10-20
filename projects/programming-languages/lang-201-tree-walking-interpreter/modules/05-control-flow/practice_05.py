# practice_05.py: practice problems for Module 05: Control Flow
#
# Fill in each function where it says "# Your code here" (delete the `pass`).
# Problems marked FIX THE BUG already have code: find what's wrong and fix it.
#
# Test your answers from your language's folder with:
#
#     python check.py practice 5
#
# Each problem gets its own result, so you can do them in any order.
# There are no answers to copy: the lesson's "Try it in code" section has hints.
#
# Your language's truthiness rule applies: only False and None are falsy.


# 1. and_(left, right) and or_(left, right)
# left is a value. right is a FUNCTION that works out the right-hand value
# when you call it: right(). Like your language's `and` and `or`, only call
# right() when you need to, and return one of the two values itself (not
# True or False).
#     and_(False, lambda: 1)    -> False   (right is never called)
#     and_(0, lambda: 2)        -> 2       (0 is truthy)
#     or_("x", lambda: 2)       -> "x"     (right is never called)
#     or_(None, lambda: "d")    -> "d"
def and_(left, right):
    # Your code here
    pass


def or_(left, right):
    # Your code here
    pass


# 2. run_while(condition, body)
# condition and body are functions with no arguments. Keep calling body()
# for as long as condition() returns a truthy value, then return how many
# times body() ran.
def run_while(condition, body):
    # Your code here
    pass


# 3. FIX THE BUG: run_if(condition, then_branch, else_branch)
# Call then_branch() if condition is truthy in YOUR language, otherwise
# else_branch(), and return what it returns. It takes the wrong branch for
# 0 and "". Why?
def run_if(condition, then_branch, else_branch):
    if condition:
        return then_branch()
    return else_branch()
