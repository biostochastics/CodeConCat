"""Simple test project for CLI testing."""


def add(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b


def multiply(x: float, y: float) -> float:
    """Multiply two numbers."""
    return x * y


class Calculator:
    """A simple calculator class."""

    def __init__(self):
        self.memory = 0

    def calculate(self, operation: str, a: float, b: float) -> float:
        """Perform a calculation."""
        if operation == "add":
            return a + b
        elif operation == "multiply":
            return a * b
        else:
            raise ValueError(f"Unknown operation: {operation}")


if __name__ == "__main__":
    calc = Calculator()
    print(calc.calculate("add", 5, 3))
