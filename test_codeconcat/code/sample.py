#!/usr/bin/env python3
# This is a sample Python file

"""
This is a sample module docstring.
It describes what this module does.
"""


def hello_world() -> str:
    """Return a hello world message.

    Returns:
        str: A greeting message
    """
    return "Hello, World!"


class Calculator:
    """A simple calculator class to test CodeConCat."""

    def __init__(self, initial_value: float = 0):
        """Initialize with an optional starting value.

        Args:
            initial_value: The starting value for calculations
        """
        self.value = initial_value

    def add(self, x: float) -> float:
        """Add a number to the current value.

        Args:
            x: Number to add

        Returns:
            float: The new value
        """
        self.value += x
        return self.value

    def subtract(self, x: float) -> float:
        """Subtract a number from the current value.

        Args:
            x: Number to subtract

        Returns:
            float: The new value
        """
        self.value -= x
        return self.value


if __name__ == "__main__":
    print(hello_world())
    calc = Calculator(10)
    print(f"10 + 5 = {calc.add(5)}")
    print(f"15 - 3 = {calc.subtract(3)}")
