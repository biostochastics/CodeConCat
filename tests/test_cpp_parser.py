"""Tests for C++ code parser."""

import unittest

from codeconcat.parser.language_parsers.cpp_parser import CppParser


class TestCppParser(unittest.TestCase):
    def setUp(self):
        self.parser = CppParser()

    def test_class_declarations(self):
        cpp_code = """
        // Regular class
        class MyClass {
            int x;
        };

        // Template class
        template<typename T>
        class TemplateClass {
            T value;
        };

        // Struct
        struct MyStruct {
            double y;
        };
        """
        declarations = self.parser.parse(cpp_code)
        class_names = {d.name for d in declarations if d.kind == "class"}
        self.assertEqual(class_names, {"MyClass", "TemplateClass", "MyStruct"})

    def test_function_declarations(self):
        cpp_code = """
        // Regular function
        void func1(int x) {
            return x + 1;
        }

        // Template function
        template<typename T>
        T func2(T x) {
            return x * 2;
        }

        // Function with specifiers
        int func3() const noexcept {
            return 42;
        }

        // Default/delete functions
        void func4() = default;
        void func5() = delete;
        """
        declarations = self.parser.parse(cpp_code)
        func_names = {d.name for d in declarations if d.kind == "function"}
        self.assertEqual(func_names, {"func1", "func2", "func3", "func4", "func5"})

    def test_namespace_declarations(self):
        cpp_code = """
        namespace ns1 {
            void func1() {}
        }

        namespace ns2 {
            class MyClass {};
        }
        """
        declarations = self.parser.parse(cpp_code)
        namespace_names = {d.name for d in declarations if d.kind == "namespace"}
        self.assertEqual(namespace_names, {"ns1", "ns2"})

    def test_enum_declarations(self):
        cpp_code = """
        enum Color {
            RED,
            GREEN,
            BLUE
        };

        enum class Direction {
            NORTH,
            SOUTH,
            EAST,
            WEST
        };
        """
        declarations = self.parser.parse(cpp_code)
        enum_names = {d.name for d in declarations if d.kind == "enum"}
        self.assertEqual(enum_names, {"Color", "Direction"})

    def test_typedef_declarations(self):
        cpp_code = """
        typedef int Integer;
        typedef double* DoublePtr;
        typedef void (*FuncPtr)(int);
        """
        declarations = self.parser.parse(cpp_code)
        typedef_names = {d.name for d in declarations if d.kind == "typedef"}
        self.assertEqual(typedef_names, {"Integer", "DoublePtr", "FuncPtr"})

    def test_using_declarations(self):
        cpp_code = """
        using MyInt = int;
        using MyFunc = void(*)(double);
        """
        declarations = self.parser.parse(cpp_code)
        using_names = {d.name for d in declarations if d.kind == "using"}
        self.assertEqual(using_names, {"MyInt", "MyFunc"})
