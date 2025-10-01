"""Comprehensive tests for the Tree-sitter Swift parser.

Tests cover:
- Basic parsing (initialization, functions, classes, structs, enums)
- Attribute extraction (property wrappers, concurrency, availability)
- Enum case extraction
- Function signatures with generics and where clauses
- Property wrappers (@State, @Published, @Binding, etc.)
- Documentation comment extraction
- Import statements
"""

from codeconcat.parser.language_parsers.tree_sitter_swift_parser import (
    TreeSitterSwiftParser,
)


class TestTreeSitterSwiftParser:
    """Test suite for TreeSitterSwiftParser."""

    def test_parser_initialization(self):
        """Test that the parser initializes correctly."""
        parser = TreeSitterSwiftParser()
        assert parser is not None
        assert parser.language_name == "swift"
        assert parser.ts_language is not None
        assert parser.parser is not None

    def test_parse_simple_function(self):
        """Test parsing a simple Swift function."""
        parser = TreeSitterSwiftParser()
        content = """
func greet(name: String) -> String {
    return "Hello, \\(name)!"
}
"""
        result = parser.parse(content, "test.swift")
        assert result is not None
        assert len(result.declarations) >= 1
        functions = [d for d in result.declarations if d.kind == "function"]
        assert len(functions) == 1
        assert functions[0].name == "greet"

    def test_parse_simple_class(self):
        """Test parsing a simple Swift class."""
        parser = TreeSitterSwiftParser()
        content = """
class Person {
    var name: String
    var age: Int

    init(name: String, age: Int) {
        self.name = name
        self.age = age
    }

    func birthday() {
        age += 1
    }
}
"""
        result = parser.parse(content, "test.swift")
        assert result is not None

        classes = [d for d in result.declarations if d.kind == "class"]
        assert len(classes) == 1
        assert classes[0].name == "Person"

        properties = [d for d in result.declarations if d.kind == "property"]
        assert len(properties) >= 2
        property_names = {p.name for p in properties}
        assert "name" in property_names
        assert "age" in property_names

    def test_parse_struct(self):
        """Test parsing a Swift struct."""
        parser = TreeSitterSwiftParser()
        content = """
struct Point {
    var x: Double
    var y: Double
}
"""
        result = parser.parse(content, "test.swift")
        assert result is not None

        structs = [d for d in result.declarations if d.kind == "struct"]
        assert len(structs) == 1
        assert structs[0].name == "Point"

    def test_parse_enum_with_cases(self):
        """Test parsing enum with individual cases extracted."""
        parser = TreeSitterSwiftParser()
        content = """
enum Direction {
    case north
    case south
    case east
    case west
}
"""
        result = parser.parse(content, "test.swift")
        assert result is not None

        enums = [d for d in result.declarations if d.kind == "enum"]
        assert len(enums) == 1
        assert enums[0].name == "Direction"

        # Test enum case extraction
        cases = [d for d in result.declarations if d.kind == "enum_case"]
        assert len(cases) == 4
        case_names = {c.name for c in cases}
        assert case_names == {"north", "south", "east", "west"}

    def test_parse_protocol(self):
        """Test parsing a Swift protocol."""
        parser = TreeSitterSwiftParser()
        content = """
protocol Drawable {
    func draw()
}
"""
        result = parser.parse(content, "test.swift")
        assert result is not None

        protocols = [d for d in result.declarations if d.kind == "protocol"]
        assert len(protocols) == 1
        assert protocols[0].name == "Drawable"

    def test_parse_imports(self):
        """Test parsing import statements."""
        parser = TreeSitterSwiftParser()
        content = """
import Foundation
import UIKit
import SwiftUI

func main() {}
"""
        result = parser.parse(content, "test.swift")
        assert result is not None
        assert len(result.imports) >= 3

        import_names = result.imports
        assert "Foundation" in import_names
        assert "UIKit" in import_names
        assert "SwiftUI" in import_names

    def test_property_with_state_wrapper(self):
        """Test parsing property with @State property wrapper."""
        parser = TreeSitterSwiftParser()
        content = """
struct CounterView: View {
    @State private var count = 0

    var body: some View {
        Text("Count: \\(count)")
    }
}
"""
        result = parser.parse(content, "test.swift")
        assert result is not None

        properties = [d for d in result.declarations if d.kind == "property"]
        count_prop = next((p for p in properties if p.name == "count"), None)
        assert count_prop is not None
        assert "@State" in count_prop.modifiers

    def test_property_with_published_wrapper(self):
        """Test parsing property with @Published property wrapper."""
        parser = TreeSitterSwiftParser()
        content = """
class ViewModel: ObservableObject {
    @Published var username: String = ""
    @Published var isLoggedIn: Bool = false
}
"""
        result = parser.parse(content, "test.swift")
        assert result is not None

        properties = [d for d in result.declarations if d.kind == "property"]
        assert len(properties) >= 2

        username_prop = next((p for p in properties if p.name == "username"), None)
        assert username_prop is not None
        assert "@Published" in username_prop.modifiers

        isLoggedIn_prop = next((p for p in properties if p.name == "isLoggedIn"), None)
        assert isLoggedIn_prop is not None
        assert "@Published" in isLoggedIn_prop.modifiers

    def test_function_with_mainactor_attribute(self):
        """Test parsing function with @MainActor attribute."""
        parser = TreeSitterSwiftParser()
        content = """
@MainActor
func updateUI() {
    print("Updating UI on main thread")
}
"""
        result = parser.parse(content, "test.swift")
        assert result is not None

        functions = [d for d in result.declarations if d.kind == "function"]
        assert len(functions) == 1
        assert "@MainActor" in functions[0].modifiers

    def test_class_with_mainactor_attribute(self):
        """Test parsing class with @MainActor attribute."""
        parser = TreeSitterSwiftParser()
        content = """
@MainActor
class ViewController {
    func viewDidLoad() {
        print("View loaded")
    }
}
"""
        result = parser.parse(content, "test.swift")
        assert result is not None

        classes = [d for d in result.declarations if d.kind == "class"]
        assert len(classes) == 1
        assert "@MainActor" in classes[0].modifiers

    def test_function_signature_with_generics(self):
        """Test that function signatures preserve generic constraints."""
        parser = TreeSitterSwiftParser()
        content = """
func swap<T>(_ a: inout T, _ b: inout T) {
    let temp = a
    a = b
    b = temp
}
"""
        result = parser.parse(content, "test.swift")
        assert result is not None

        functions = [d for d in result.declarations if d.kind == "function"]
        assert len(functions) == 1
        assert functions[0].name == "swap"
        # Signature should contain generic parameter <T>
        assert "<T>" in functions[0].signature

    def test_function_signature_with_where_clause(self):
        """Test that function signatures preserve where clauses."""
        parser = TreeSitterSwiftParser()
        content = """
func findIndex<T>(of valueToFind: T, in array: [T]) -> Int? where T: Equatable {
    for (index, value) in array.enumerated() {
        if value == valueToFind {
            return index
        }
    }
    return nil
}
"""
        result = parser.parse(content, "test.swift")
        assert result is not None

        functions = [d for d in result.declarations if d.kind == "function"]
        assert len(functions) == 1
        assert functions[0].name == "findIndex"
        # Signature should contain where clause
        assert "where" in functions[0].signature
        assert "Equatable" in functions[0].signature

    def test_async_function_modifier(self):
        """Test parsing async function with async modifier."""
        parser = TreeSitterSwiftParser()
        content = """
func fetchData() async -> Data {
    // Async implementation
    return Data()
}
"""
        result = parser.parse(content, "test.swift")
        assert result is not None

        functions = [d for d in result.declarations if d.kind == "function"]
        assert len(functions) == 1
        assert "async" in functions[0].modifiers

    def test_throws_function_modifier(self):
        """Test parsing function with throws modifier."""
        parser = TreeSitterSwiftParser()
        content = """
func riskyOperation() throws -> String {
    throw NSError(domain: "", code: 0)
}
"""
        result = parser.parse(content, "test.swift")
        assert result is not None

        functions = [d for d in result.declarations if d.kind == "function"]
        assert len(functions) == 1
        assert "throws" in functions[0].modifiers

    def test_async_throws_function_modifiers(self):
        """Test parsing function with both async and throws modifiers."""
        parser = TreeSitterSwiftParser()
        content = """
func fetchUserData() async throws -> User {
    // Async throwing implementation
    return User()
}
"""
        result = parser.parse(content, "test.swift")
        assert result is not None

        functions = [d for d in result.declarations if d.kind == "function"]
        assert len(functions) == 1
        assert "async" in functions[0].modifiers
        assert "throws" in functions[0].modifiers

    def test_doc_comment_line_style(self):
        """Test parsing line-style documentation comments (///)."""
        parser = TreeSitterSwiftParser()
        content = """
/// Calculates the sum of two integers.
/// - Parameters:
///   - a: The first integer
///   - b: The second integer
/// - Returns: The sum of a and b
func add(_ a: Int, _ b: Int) -> Int {
    return a + b
}
"""
        result = parser.parse(content, "test.swift")
        assert result is not None

        functions = [d for d in result.declarations if d.kind == "function"]
        assert len(functions) == 1
        assert functions[0].docstring != ""
        # Docstring should contain documentation content
        assert "Calculates the sum" in functions[0].docstring or "sum" in functions[0].docstring

    def test_doc_comment_block_style(self):
        """Test parsing block-style documentation comments (/** */)."""
        parser = TreeSitterSwiftParser()
        content = """
/**
 * A simple class representing a person.
 *
 * This class stores basic information about a person.
 */
class Person {
    var name: String = ""
}
"""
        result = parser.parse(content, "test.swift")
        assert result is not None

        classes = [d for d in result.declarations if d.kind == "class"]
        assert len(classes) == 1
        assert classes[0].docstring != ""
        # Docstring should contain documentation content
        assert "person" in classes[0].docstring.lower()

    def test_typealias_declaration(self):
        """Test parsing typealias declarations."""
        parser = TreeSitterSwiftParser()
        content = """
typealias Coordinate = (x: Double, y: Double)
"""
        result = parser.parse(content, "test.swift")
        assert result is not None

        typealiases = [d for d in result.declarations if d.kind == "typealias"]
        assert len(typealiases) == 1
        assert typealiases[0].name == "Coordinate"

    def test_access_modifiers(self):
        """Test parsing various access modifiers."""
        parser = TreeSitterSwiftParser()
        content = """
public class PublicClass {}
private class PrivateClass {}
internal func internalFunc() {}
fileprivate var fileprivateVar = 0
open class OpenClass {}
"""
        result = parser.parse(content, "test.swift")
        assert result is not None

        classes = [d for d in result.declarations if d.kind == "class"]
        assert len(classes) >= 3

        public_class = next((c for c in classes if c.name == "PublicClass"), None)
        assert public_class is not None
        assert "public" in public_class.modifiers

        private_class = next((c for c in classes if c.name == "PrivateClass"), None)
        assert private_class is not None
        assert "private" in private_class.modifiers

        open_class = next((c for c in classes if c.name == "OpenClass"), None)
        assert open_class is not None
        assert "open" in open_class.modifiers

    def test_static_modifier(self):
        """Test parsing static modifier on properties and functions."""
        parser = TreeSitterSwiftParser()
        content = """
struct Math {
    static let pi = 3.14159

    static func abs(_ value: Double) -> Double {
        return value < 0 ? -value : value
    }
}
"""
        result = parser.parse(content, "test.swift")
        assert result is not None

        properties = [d for d in result.declarations if d.kind == "property"]
        pi_prop = next((p for p in properties if p.name == "pi"), None)
        assert pi_prop is not None
        assert "static" in pi_prop.modifiers

        functions = [d for d in result.declarations if d.kind == "function"]
        abs_func = next((f for f in functions if f.name == "abs"), None)
        assert abs_func is not None
        assert "static" in abs_func.modifiers

    def test_multiple_attributes_on_property(self):
        """Test parsing property with multiple attributes."""
        parser = TreeSitterSwiftParser()
        content = """
struct ContentView: View {
    @State @MainActor private var isLoading = false
}
"""
        result = parser.parse(content, "test.swift")
        assert result is not None

        properties = [d for d in result.declarations if d.kind == "property"]
        loading_prop = next((p for p in properties if p.name == "isLoading"), None)
        assert loading_prop is not None
        # Should have both @State and @MainActor attributes
        assert any("@State" in str(m) for m in loading_prop.modifiers)
        assert any("@MainActor" in str(m) for m in loading_prop.modifiers)

    def test_initializer_declaration(self):
        """Test parsing initializer (init) declarations."""
        parser = TreeSitterSwiftParser()
        content = """
class Rectangle {
    var width: Double
    var height: Double

    init(width: Double, height: Double) {
        self.width = width
        self.height = height
    }
}
"""
        result = parser.parse(content, "test.swift")
        assert result is not None

        initializers = [d for d in result.declarations if d.kind == "initializer"]
        assert len(initializers) == 1
        assert initializers[0].name == "init"

    def test_actor_declaration(self):
        """Test parsing Swift actor declaration (concurrency)."""
        parser = TreeSitterSwiftParser()
        content = """
actor BankAccount {
    var balance: Double = 0.0

    func deposit(_ amount: Double) {
        balance += amount
    }
}
"""
        result = parser.parse(content, "test.swift")
        assert result is not None

        actors = [d for d in result.declarations if d.kind == "actor"]
        assert len(actors) == 1
        assert actors[0].name == "BankAccount"

    def test_extension_declaration(self):
        """Test parsing extension declarations."""
        parser = TreeSitterSwiftParser()
        content = """
extension String {
    func reversed() -> String {
        return String(self.reversed())
    }
}
"""
        result = parser.parse(content, "test.swift")
        assert result is not None

        extensions = [d for d in result.declarations if d.kind == "extension"]
        assert len(extensions) == 1
        assert extensions[0].name == "String"

    def test_associatedtype_in_protocol(self):
        """Test parsing associatedtype declarations in protocols."""
        parser = TreeSitterSwiftParser()
        content = """
protocol Container {
    associatedtype Item
    func append(_ item: Item)
}
"""
        result = parser.parse(content, "test.swift")
        assert result is not None

        associatedtypes = [d for d in result.declarations if d.kind == "associatedtype"]
        assert len(associatedtypes) == 1
        assert associatedtypes[0].name == "Item"

    def test_computed_property(self):
        """Test parsing computed properties."""
        parser = TreeSitterSwiftParser()
        content = """
struct Circle {
    var radius: Double

    var area: Double {
        return 3.14159 * radius * radius
    }
}
"""
        result = parser.parse(content, "test.swift")
        assert result is not None

        properties = [d for d in result.declarations if d.kind == "property"]
        area_prop = next((p for p in properties if p.name == "area"), None)
        assert area_prop is not None
        # Computed property should have "computed" modifier
        assert "computed" in area_prop.modifiers

    def test_multiple_enum_cases_on_single_line(self):
        """Test parsing multiple enum cases declared on a single line."""
        parser = TreeSitterSwiftParser()
        content = """
enum Status {
    case pending, active, completed
}
"""
        result = parser.parse(content, "test.swift")
        assert result is not None

        # Should extract individual enum cases
        cases = [d for d in result.declarations if d.kind == "enum_case"]
        # All three cases should be extracted
        assert len(cases) >= 3
