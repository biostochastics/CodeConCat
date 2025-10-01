#!/usr/bin/env python3
"""Comprehensive smoke tests for tree-sitter C++ parser.

Tests basic functionality, include extraction, declaration extraction,
docstring handling (Doxygen), and error resilience for the C++ parser.
"""

import pytest

from codeconcat.parser.language_parsers.tree_sitter_cpp_parser import TreeSitterCppParser


class TestTreeSitterCppSmoke:
    """Smoke tests for TreeSitterCppParser."""

    @pytest.fixture
    def parser(self):
        """Fixture providing a C++ parser instance."""
        return TreeSitterCppParser()

    @pytest.fixture
    def cpp_sample(self):
        """Fixture providing sample C++ code."""
        return '''#include <iostream>
#include <vector>
#include <string>

namespace myapp {

/// Maximum number of retries
const int MAX_RETRIES = 3;

/**
 * @brief Main application class
 *
 * Handles application lifecycle and processing.
 * @author CodeConCat
 */
class Application {
private:
    std::string name;
    std::vector<std::string> items;

public:
    /**
     * @brief Constructor for Application
     * @param app_name The application name
     */
    Application(const std::string& app_name);

    /**
     * @brief Destructor
     */
    ~Application();

    /**
     * @brief Process an item
     * @param item The item to process
     * @return true if successful, false otherwise
     */
    bool processItem(const std::string& item);

    /**
     * @brief Get the application name
     * @return The name string
     */
    std::string getName() const;
};

/**
 * @brief Utility helper class
 */
class Helper {
public:
    /**
     * @brief Validate input string
     * @param input The string to validate
     * @return true if valid
     */
    static bool validate(const std::string& input);
};

}  // namespace myapp

// Template function
/**
 * @brief Generic max function
 * @tparam T The type parameter
 * @param a First value
 * @param b Second value
 * @return The maximum value
 */
template<typename T>
T max(T a, T b) {
    return (a > b) ? a : b;
}
'''

    def test_parser_initialization(self, parser):
        """Test parser initializes correctly."""
        assert parser is not None
        assert parser.language_name == "cpp"
        assert parser.ts_language is not None

    def test_basic_parsing(self, parser, cpp_sample):
        """Test basic parsing returns valid result."""
        result = parser.parse(cpp_sample, "Application.cpp")

        assert result is not None
        assert hasattr(result, "declarations")
        assert hasattr(result, "imports")
        assert result.error is None

    def test_include_extraction(self, parser, cpp_sample):
        """Test include directive extraction."""
        result = parser.parse(cpp_sample, "Application.cpp")

        imports = result.imports
        assert len(imports) == 3
        assert "iostream" in imports
        assert "vector" in imports
        assert "string" in imports

    def test_namespace_extraction(self, parser, cpp_sample):
        """Test namespace declaration extraction."""
        result = parser.parse(cpp_sample, "Application.cpp")

        namespaces = [d for d in result.declarations if d.kind == "namespace"]
        assert len(namespaces) >= 1

        myapp_ns = next((ns for ns in namespaces if ns.name == "myapp"), None)
        assert myapp_ns is not None

    def test_class_extraction(self, parser, cpp_sample):
        """Test class declaration extraction."""
        result = parser.parse(cpp_sample, "Application.cpp")

        classes = [d for d in result.declarations if d.kind == "class"]
        assert len(classes) >= 2

        # Check Application class
        app_class = next((c for c in classes if c.name == "Application"), None)
        assert app_class is not None
        assert app_class.docstring is not None
        assert "Main application class" in app_class.docstring

        # Check Helper class
        helper_class = next((c for c in classes if c.name == "Helper"), None)
        assert helper_class is not None

    def test_function_extraction(self, parser, cpp_sample):
        """Test function declaration extraction."""
        result = parser.parse(cpp_sample, "Application.cpp")

        functions = [d for d in result.declarations if d.kind == "function"]

        # Should find processItem, getName, validate, and template function
        assert len(functions) >= 1

        # Check for template function
        max_func = next((f for f in functions if f.name == "max"), None)
        assert max_func is not None

    def test_constructor_extraction(self, parser, cpp_sample):
        """Test constructor extraction."""
        result = parser.parse(cpp_sample, "Application.cpp")

        constructors = [d for d in result.declarations if d.kind == "constructor"]
        assert len(constructors) >= 1

        constructor = constructors[0]
        assert constructor.name == "Application"
        assert "public" in constructor.modifiers

    def test_destructor_extraction(self, parser, cpp_sample):
        """Test destructor extraction."""
        result = parser.parse(cpp_sample, "Application.cpp")

        destructors = [d for d in result.declarations if d.kind == "destructor"]
        assert len(destructors) >= 1

        destructor = destructors[0]
        assert destructor.name == "~Application"
        assert "public" in destructor.modifiers

    def test_doxygen_extraction(self, parser, cpp_sample):
        """Test Doxygen comment extraction and cleaning."""
        result = parser.parse(cpp_sample, "Application.cpp")

        app_class = next((d for d in result.declarations
                         if d.kind == "class" and d.name == "Application"), None)

        assert app_class.docstring is not None
        docstring = app_class.docstring

        # Should not have comment markers
        assert "/**" not in docstring
        assert "*/" not in docstring
        assert "@brief" not in docstring  # Tags should be cleaned

        # Should have cleaned content
        assert "Main application class" in docstring

    def test_line_numbers(self, parser, cpp_sample):
        """Test accurate line number tracking."""
        result = parser.parse(cpp_sample, "Application.cpp")

        app_class = next((d for d in result.declarations
                         if d.kind == "class" and d.name == "Application"), None)

        assert app_class.start_line > 0
        assert app_class.end_line > app_class.start_line

    def test_empty_file(self, parser):
        """Test parser handles empty file gracefully."""
        result = parser.parse("", "Empty.cpp")

        assert result is not None
        assert len(result.declarations) == 0
        assert len(result.imports) == 0

    def test_malformed_syntax(self, parser):
        """Test parser handles syntax errors gracefully."""
        malformed = "class Broken { void test( { }"
        result = parser.parse(malformed, "Broken.cpp")

        # Parser should still return a result (tree-sitter is resilient)
        assert result is not None

    def test_template_class(self, parser):
        """Test parsing template class declarations."""
        template_code = '''
/**
 * @brief Generic container class
 * @tparam T The element type
 */
template<typename T>
class Container {
private:
    std::vector<T> items;

public:
    /**
     * @brief Add an item
     * @param item The item to add
     */
    void add(const T& item) {
        items.push_back(item);
    }

    size_t size() const {
        return items.size();
    }
};
'''
        result = parser.parse(template_code, "Container.h")

        classes = [d for d in result.declarations if d.kind == "class"]
        assert len(classes) >= 1
        container_class = classes[0]
        assert container_class.name == "Container"
        assert "Generic container class" in container_class.docstring

    def test_struct_parsing(self, parser):
        """Test struct declaration parsing."""
        struct_code = '''
/**
 * @brief Point structure
 */
struct Point {
    int x;  ///< X coordinate
    int y;  ///< Y coordinate

    /**
     * @brief Calculate distance from origin
     * @return The distance
     */
    double distanceFromOrigin() const {
        return std::sqrt(x * x + y * y);
    }
};
'''
        result = parser.parse(struct_code, "Point.h")

        structs = [d for d in result.declarations if d.kind == "struct"]
        assert len(structs) >= 1
        assert structs[0].name == "Point"
        assert "Point structure" in structs[0].docstring

    def test_enum_parsing(self, parser):
        """Test enum declaration parsing."""
        enum_code = '''
/**
 * @brief Status enumeration
 */
enum class Status {
    Active,    ///< Active status
    Inactive,  ///< Inactive status
    Pending    ///< Pending status
};
'''
        result = parser.parse(enum_code, "Status.h")

        enums = [d for d in result.declarations if d.kind == "enum"]
        assert len(enums) >= 1
        assert enums[0].name == "Status"
        assert "Status enumeration" in enums[0].docstring

    def test_inline_triple_slash_comments(self, parser):
        """Test inline /// Doxygen comments."""
        inline_doc_code = '''
/// A simple function with inline documentation
int add(int a, int b) {
    return a + b;
}
'''
        result = parser.parse(inline_doc_code, "math.cpp")

        functions = [d for d in result.declarations if d.kind == "function"]
        assert len(functions) >= 1
        add_func = functions[0]
        assert add_func.name == "add"
        # Inline /// comments should be extracted
        assert add_func.docstring is not None

    def test_const_method(self, parser):
        """Test const method parsing."""
        const_code = '''
class Data {
public:
    /**
     * @brief Get value (const)
     */
    int getValue() const;
};
'''
        result = parser.parse(const_code, "Data.h")

        functions = [d for d in result.declarations if d.kind == "function"]
        get_value = next((f for f in functions if f.name == "getValue"), None)
        assert get_value is not None
        assert "const" in get_value.modifiers

    def test_operator_overload(self, parser):
        """Test operator overload parsing."""
        operator_code = '''
class Vector {
public:
    /**
     * @brief Addition operator
     */
    Vector operator+(const Vector& other) const;

    /**
     * @brief Equality operator
     */
    bool operator==(const Vector& other) const;
};
'''
        result = parser.parse(operator_code, "Vector.h")

        # Operators might be captured as functions or methods
        functions = [d for d in result.declarations if d.kind in ["function", "method", "operator"]]
        assert len(functions) >= 2
