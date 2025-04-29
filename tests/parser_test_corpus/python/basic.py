#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Basic Python test file for parser validation.

This file contains common Python constructs that should be properly parsed.
"""


class SimpleClass:
    """A simple class with documentation."""

    class_var = "class variable"

    def __init__(self, name: str):
        """Initialize with a name.

        Args:
            name: The name to use
        """
        self.name = name
        self._private = 42

    def method(self, arg1: int, arg2: str = "default") -> str:
        """A simple method with documentation.

        Args:
            arg1: First argument
            arg2: Second argument with default

        Returns:
            A string result
        """
        return f"{self.name}: {arg1} - {arg2}"

    @property
    def property_example(self) -> str:
        """A property with documentation."""
        return self.name.upper()

    @staticmethod
    def static_method(value: int) -> int:
        """A static method with documentation."""
        return value * 2


def standalone_function(a: int, b: int) -> int:
    """A standalone function with documentation.

    Args:
        a: First number
        b: Second number

    Returns:
        Sum of a and b
    """
    return a + b


# A constant with documentation
PI = 3.14159
"""The mathematical constant pi, approximately."""


# Nested functions
def outer_function(x: int) -> callable:
    """An outer function that returns another function.

    Args:
        x: Value to capture in closure

    Returns:
        A function that uses the captured value
    """

    def inner_function(y: int) -> int:
        """An inner function with its own docstring.

        Args:
            y: Value to add to the captured x

        Returns:
            Sum of x and y
        """
        return x + y

    return inner_function


# Class with inheritance
class ChildClass(SimpleClass):
    """A child class that inherits from SimpleClass."""

    def __init__(self, name: str, extra: str):
        """Initialize with name and extra info.

        Args:
            name: The name to use
            extra: Extra information
        """
        super().__init__(name)
        self.extra = extra

    def method(self, arg1: int, arg2: str = "child_default") -> str:
        """Override parent method.

        Args:
            arg1: First argument
            arg2: Second argument with default

        Returns:
            A modified string result
        """
        parent_result = super().method(arg1, arg2)
        return f"{parent_result} (child: {self.extra})"


if __name__ == "__main__":
    # Example usage
    simple = SimpleClass("test")
    child = ChildClass("child", "extra_info")
    print(simple.method(1, "hello"))
    print(child.method(2, "world"))
    print(standalone_function(5, 7))
