"""Tests for Go parser."""

import pytest

from codeconcat.parser.language_parsers.go_parser import parse_go
from codeconcat.errors import LanguageParserError


def test_parse_go_function():
    """Test parsing Go functions."""
    code = """
package main

func hello() {
    fmt.Println("Hello, World!")
}

func add(x, y int) int {
    return x + y
}
"""
    result = parse_go("test.go", code)
    assert result is not None
    assert len(result.declarations) == 2

    hello_func = next(d for d in result.declarations if d.name == "hello")
    assert hello_func.kind == "function"
    assert hello_func.start_line == 4

    add_func = next(d for d in result.declarations if d.name == "add")
    assert add_func.kind == "function"
    assert add_func.start_line == 8


def test_parse_go_struct():
    """Test parsing Go structs."""
    code = """
package main

type Person struct {
    Name string
    Age  int
}

type Employee struct {
    Person
    Salary float64
}
"""
    result = parse_go("test.go", code)
    assert result is not None
    assert len(result.declarations) == 2

    person = next(d for d in result.declarations if d.name == "Person")
    assert person.kind == "struct"
    assert person.start_line == 4

    employee = next(d for d in result.declarations if d.name == "Employee")
    assert employee.kind == "struct"
    assert employee.start_line == 9


def test_parse_go_interface():
    """Test parsing Go interfaces."""
    code = """
package main

type Reader interface {
    Read(p []byte) (n int, err error)
}

type Writer interface {
    Write(p []byte) (n int, err error)
}
"""
    result = parse_go("test.go", code)
    assert result is not None
    assert len(result.declarations) == 2

    reader = next(d for d in result.declarations if d.name == "Reader")
    assert reader.kind == "interface"
    assert reader.start_line == 4

    writer = next(d for d in result.declarations if d.name == "Writer")
    assert writer.kind == "interface"
    assert writer.start_line == 8


def test_parse_go_const_var():
    """Test parsing Go constants and variables."""
    code = """
package main

const (
    MaxItems = 100
    MinItems = 1
)

var (
    Debug = false
    Count = 0
)
"""
    result = parse_go("test.go", code)
    assert result is not None
    assert len(result.declarations) == 4

    max_items = next(d for d in result.declarations if d.name == "MaxItems")
    assert max_items.kind == "const"
    assert max_items.start_line == 5

    min_items = next(d for d in result.declarations if d.name == "MinItems")
    assert min_items.kind == "const"
    assert min_items.start_line == 6

    debug = next(d for d in result.declarations if d.name == "Debug")
    assert debug.kind == "var"
    assert debug.start_line == 10

    count = next(d for d in result.declarations if d.name == "Count")
    assert count.kind == "var"
    assert count.start_line == 11


def test_parse_go_empty():
    """Test parsing empty Go file."""
    result = parse_go("test.go", "")
    assert result is not None
    assert len(result.declarations) == 0


def test_parse_go_invalid():
    """Test parsing invalid Go code."""
    code = """
this is not valid go code
"""
    with pytest.raises(LanguageParserError):
        parse_go("test.go", code)
