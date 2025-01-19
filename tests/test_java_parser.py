"""Tests for Java parser."""

import pytest

from codeconcat.parser.language_parsers.java_parser import parse_java


def test_parse_java_class():
    """Test parsing Java classes."""
    code = """
public class Person {
    private String name;
    private int age;
    
    public Person(String name, int age) {
        this.name = name;
        this.age = age;
    }
    
    public String getName() {
        return name;
    }
}

class Employee extends Person {
    private double salary;
    
    public Employee(String name, int age, double salary) {
        super(name, age);
        this.salary = salary;
    }
}
"""
    result = parse_java("test.java", code)
    assert result is not None
    assert len(result.declarations) == 2

    person = next(d for d in result.declarations if d.name == "Person")
    assert person.kind == "class"
    assert person.start_line == 2

    employee = next(d for d in result.declarations if d.name == "Employee")
    assert employee.kind == "class"
    assert employee.start_line == 15


def test_parse_java_interface():
    """Test parsing Java interfaces."""
    code = """
public interface Readable {
    String read();
}

interface Writable {
    void write(String data);
}
"""
    result = parse_java("test.java", code)
    assert result is not None
    assert len(result.declarations) == 2

    readable = next(d for d in result.declarations if d.name == "Readable")
    assert readable.kind == "interface"
    assert readable.start_line == 2

    writable = next(d for d in result.declarations if d.name == "Writable")
    assert writable.kind == "interface"
    assert writable.start_line == 6


def test_parse_java_method():
    """Test parsing Java methods."""
    code = """
public class Calculator {
    public int add(int a, int b) {
        return a + b;
    }
    
    private double multiply(double x, double y) {
        return x * y;
    }
    
    protected static void log(String message) {
        System.out.println(message);
    }
}
"""
    result = parse_java("test.java", code)
    assert result is not None
    assert len(result.declarations) == 4

    calc = next(d for d in result.declarations if d.name == "Calculator")
    assert calc.kind == "class"
    assert calc.start_line == 2

    add = next(d for d in result.declarations if d.name == "add")
    assert add.kind == "method"
    assert add.start_line == 3

    multiply = next(d for d in result.declarations if d.name == "multiply")
    assert multiply.kind == "method"
    assert multiply.start_line == 7

    log = next(d for d in result.declarations if d.name == "log")
    assert log.kind == "method"
    assert log.start_line == 11


def test_parse_java_field():
    """Test parsing Java fields."""
    code = """
public class Constants {
    public static final int MAX_VALUE = 100;
    private static String prefix = "test";
    protected boolean debug = false;
}
"""
    result = parse_java("test.java", code)
    assert result is not None
    assert len(result.declarations) == 4

    constants = next(d for d in result.declarations if d.name == "Constants")
    assert constants.kind == "class"
    assert constants.start_line == 2

    max_value = next(d for d in result.declarations if d.name == "MAX_VALUE")
    assert max_value.kind == "field"
    assert max_value.start_line == 3

    prefix = next(d for d in result.declarations if d.name == "prefix")
    assert prefix.kind == "field"
    assert prefix.start_line == 4

    debug = next(d for d in result.declarations if d.name == "debug")
    assert debug.kind == "field"
    assert debug.start_line == 5


def test_parse_java_empty():
    """Test parsing empty Java file."""
    result = parse_java("test.java", "")
    assert result is not None
    assert len(result.declarations) == 0


def test_parse_java_invalid():
    """Test parsing invalid Java code."""
    code = """
this is not valid java code
"""
    result = parse_java("test.java", code)
    assert result is not None
    assert len(result.declarations) == 0
