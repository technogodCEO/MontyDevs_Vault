# practice_04.py: practice problems for Module 04: Variables and Scope
#
# Fill in each method or function where it says "# Your code here" (delete
# the `pass`). Problems marked FIX THE BUG already have code: find what's
# wrong and fix it.
#
# Test your answers from your language's folder with:
#
#     python check.py practice 4
#
# Each problem gets its own result, so you can do them in any order.
# There are no answers to copy: the lesson's "Try it in code" section has hints.


# 1 and 2. Environment
# An environment holds the variables of one scope, and points to the
# environment around it (its parent), or None for the global scope.
#
#     outer = Environment()
#     inner = Environment(outer)
#     outer.define("a", 1)
#     inner.get("a")       -> 1    (found in the parent)
#     inner.assign("a", 5) # changes the "a" in outer
#     outer.get("zzz")     # raises NameError
class Environment:
    def __init__(self, parent=None):
        self.values = {}
        self.parent = parent

    # Problem 1: define(name, value) and get(name)
    # define() makes a new variable in THIS environment (replacing one with
    # the same name here, if there is one).
    def define(self, name, value):
        # Your code here
        pass

    # get() returns the value from the nearest environment that has the
    # name: this one, then its parent, and so on. If none has it, raise
    # NameError.
    def get(self, name):
        # Your code here
        pass

    # Problem 2: assign(name, value)
    # Change an existing variable in the nearest environment that has it.
    # If none has it, raise NameError (assigning never creates a variable).
    def assign(self, name, value):
        # Your code here
        pass


# 3. FIX THE BUG: lookup(scopes, name)
# scopes is a list of dictionaries, from the outermost scope (first) to the
# innermost (last). Return the value of name from the innermost scope that
# has it, or None if no scope does. Inner names should hide outer ones, but
# this always finds the global one. Why?
#     lookup([{"a": "global"}, {"a": "inner"}], "a")  -> "inner"
def lookup(scopes, name):
    for scope in scopes:
        if name in scope:
            return scope[name]
    return None
