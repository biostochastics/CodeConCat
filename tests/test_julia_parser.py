"""Tests for Julia parser."""

import pytest

from codeconcat.errors import LanguageParserError
from codeconcat.parser.language_parsers.julia_parser import parse_julia


def test_parse_julia_function():
    """Test parsing Julia functions."""
    code = """
function greet()
    println("Hello, World!")
end

function add(x::Int, y::Int)::Int
    return x + y
end

# One-line function definition
square(x) = x * x
"""
    result = parse_julia("test.jl", code)
    assert result is not None
    assert len(result.declarations) == 3

    greet = next(d for d in result.declarations if d.name == "greet")
    assert greet.kind == "function"
    assert greet.start_line == 2

    add = next(d for d in result.declarations if d.name == "add")
    assert add.kind == "function"
    assert add.start_line == 6

    square = next(d for d in result.declarations if d.name == "square")
    assert square.kind == "function"
    assert square.start_line == 10


def test_parse_julia_struct():
    """Test parsing Julia structs."""
    code = """
struct Point
    x::Float64
    y::Float64
end

mutable struct Person
    name::String
    age::Int
end
"""
    result = parse_julia("test.jl", code)
    assert result is not None
    assert len(result.declarations) == 2

    point = next(d for d in result.declarations if d.name == "Point")
    assert point.kind == "struct"
    assert point.start_line == 2

    person = next(d for d in result.declarations if d.name == "Person")
    assert person.kind == "struct"
    assert person.start_line == 7


def test_parse_julia_abstract_type():
    """Test parsing Julia abstract types."""
    code = """
abstract type Shape end

abstract type Animal <: Organism end
"""
    result = parse_julia("test.jl", code)
    assert result is not None
    assert len(result.declarations) == 2

    shape = next(d for d in result.declarations if d.name == "Shape")
    assert shape.kind == "abstract"
    assert shape.start_line == 2

    animal = next(d for d in result.declarations if d.name == "Animal")
    assert animal.kind == "abstract"
    assert animal.start_line == 4


def test_parse_julia_module():
    """Test parsing Julia modules."""
    code = """
module Geometry

export Point, distance

struct Point
    x::Float64
    y::Float64
end

function distance(p1::Point, p2::Point)
    sqrt((p2.x - p1.x)^2 + (p2.y - p1.y)^2)
end

end # module
"""
    result = parse_julia("test.jl", code)
    assert result is not None
    assert len(result.declarations) == 4

    module_decl = next(d for d in result.declarations if d.name == "Geometry")
    assert module_decl.kind == "module"
    assert module_decl.start_line == 2

    point = next(d for d in result.declarations if d.name == "Point")
    assert point.kind == "struct"
    assert point.start_line == 6

    distance = next(d for d in result.declarations if d.name == "distance")
    assert distance.kind == "function"
    assert distance.start_line == 10


def test_parse_julia_macro():
    """Test parsing Julia macros."""
    code = """
macro debug(expr)
    return :(println("Debug: ", $(esc(expr))))
end

@inline function fast_function(x)
    x + 1
end
"""
    result = parse_julia("test.jl", code)
    assert result is not None
    assert len(result.declarations) == 2

    debug = next(d for d in result.declarations if d.name == "debug")
    assert debug.kind == "macro"
    assert debug.start_line == 2

    fast_function = next(d for d in result.declarations if d.name == "fast_function")
    assert fast_function.kind == "function"
    assert fast_function.start_line == 6


def test_parse_julia_empty():
    """Test parsing empty Julia file."""
    result = parse_julia("test.jl", "")
    assert result is not None
    assert len(result.declarations) == 0


def test_parse_julia_invalid():
    """Test parsing invalid Julia code."""
    code = """
this is not valid julia code
"""
    with pytest.raises(LanguageParserError):
        parse_julia("test.jl", code)
