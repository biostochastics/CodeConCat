"""Utility functions for string processing in CodeConCat."""


def is_inside_string(line: str, position: int) -> bool:
    """
    Determine if a character position in a line is inside a string using a state machine.

    This is a robust implementation that correctly handles escaped quotes and other edge cases
    that a simple quote counting approach would miss.

    Args:
        line: The line of code to check
        position: The character position to check (0-indexed)

    Returns:
        True if the character at the given position is inside a string, False otherwise
    """
    if position < 0 or position >= len(line):
        return False

    # States for our state machine
    NORMAL = 0
    IN_SINGLE_QUOTE = 1
    IN_DOUBLE_QUOTE = 2
    ESCAPE_IN_SINGLE = 3
    ESCAPE_IN_DOUBLE = 4

    state = NORMAL

    # Process each character in the line up to the position we're checking
    for i in range(position):
        char = line[i]

        if state == NORMAL:
            if char == "'":
                state = IN_SINGLE_QUOTE
            elif char == '"':
                state = IN_DOUBLE_QUOTE

        elif state == IN_SINGLE_QUOTE:
            if char == "\\":
                state = ESCAPE_IN_SINGLE
            elif char == "'":
                state = NORMAL

        elif state == IN_DOUBLE_QUOTE:
            if char == "\\":
                state = ESCAPE_IN_DOUBLE
            elif char == '"':
                state = NORMAL

        elif state == ESCAPE_IN_SINGLE:
            # After escape character, return to normal string state
            state = IN_SINGLE_QUOTE

        elif state == ESCAPE_IN_DOUBLE:
            # After escape character, return to normal string state
            state = IN_DOUBLE_QUOTE

    # If we're in a string state at the position, return True
    return state in (IN_SINGLE_QUOTE, IN_DOUBLE_QUOTE, ESCAPE_IN_SINGLE, ESCAPE_IN_DOUBLE)
