"""Comprehensive tests for the Python parser to improve coverage."""

from codeconcat.parser.language_parsers.python_parser import PythonParser
from codeconcat.base_types import ParsedFileData


class TestPythonParserComprehensive:
    """Comprehensive test suite for Python parser."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = PythonParser()

    def test_parse_simple_function(self):
        """Test parsing a simple function."""
        code = '''
def hello_world():
    """Say hello."""
    print("Hello, World!")
'''
        result = self.parser.parse(code)
        assert isinstance(result, ParsedFileData)
        assert len(result.declarations) == 1
        assert result.declarations[0].name == "hello_world"
        assert result.declarations[0].kind == "function"
        assert result.declarations[0].start_line == 2
        assert result.declarations[0].end_line == 4

    def test_parse_class_with_methods(self):
        """Test parsing a class with methods."""
        code = '''
class Calculator:
    """A simple calculator class."""
    
    def __init__(self):
        self.result = 0
    
    def add(self, a, b):
        """Add two numbers."""
        return a + b
    
    def subtract(self, a, b):
        """Subtract b from a."""
        return a - b
'''
        result = self.parser.parse(code)
        assert len(result.declarations) == 4  # class + 3 methods

        # Check class declaration
        class_decl = result.declarations[0]
        assert class_decl.name == "Calculator"
        assert class_decl.kind == "class"

        # Check methods
        method_names = [d.name for d in result.declarations[1:]]
        assert "__init__" in method_names
        assert "add" in method_names
        assert "subtract" in method_names

    def test_parse_decorated_function(self):
        """Test parsing decorated functions."""
        code = '''
@property
@lru_cache(maxsize=128)
def expensive_property(self):
    """An expensive computed property."""
    return self._compute_value()
'''
        result = self.parser.parse(code)
        assert len(result.declarations) == 1
        assert result.declarations[0].name == "expensive_property"
        assert result.declarations[0].kind == "function"

    def test_parse_async_function(self):
        """Test parsing async functions."""
        code = '''
async def fetch_data(url):
    """Fetch data from URL asynchronously."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
'''
        result = self.parser.parse(code)
        assert len(result.declarations) == 1
        assert result.declarations[0].name == "fetch_data"
        assert result.declarations[0].kind == "function"

    def test_parse_nested_classes(self):
        """Test parsing nested classes."""
        code = '''
class Outer:
    """Outer class."""
    
    class Inner:
        """Inner class."""
        
        def inner_method(self):
            """Method in inner class."""
            pass
    
    def outer_method(self):
        """Method in outer class."""
        pass
'''
        result = self.parser.parse(code)
        # Should find: Outer, Inner, inner_method, outer_method
        assert len(result.declarations) == 4

        class_names = [d.name for d in result.declarations if d.kind == "class"]
        assert "Outer" in class_names
        assert "Inner" in class_names

    def test_parse_generator_function(self):
        """Test parsing generator functions."""
        code = '''
def fibonacci(n):
    """Generate Fibonacci sequence."""
    a, b = 0, 1
    for _ in range(n):
        yield a
        a, b = b, a + b
'''
        result = self.parser.parse(code)
        assert len(result.declarations) == 1
        assert result.declarations[0].name == "fibonacci"

    def test_parse_lambda_in_variable(self):
        """Test parsing lambda functions assigned to variables."""
        code = """
square = lambda x: x ** 2
add = lambda x, y: x + y
multiply = lambda *args: reduce(lambda x, y: x * y, args)
"""
        result = self.parser.parse(code)
        # Lambda parsing might not capture all, but should handle basic cases
        assert isinstance(result, ParsedFileData)

    def test_parse_imports(self):
        """Test parsing import statements."""
        code = """
import os
import sys
from typing import List, Dict, Optional
from collections import defaultdict
from .local_module import helper_function
"""
        result = self.parser.parse(code)
        assert len(result.imports) >= 5
        import_names = [imp.module_name for imp in result.imports]
        assert "os" in import_names
        assert "sys" in import_names
        assert "typing" in import_names

    def test_parse_type_hints(self):
        """Test parsing functions with type hints."""
        code = '''
def greet(name: str, age: int = 18) -> str:
    """Greet a person with their name and age."""
    return f"Hello {name}, you are {age} years old"

def process_items(items: List[Dict[str, Any]]) -> Optional[int]:
    """Process a list of items."""
    if not items:
        return None
    return len(items)
'''
        result = self.parser.parse(code)
        assert len(result.declarations) == 2
        assert all(d.kind == "function" for d in result.declarations)

    def test_parse_context_manager(self):
        """Test parsing context manager classes."""
        code = '''
