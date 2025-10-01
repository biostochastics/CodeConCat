"""Tests for the Tree-sitter Kotlin parser."""

from codeconcat.parser.language_parsers.tree_sitter_kotlin_parser import (
    TreeSitterKotlinParser,
)


class TestTreeSitterKotlinParser:
    """Test suite for TreeSitterKotlinParser."""

    def test_parser_initialization(self):
        """Test that the parser initializes correctly."""
        parser = TreeSitterKotlinParser()
        assert parser is not None
        assert parser.language_name == "kotlin"
        assert parser.ts_language is not None
        assert parser.parser is not None

    def test_parse_simple_function(self):
        """Test parsing a simple Kotlin function."""
        parser = TreeSitterKotlinParser()
        content = """
fun greet(name: String): String {
    return "Hello, $name!"
}
"""
        result = parser.parse(content, "test.kt")
        assert result is not None
        assert len(result.declarations) >= 1
        functions = [d for d in result.declarations if d.kind == "function"]
        assert len(functions) == 1
        assert functions[0].name == "greet"

    def test_parse_simple_class(self):
        """Test parsing a simple Kotlin class."""
        parser = TreeSitterKotlinParser()
        content = """
class Person(val name: String, var age: Int) {
    fun birthday() {
        age++
    }
}
"""
        result = parser.parse(content, "test.kt")
        assert result is not None

        classes = [d for d in result.declarations if d.kind == "class"]
        assert len(classes) == 1
        assert classes[0].name == "Person"

        functions = [d for d in result.declarations if d.kind == "function"]
        assert len(functions) >= 1
        assert any(f.name == "birthday" for f in functions)

    def test_parse_imports(self):
        """Test parsing import statements."""
        parser = TreeSitterKotlinParser()
        content = """
import kotlin.collections.List
import java.util.*
import com.example.MyClass

fun main() {}
"""
        result = parser.parse(content, "test.kt")
        assert result is not None
        assert len(result.imports) >= 1

        # result.imports contains strings, not objects
        import_paths = result.imports
        assert any("kotlin.collections" in imp for imp in import_paths)

    def test_parse_property(self):
        """Test parsing top-level property declarations."""
        parser = TreeSitterKotlinParser()
        content = """
val PI = 3.14159
var count = 0

fun increment() {
    count++
}
"""
        result = parser.parse(content, "test.kt")
        assert result is not None

        properties = [d for d in result.declarations if d.kind == "property"]
        assert len(properties) >= 1
        property_names = {p.name for p in properties}
        assert "PI" in property_names or "count" in property_names

    def test_parse_object_declaration(self):
        """Test parsing Kotlin object declarations (singletons)."""
        parser = TreeSitterKotlinParser()
        content = """
object DatabaseConnection {
    val url = "jdbc:mysql://localhost:3306/db"

    fun connect() {
        println("Connecting...")
    }
}
"""
        result = parser.parse(content, "test.kt")
        assert result is not None

        objects = [d for d in result.declarations if d.kind == "object"]
        assert len(objects) == 1
        assert objects[0].name == "DatabaseConnection"

    # ========== COMPREHENSIVE TESTS ==========

    def test_parse_multiple_functions_with_parameters(self):
        """Test parsing multiple functions with various parameter types."""
        parser = TreeSitterKotlinParser()
        content = """
fun add(a: Int, b: Int): Int = a + b

fun processString(text: String, count: Int = 1): String {
    return text.repeat(count)
}

fun <T> identity(value: T): T = value
"""
        result = parser.parse(content, "test.kt")
        assert result is not None

        functions = [d for d in result.declarations if d.kind == "function"]
        assert len(functions) >= 3
        function_names = {f.name for f in functions}
        assert "add" in function_names
        assert "processString" in function_names
        assert "identity" in function_names

    def test_parse_class_with_inheritance(self):
        """Test parsing classes with inheritance and interfaces."""
        parser = TreeSitterKotlinParser()
        content = """
interface Drawable {
    fun draw()
}

abstract class Shape : Drawable {
    abstract val area: Double
}

class Circle(val radius: Double) : Shape() {
    override val area: Double
        get() = Math.PI * radius * radius

    override fun draw() {
        println("Drawing circle")
    }
}
"""
        result = parser.parse(content, "test.kt")
        assert result is not None

        classes = [d for d in result.declarations if d.kind == "class"]
        assert len(classes) >= 2
        class_names = {c.name for c in classes}
        assert "Shape" in class_names
        assert "Circle" in class_names

    def test_parse_data_class(self):
        """Test parsing data classes."""
        parser = TreeSitterKotlinParser()
        content = """
data class User(
    val id: Long,
    val name: String,
    val email: String
)

data class Point(val x: Int, val y: Int)
"""
        result = parser.parse(content, "test.kt")
        assert result is not None

        classes = [d for d in result.declarations if d.kind == "class"]
        assert len(classes) >= 2
        class_names = {c.name for c in classes}
        assert "User" in class_names
        assert "Point" in class_names

    def test_parse_sealed_class(self):
        """Test parsing sealed classes."""
        parser = TreeSitterKotlinParser()
        content = """
sealed class Result {
    data class Success(val data: String) : Result()
    data class Error(val message: String) : Result()
    object Loading : Result()
}
"""
        result = parser.parse(content, "test.kt")
        assert result is not None

        classes = [d for d in result.declarations if d.kind == "class"]
        assert len(classes) >= 1
        # At least Result class should be found
        assert any(c.name == "Result" for c in classes)

    def test_parse_suspend_function(self):
        """Test parsing suspend functions (coroutines)."""
        parser = TreeSitterKotlinParser()
        content = """
suspend fun fetchData(): String {
    delay(1000)
    return "data"
}

suspend fun <T> retry(times: Int, block: suspend () -> T): T {
    repeat(times - 1) {
        try {
            return block()
        } catch (e: Exception) {
            // Continue
        }
    }
    return block()
}
"""
        result = parser.parse(content, "test.kt")
        assert result is not None

        functions = [d for d in result.declarations if d.kind == "function"]
        assert len(functions) >= 2
        function_names = {f.name for f in functions}
        assert "fetchData" in function_names
        assert "retry" in function_names

    def test_parse_extension_function(self):
        """Test parsing extension functions."""
        parser = TreeSitterKotlinParser()
        content = """
fun String.isPalindrome(): Boolean {
    return this == this.reversed()
}

fun <T> List<T>.secondOrNull(): T? {
    return if (this.size >= 2) this[1] else null
}

fun Int.square() = this * this
"""
        result = parser.parse(content, "test.kt")
        assert result is not None

        functions = [d for d in result.declarations if d.kind == "function"]
        assert len(functions) >= 3
        function_names = {f.name for f in functions}
        assert "isPalindrome" in function_names
        assert "secondOrNull" in function_names
        assert "square" in function_names

    def test_parse_companion_object(self):
        """Test parsing companion objects."""
        parser = TreeSitterKotlinParser()
        content = """
class Factory {
    companion object {
        const val VERSION = "1.0"

        fun create(): Factory {
            return Factory()
        }
    }
}
"""
        result = parser.parse(content, "test.kt")
        assert result is not None

        classes = [d for d in result.declarations if d.kind == "class"]
        assert len(classes) >= 1
        assert any(c.name == "Factory" for c in classes)

    def test_parse_enum_class(self):
        """Test parsing enum classes."""
        parser = TreeSitterKotlinParser()
        content = """
enum class Color(val rgb: Int) {
    RED(0xFF0000),
    GREEN(0x00FF00),
    BLUE(0x0000FF)
}

enum class Direction {
    NORTH, SOUTH, EAST, WEST
}
"""
        result = parser.parse(content, "test.kt")
        assert result is not None

        classes = [d for d in result.declarations if d.kind == "class"]
        assert len(classes) >= 2
        class_names = {c.name for c in classes}
        assert "Color" in class_names
        assert "Direction" in class_names

    def test_parse_value_class(self):
        """Test parsing value classes (inline classes)."""
        parser = TreeSitterKotlinParser()
        content = """
@JvmInline
value class Password(private val s: String)

@JvmInline
value class UserId(val id: Long)
"""
        result = parser.parse(content, "test.kt")
        assert result is not None

        classes = [d for d in result.declarations if d.kind == "class"]
        assert len(classes) >= 2
        class_names = {c.name for c in classes}
        assert "Password" in class_names
        assert "UserId" in class_names

    def test_parse_nested_classes(self):
        """Test parsing nested and inner classes."""
        parser = TreeSitterKotlinParser()
        content = """
class Outer {
    class Nested {
        fun nestedMethod() {}
    }

    inner class Inner {
        fun innerMethod() {}
    }
}
"""
        result = parser.parse(content, "test.kt")
        assert result is not None

        classes = [d for d in result.declarations if d.kind == "class"]
        assert len(classes) >= 1
        # Outer class should be found
        assert any(c.name == "Outer" for c in classes)

    def test_parse_unicode_identifiers(self):
        """Test parsing Unicode identifiers."""
        parser = TreeSitterKotlinParser()
        content = """
val 数字 = 42
val αβγ = "Greek"

fun 函数(参数: String): String {
    return "Unicode: $参数"
}

class Класс {
    fun метод() {}
}
"""
        result = parser.parse(content, "test.kt")
        assert result is not None

        # Should parse without errors
        properties = [d for d in result.declarations if d.kind == "property"]
        functions = [d for d in result.declarations if d.kind == "function"]
        classes = [d for d in result.declarations if d.kind == "class"]

        # Should find at least some declarations (Unicode support varies by grammar)
        assert len(properties) + len(functions) + len(classes) > 0

    def test_parse_empty_file(self):
        """Test parsing an empty file."""
        parser = TreeSitterKotlinParser()
        content = ""
        result = parser.parse(content, "empty.kt")
        assert result is not None
        assert len(result.declarations) == 0
        assert len(result.imports) == 0

    def test_parse_comment_only_file(self):
        """Test parsing a file with only comments."""
        parser = TreeSitterKotlinParser()
        content = """
// This is a comment
/* This is a block comment */
/**
 * This is a KDoc comment
 */
"""
        result = parser.parse(content, "comments.kt")
        assert result is not None
        assert len(result.declarations) == 0
        assert len(result.imports) == 0

    def test_parse_whitespace_only(self):
        """Test parsing a file with only whitespace."""
        parser = TreeSitterKotlinParser()
        content = "   \n\n  \t\n   "
        result = parser.parse(content, "whitespace.kt")
        assert result is not None
        assert len(result.declarations) == 0

    def test_parse_malformed_syntax_missing_brace(self):
        """Test parsing code with missing closing brace."""
        parser = TreeSitterKotlinParser()
        content = """
fun broken() {
    println("Missing closing brace")
"""
        # Parser should not crash
        result = parser.parse(content, "malformed.kt")
        assert result is not None
        # May or may not find the function depending on error recovery

    def test_parse_malformed_syntax_invalid_token(self):
        """Test parsing code with invalid tokens."""
        parser = TreeSitterKotlinParser()
        content = """
fun valid() {}

@@@ invalid syntax @@@

fun alsoValid() {}
"""
        # Parser should not crash
        result = parser.parse(content, "malformed2.kt")
        assert result is not None
        # Should still find at least one valid function
        functions = [d for d in result.declarations if d.kind == "function"]
        assert len(functions) >= 1

    def test_parse_mixed_declarations(self):
        """Test parsing a file with mixed declaration types."""
        parser = TreeSitterKotlinParser()
        content = """
package com.example

import kotlin.math.*

const val MAX_SIZE = 100

interface Repository {
    suspend fun fetch(): List<String>
}

data class Item(val id: Int, val name: String)

object Cache {
    private val map = mutableMapOf<Int, Item>()

    fun put(item: Item) {
        map[item.id] = item
    }
}

fun processItems(items: List<Item>): Int {
    return items.size
}

fun List<Item>.filterById(id: Int) = filter { it.id == id }
"""
        result = parser.parse(content, "mixed.kt")
        assert result is not None

        # Should find multiple declaration types
        functions = [d for d in result.declarations if d.kind == "function"]
        classes = [d for d in result.declarations if d.kind == "class"]
        objects = [d for d in result.declarations if d.kind == "object"]
        properties = [d for d in result.declarations if d.kind == "property"]

        assert len(functions) >= 2
        assert len(classes) >= 1
        assert len(objects) >= 1
        # Properties might not all be captured, but should have some declarations
        assert len(result.declarations) >= 4

    def test_parse_lambda_and_higher_order_functions(self):
        """Test parsing lambdas and higher-order functions."""
        parser = TreeSitterKotlinParser()
        content = """
fun <T, R> List<T>.myMap(transform: (T) -> R): List<R> {
    return this.map(transform)
}

val doubler: (Int) -> Int = { it * 2 }

fun runWithCallback(callback: () -> Unit) {
    callback()
}
"""
        result = parser.parse(content, "lambdas.kt")
        assert result is not None

        functions = [d for d in result.declarations if d.kind == "function"]
        assert len(functions) >= 2

    def test_parse_generics(self):
        """Test parsing generic types and functions."""
        parser = TreeSitterKotlinParser()
        content = """
class Box<T>(val value: T)

interface Container<out T> {
    fun get(): T
}

fun <T : Comparable<T>> max(a: T, b: T): T {
    return if (a > b) a else b
}
"""
        result = parser.parse(content, "generics.kt")
        assert result is not None

        classes = [d for d in result.declarations if d.kind == "class"]
        functions = [d for d in result.declarations if d.kind == "function"]

        assert len(classes) >= 1
        assert len(functions) >= 1

    def test_parse_annotations(self):
        """Test parsing annotated declarations."""
        parser = TreeSitterKotlinParser()
        content = """
@Deprecated("Use newFunction instead")
fun oldFunction() {}

@Target(AnnotationTarget.CLASS)
@Retention(AnnotationRetention.RUNTIME)
annotation class MyAnnotation

@MyAnnotation
class AnnotatedClass
"""
        result = parser.parse(content, "annotations.kt")
        assert result is not None

        functions = [d for d in result.declarations if d.kind == "function"]
        classes = [d for d in result.declarations if d.kind == "class"]

        assert len(functions) >= 1
        assert len(classes) >= 1

    def test_parse_delegation(self):
        """Test parsing class delegation."""
        parser = TreeSitterKotlinParser()
        content = """
interface Base {
    fun print()
}

class BaseImpl : Base {
    override fun print() { println("Base") }
}

class Derived(b: Base) : Base by b
"""
        result = parser.parse(content, "delegation.kt")
        assert result is not None

        classes = [d for d in result.declarations if d.kind == "class"]
        assert len(classes) >= 2
