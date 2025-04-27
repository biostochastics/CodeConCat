"""Tests for Python code parser."""

import unittest

from codeconcat.parser.language_parsers.python_parser import PythonParser
from codeconcat.errors import LanguageParserError


class TestPythonParser(unittest.TestCase):
    def setUp(self):
        self.parser = PythonParser()

    def test_function_declarations(self):
        python_code = """
        # Simple function
        def func1(x):
            return x + 1

        # Function with type hints
        def func2(x: int) -> int:
            return x + 1

        # Async function
        async def func3():
            pass

        # Multi-line function
        def complex_func(
            x: int,
            y: str,
            *args,
            **kwargs
        ) -> int:
            return x
        """
        declarations = self.parser.parse(python_code)
        func_names = {d.name for d in declarations if d.kind == "function"}
        self.assertEqual(func_names, {"func1", "func2", "func3", "complex_func"})

    def test_class_declarations(self):
        python_code = """
        # Simple class
        class MyClass:
            pass

        # Class with parent
        class ChildClass(MyClass):
            pass

        # Class with multiple parents
        class MultiChild(MyClass, object):
            pass
        """
        declarations = self.parser.parse(python_code)
        class_names = {d.name for d in declarations if d.kind == "class"}
        self.assertEqual(class_names, {"MyClass", "ChildClass", "MultiChild"})

    def test_decorators(self):
        python_code = """
        # Simple decorator
        @property
        def my_prop(self):
            pass

        # Multiple decorators
        @classmethod
        @staticmethod
        def my_method():
            pass

        # Decorator with arguments
        @my_decorator(
            arg1='value1',
            arg2='value2'
        )
        def decorated_func():
            pass

        # Class decorator
        @singleton
        class MyClass:
            pass
        """
        declarations = self.parser.parse(python_code)

        prop = next(d for d in declarations if d.name == "my_prop")
        method = next(d for d in declarations if d.name == "my_method")
        func = next(d for d in declarations if d.name == "decorated_func")
        cls = next(d for d in declarations if d.name == "MyClass")

        self.assertEqual(prop.modifiers, {"@property"})
        self.assertEqual(method.modifiers, {"@classmethod", "@staticmethod"})
        self.assertTrue(any("@my_decorator" in m for m in func.modifiers))
        self.assertEqual(cls.modifiers, {"@singleton"})

    def test_docstrings(self):
        python_code = '''
        def func_with_docstring():
            """This is a docstring.
            
            It spans multiple lines.
            """
            pass

        class ClassWithDocstring:
            """Class docstring.
            
            With multiple lines.
            """
            pass

        def func_with_quotes():
            """This docstring has "quotes" and \'\'\'triple quotes\'\'\' in it."""
            pass
        '''
        declarations = self.parser.parse(python_code)

        func = next(d for d in declarations if d.name == "func_with_docstring")
        cls = next(d for d in declarations if d.name == "ClassWithDocstring")
        quotes_func = next(d for d in declarations if d.name == "func_with_quotes")

        self.assertTrue(func.docstring)
        self.assertTrue(cls.docstring)
        self.assertTrue(quotes_func.docstring)

    def test_variables_and_constants(self):
        python_code = """
        # Simple variable
        x = 1

        # Variable with type hint
        y: int = 2

        # Multi-line variable
        z = (
            some_function_call()
        )

        # Constants
        CONSTANT = 42
        PI: float = 3.14159
        """
        declarations = self.parser.parse(python_code)

        var_names = {d.name for d in declarations if d.kind == "variable"}
        const_names = {d.name for d in declarations if d.kind == "constant"}

        self.assertEqual(var_names, {"x", "y", "z"})
        self.assertEqual(const_names, {"CONSTANT", "PI"})

    def test_nested_functions(self):
        python_code = """
        def outer():
            def inner1():
                def inner2():
                    pass
                return inner2
            return inner1
        """
        declarations = self.parser.parse(python_code)
        func_names = {d.name for d in declarations if d.kind == "function"}
        self.assertEqual(func_names, {"outer", "inner1", "inner2"})

    def test_invalid_syntax_raises_error(self):
        """Test that parsing invalid Python code raises LanguageParserError."""
        invalid_python_code = """
        def invalid_func(:
            pass
        """
        with self.assertRaises(LanguageParserError):
            self.parser.parse(invalid_python_code)


if __name__ == "__main__":
    unittest.main()