class FileManager:
    """Context manager for file operations."""
    
    def __init__(self, filename, mode):
        self.filename = filename
        self.mode = mode
        self.file = None
    
    def __enter__(self):
        """Enter the context."""
        self.file = open(self.filename, self.mode)
        return self.file
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context."""
        self.file.close()
'''
        result = self.parser.parse(code)
        assert len(result.declarations) == 4  # class + 3 methods
        method_names = [d.name for d in result.declarations if d.kind == "function"]
        assert "__enter__" in method_names
        assert "__exit__" in method_names

    def test_parse_property_decorator(self):
        """Test parsing property decorators."""
        code = '''
class Temperature:
    def __init__(self):
        self._celsius = 0
    
    @property
    def celsius(self):
        """Get temperature in Celsius."""
        return self._celsius
    
    @celsius.setter
    def celsius(self, value):
        """Set temperature in Celsius."""
        self._celsius = value
    
    @property
    def fahrenheit(self):
        """Get temperature in Fahrenheit."""
        return self._celsius * 9/5 + 32
'''
        result = self.parser.parse(code)
        # Should find class and all methods/properties
        assert len(result.declarations) >= 4

    def test_parse_dataclass(self):
        """Test parsing dataclasses."""
        code = '''
from dataclasses import dataclass, field
from typing import List

@dataclass
class Person:
    """A person with name and age."""
    name: str
    age: int = 18
    hobbies: List[str] = field(default_factory=list)
    
    def greet(self):
        """Greet the person."""
        return f"Hello, I'm {self.name}"
'''
        result = self.parser.parse(code)
        assert len(result.declarations) == 2  # class + method
        assert result.declarations[0].name == "Person"
        assert result.declarations[0].kind == "class"

    def test_parse_metaclass(self):
        """Test parsing metaclasses."""
        code = '''
class SingletonMeta(type):
    """Metaclass for singleton pattern."""
    _instances = {}
    
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

class Database(metaclass=SingletonMeta):
    """Singleton database connection."""
    def __init__(self):
        self.connection = None
'''
        result = self.parser.parse(code)
        assert len(result.declarations) >= 3  # 2 classes + methods

    def test_parse_comprehensions(self):
        """Test parsing various comprehensions."""
        code = '''
# List comprehension
squares = [x**2 for x in range(10)]

# Dictionary comprehension  
square_dict = {x: x**2 for x in range(5)}

# Set comprehension
unique_squares = {x**2 for x in range(-5, 6)}

# Generator expression
sum_of_squares = sum(x**2 for x in range(100))

def get_evens(numbers):
    """Get even numbers using comprehension."""
    return [n for n in numbers if n % 2 == 0]
'''
        result = self.parser.parse(code)
        assert len(result.declarations) == 1  # Only the function
        assert result.declarations[0].name == "get_evens"

    def test_parse_exception_handling(self):
        """Test parsing exception handling code."""
        code = '''
def safe_divide(a, b):
    """Safely divide two numbers."""
    try:
        result = a / b
    except ZeroDivisionError:
        return None
    except TypeError as e:
        raise ValueError(f"Invalid types: {e}")
    else:
        return result
    finally:
        print("Division attempted")
'''
        result = self.parser.parse(code)
        assert len(result.declarations) == 1
        assert result.declarations[0].name == "safe_divide"

    def test_parse_walrus_operator(self):
        """Test parsing code with walrus operator (Python 3.8+)."""
        code = '''
def process_data(data):
    """Process data with walrus operator."""
    if (n := len(data)) > 10:
        return f"Large dataset: {n} items"
    return f"Small dataset: {n} items"
'''
        result = self.parser.parse(code)
        assert len(result.declarations) == 1

    def test_parse_match_statement(self):
        """Test parsing match statements (Python 3.10+)."""
        code = '''
def handle_command(command):
    """Handle command using match statement."""
    match command.split():
        case ["quit"]:
            return "Goodbye!"
        case ["hello", name]:
            return f"Hello, {name}!"
        case _:
            return "Unknown command"
'''
        result = self.parser.parse(code)
        assert len(result.declarations) == 1

    def test_parse_multiline_strings(self):
        """Test parsing multiline string handling."""
        code = '''
def get_help_text():
    """Get help text."""
    return """
    This is a multiline help text.
    It spans multiple lines and contains:
    - Bullet points
    - Special characters: @#$%
    - Unicode: ñ, é, 中文
    """

SQL_QUERY = """
    SELECT * FROM users
    WHERE active = TRUE
    ORDER BY created_at DESC
"""
'''
        result = self.parser.parse(code)
        assert len(result.declarations) == 1

    def test_parse_error_handling(self):
        """Test parser error handling with invalid code."""
        invalid_code = '''
def broken_function(
    """This is broken Python code
    return "test"
'''
        result = self.parser.parse(invalid_code)
        # Parser should handle errors gracefully
        assert isinstance(result, ParsedFileData)

    def test_empty_file(self):
        """Test parsing empty file."""
        result = self.parser.parse("")
        assert isinstance(result, ParsedFileData)
        assert len(result.declarations) == 0
        assert len(result.imports) == 0

    def test_comments_only(self):
        """Test parsing file with only comments."""
        code = """
# This is a comment
# Another comment
"""
        result = self.parser.parse(code)
        assert isinstance(result, ParsedFileData)
        assert len(result.declarations) == 0
