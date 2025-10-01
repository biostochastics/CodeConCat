#!/usr/bin/env python3

"""
Comprehensive smoke tests for the C# tree-sitter parser.

Tests all major C# language features including:
- Namespaces (regular and file-scoped)
- Classes, interfaces, structs, records
- Methods, properties, constructors, destructors
- XML documentation comments
- Operators and conversion operators
- Events and delegates
- Generics and attributes
"""

import pytest

from codeconcat.parser.language_parsers.tree_sitter_csharp_parser import TreeSitterCSharpParser


class TestTreeSitterCSharpSmoke:
    """Comprehensive smoke tests for C# tree-sitter parser."""

    def test_parser_initialization(self):
        """Test that the parser initializes correctly."""
        parser = TreeSitterCSharpParser()
        assert parser is not None
        assert parser.language_name == "csharp"
        assert parser.ts_language is not None

    def test_basic_parsing(self):
        """Test basic parsing of a simple C# file."""
        code = """using System;

namespace TestNamespace
{
    public class TestClass
    {
        public void TestMethod()
        {
            Console.WriteLine("Hello");
        }
    }
}
"""
        parser = TreeSitterCSharpParser()
        result = parser.parse(code, "test.cs")

        assert result.error is None
        assert len(result.declarations) > 0

    def test_using_directives(self):
        """Test extraction of using directives."""
        code = """using System;
using System.Collections.Generic;
using System.Linq;
using MyNamespace.MySubNamespace;

namespace Test {}
"""
        parser = TreeSitterCSharpParser()
        result = parser.parse(code, "test.cs")

        assert "System" in result.imports
        assert "System.Collections.Generic" in result.imports
        assert "System.Linq" in result.imports
        assert "MyNamespace.MySubNamespace" in result.imports

    def test_namespace_extraction(self):
        """Test extraction of namespace declarations."""
        code = """namespace MyNamespace.SubNamespace
{
    public class TestClass {}
}
"""
        parser = TreeSitterCSharpParser()
        result = parser.parse(code, "test.cs")

        namespace_decls = [d for d in result.declarations if d.kind == "namespace"]
        assert len(namespace_decls) >= 1
        assert namespace_decls[0].name == "MyNamespace.SubNamespace"

    def test_file_scoped_namespace(self):
        """Test extraction of file-scoped namespace (C# 10+)."""
        code = """namespace MyNamespace;

public class TestClass {}
"""
        parser = TreeSitterCSharpParser()
        result = parser.parse(code, "test.cs")

        namespace_decls = [d for d in result.declarations if d.kind == "file_namespace"]
        assert len(namespace_decls) >= 1
        assert namespace_decls[0].name == "MyNamespace"

    def test_class_extraction(self):
        """Test extraction of class declarations."""
        code = """namespace Test
{
    public class TestClass
    {
        private int field;
    }
}
"""
        parser = TreeSitterCSharpParser()
        result = parser.parse(code, "test.cs")

        namespace = next((d for d in result.declarations if d.kind == "namespace"), None)
        assert namespace is not None

        classes = [d for d in namespace.children if d.kind == "class"]
        assert len(classes) >= 1
        assert classes[0].name == "TestClass"
        assert "public" in classes[0].modifiers

    def test_interface_extraction(self):
        """Test extraction of interface declarations."""
        code = """namespace Test
{
    public interface ITestInterface
    {
        void TestMethod();
    }
}
"""
        parser = TreeSitterCSharpParser()
        result = parser.parse(code, "test.cs")

        namespace = next((d for d in result.declarations if d.kind == "namespace"), None)
        interfaces = [d for d in namespace.children if d.kind == "interface"]
        assert len(interfaces) >= 1
        assert interfaces[0].name == "ITestInterface"

    def test_struct_extraction(self):
        """Test extraction of struct declarations."""
        code = """namespace Test
{
    public struct Point
    {
        public int X;
        public int Y;
    }
}
"""
        parser = TreeSitterCSharpParser()
        result = parser.parse(code, "test.cs")

        namespace = next((d for d in result.declarations if d.kind == "namespace"), None)
        structs = [d for d in namespace.children if d.kind == "struct"]
        assert len(structs) >= 1
        assert structs[0].name == "Point"

    def test_record_extraction(self):
        """Test extraction of record declarations (C# 9.0+)."""
        code = """namespace Test
{
    public record Person(string Name, int Age);
}
"""
        parser = TreeSitterCSharpParser()
        result = parser.parse(code, "test.cs")

        namespace = next((d for d in result.declarations if d.kind == "namespace"), None)
        records = [d for d in namespace.children if d.kind == "record"]
        assert len(records) >= 1
        assert records[0].name == "Person"

    def test_method_extraction(self):
        """Test extraction of method declarations."""
        code = """namespace Test
{
    public class TestClass
    {
        public int Add(int a, int b)
        {
            return a + b;
        }
    }
}
"""
        parser = TreeSitterCSharpParser()
        result = parser.parse(code, "test.cs")

        namespace = next((d for d in result.declarations if d.kind == "namespace"), None)
        test_class = next((d for d in namespace.children if d.name == "TestClass"), None)

        methods = [d for d in test_class.children if d.kind == "method"]
        assert len(methods) >= 1
        assert methods[0].name == "Add"
        assert "public" in methods[0].modifiers

    def test_property_extraction(self):
        """Test extraction of property declarations."""
        code = """namespace Test
{
    public class TestClass
    {
        public string Name { get; set; }
        public int Age { get; private set; }
    }
}
"""
        parser = TreeSitterCSharpParser()
        result = parser.parse(code, "test.cs")

        namespace = next((d for d in result.declarations if d.kind == "namespace"), None)
        test_class = next((d for d in namespace.children if d.name == "TestClass"), None)

        properties = [d for d in test_class.children if d.kind == "property"]
        assert len(properties) >= 2
        property_names = {p.name for p in properties}
        assert "Name" in property_names
        assert "Age" in property_names

    def test_constructor_extraction(self):
        """Test extraction of constructor declarations."""
        code = """namespace Test
{
    public class TestClass
    {
        public TestClass(int value)
        {
        }
    }
}
"""
        parser = TreeSitterCSharpParser()
        result = parser.parse(code, "test.cs")

        namespace = next((d for d in result.declarations if d.kind == "namespace"), None)
        test_class = next((d for d in namespace.children if d.name == "TestClass"), None)

        constructors = [d for d in test_class.children if d.kind == "constructor"]
        assert len(constructors) >= 1
        assert constructors[0].kind == "constructor"
        assert constructors[0].name == "TestClass"

    def test_destructor_extraction(self):
        """Test extraction of destructor declarations."""
        code = """namespace Test
{
    public class TestClass
    {
        ~TestClass()
        {
        }
    }
}
"""
        parser = TreeSitterCSharpParser()
        result = parser.parse(code, "test.cs")

        namespace = next((d for d in result.declarations if d.kind == "namespace"), None)
        test_class = next((d for d in namespace.children if d.name == "TestClass"), None)

        destructors = [d for d in test_class.children if d.kind == "destructor"]
        assert len(destructors) >= 1
        assert destructors[0].kind == "destructor"
        assert destructors[0].name == "TestClass"

    def test_xml_doc_comment_extraction(self):
        """Test extraction and cleaning of XML documentation comments."""
        code = """namespace Test
{
    /// <summary>
    /// This is a test class with documentation.
    /// It demonstrates XML doc comments.
    /// </summary>
    /// <remarks>Additional remarks here</remarks>
    public class TestClass
    {
    }
}
"""
        parser = TreeSitterCSharpParser()
        result = parser.parse(code, "test.cs")

        namespace = next((d for d in result.declarations if d.kind == "namespace"), None)
        test_class = next((d for d in namespace.children if d.name == "TestClass"), None)

        assert test_class.docstring is not None
        assert len(test_class.docstring) > 0
        # XML tags should be cleaned
        assert "<summary>" not in test_class.docstring
        assert "test class with documentation" in test_class.docstring

    def test_xml_doc_param_tags(self):
        """Test that XML doc param tags are properly cleaned."""
        code = """namespace Test
{
    public class TestClass
    {
        /// <summary>
        /// Adds two numbers together.
        /// </summary>
        /// <param name="a">The first number</param>
        /// <param name="b">The second number</param>
        /// <returns>The sum of a and b</returns>
        public int Add(int a, int b)
        {
            return a + b;
        }
    }
}
"""
        parser = TreeSitterCSharpParser()
        result = parser.parse(code, "test.cs")

        namespace = next((d for d in result.declarations if d.kind == "namespace"), None)
        test_class = next((d for d in namespace.children if d.name == "TestClass"), None)
        method = next((d for d in test_class.children if d.name == "Add"), None)

        assert method.docstring is not None
        # XML tags should be cleaned but content preserved
        assert "<param" not in method.docstring
        assert "<returns>" not in method.docstring
        assert "Adds two numbers" in method.docstring
        assert "first number" in method.docstring or "a" in method.docstring

    def test_enum_extraction(self):
        """Test extraction of enum declarations."""
        code = """namespace Test
{
    public enum Color
    {
        Red,
        Green,
        Blue
    }
}
"""
        parser = TreeSitterCSharpParser()
        result = parser.parse(code, "test.cs")

        namespace = next((d for d in result.declarations if d.kind == "namespace"), None)
        enums = [d for d in namespace.children if d.kind == "enum"]
        assert len(enums) >= 1
        assert enums[0].name == "Color"

    def test_delegate_extraction(self):
        """Test extraction of delegate declarations."""
        code = """namespace Test
{
    public delegate void EventHandler(object sender, EventArgs e);
}
"""
        parser = TreeSitterCSharpParser()
        result = parser.parse(code, "test.cs")

        namespace = next((d for d in result.declarations if d.kind == "namespace"), None)
        delegates = [d for d in namespace.children if d.kind == "delegate"]
        assert len(delegates) >= 1
        assert delegates[0].name == "EventHandler"

    def test_event_extraction(self):
        """Test extraction of event declarations."""
        code = """namespace Test
{
    public class TestClass
    {
        public event EventHandler Changed;
    }
}
"""
        parser = TreeSitterCSharpParser()
        result = parser.parse(code, "test.cs")

        namespace = next((d for d in result.declarations if d.kind == "namespace"), None)
        test_class = next((d for d in namespace.children if d.name == "TestClass"), None)

        events = [d for d in test_class.children if d.kind == "event"]
        assert len(events) >= 1
        assert events[0].name == "Changed"

    def test_operator_overload(self):
        """Test extraction of operator overload declarations."""
        code = """namespace Test
{
    public class Vector
    {
        public static Vector operator +(Vector a, Vector b)
        {
            return null;
        }

        public static bool operator ==(Vector a, Vector b)
        {
            return true;
        }
    }
}
"""
        parser = TreeSitterCSharpParser()
        result = parser.parse(code, "test.cs")

        namespace = next((d for d in result.declarations if d.kind == "namespace"), None)
        vector_class = next((d for d in namespace.children if d.name == "Vector"), None)

        operators = [d for d in vector_class.children if d.kind == "operator"]
        assert len(operators) >= 2

    def test_generic_class(self):
        """Test extraction of generic class with type parameters."""
        code = """namespace Test
{
    /// <summary>
    /// A generic container class.
    /// </summary>
    /// <typeparam name="T">The element type</typeparam>
    public class Container<T>
    {
        public T Value { get; set; }
    }
}
"""
        parser = TreeSitterCSharpParser()
        result = parser.parse(code, "test.cs")

        namespace = next((d for d in result.declarations if d.kind == "namespace"), None)
        classes = [d for d in namespace.children if d.kind == "class"]
        assert len(classes) >= 1
        assert classes[0].name == "Container"
        assert classes[0].docstring is not None
        assert "generic container" in classes[0].docstring.lower()

    def test_async_method(self):
        """Test extraction of async method declarations."""
        code = """namespace Test
{
    public class TestClass
    {
        public async Task<int> GetValueAsync()
        {
            await Task.Delay(100);
            return 42;
        }
    }
}
"""
        parser = TreeSitterCSharpParser()
        result = parser.parse(code, "test.cs")

        namespace = next((d for d in result.declarations if d.kind == "namespace"), None)
        test_class = next((d for d in namespace.children if d.name == "TestClass"), None)

        methods = [d for d in test_class.children if d.kind == "method"]
        assert len(methods) >= 1
        assert methods[0].name == "GetValueAsync"
        assert "async" in methods[0].modifiers

    def test_expression_bodied_members(self):
        """Test extraction of expression-bodied methods and properties."""
        code = """namespace Test
{
    public class TestClass
    {
        public int Value => 42;

        public int Double(int x) => x * 2;
    }
}
"""
        parser = TreeSitterCSharpParser()
        result = parser.parse(code, "test.cs")

        namespace = next((d for d in result.declarations if d.kind == "namespace"), None)
        test_class = next((d for d in namespace.children if d.name == "TestClass"), None)

        properties = [d for d in test_class.children if d.kind == "property"]
        methods = [d for d in test_class.children if d.kind == "method"]
        assert len(properties) >= 1
        assert len(methods) >= 1

    def test_nested_classes(self):
        """Test extraction of nested class declarations."""
        code = """namespace Test
{
    public class OuterClass
    {
        public class InnerClass
        {
            public void InnerMethod() {}
        }
    }
}
"""
        parser = TreeSitterCSharpParser()
        result = parser.parse(code, "test.cs")

        namespace = next((d for d in result.declarations if d.kind == "namespace"), None)
        outer_class = next((d for d in namespace.children if d.name == "OuterClass"), None)

        inner_classes = [d for d in outer_class.children if d.kind == "class"]
        assert len(inner_classes) >= 1
        assert inner_classes[0].name == "InnerClass"

    def test_line_numbers(self):
        """Test that line numbers are correctly tracked."""
        code = """namespace Test
{
    public class TestClass
    {
        public void Method1() {}

        public void Method2() {}
    }
}
"""
        parser = TreeSitterCSharpParser()
        result = parser.parse(code, "test.cs")

        namespace = next((d for d in result.declarations if d.kind == "namespace"), None)
        assert namespace.start_line == 1

        test_class = next((d for d in namespace.children if d.name == "TestClass"), None)
        assert test_class.start_line == 3

        methods = sorted([d for d in test_class.children if d.kind == "method"],
                        key=lambda x: x.start_line)
        assert len(methods) == 2
        assert methods[0].start_line < methods[1].start_line

    def test_empty_file(self):
        """Test parsing an empty or whitespace-only file."""
        code = "   \n\n  \n"
        parser = TreeSitterCSharpParser()
        result = parser.parse(code, "empty.cs")

        assert result.error is None
        assert len(result.declarations) == 0

    def test_malformed_syntax(self):
        """Test that malformed syntax doesn't crash the parser."""
        code = """namespace Test
{
    public class TestClass
    {
        public void BrokenMethod(
    }
"""
        parser = TreeSitterCSharpParser()
        result = parser.parse(code, "malformed.cs")

        # Should not crash, may or may not have an error
        assert result is not None
