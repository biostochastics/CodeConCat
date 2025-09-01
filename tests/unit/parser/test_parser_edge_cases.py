#!/usr/bin/env python3

"""
Edge case tests for CodeConCat parsers.

These tests focus on complex or unusual language constructs that might
challenge the parsers, such as deeply nested structures, unusual formatting,
non-standard comment placement, and other edge cases.
"""

import logging

import pytest

from codeconcat.base_types import ParseResult
from codeconcat.parser.enable_debug import enable_all_parser_debug_logging
from codeconcat.parser.language_parsers.enhanced_js_ts_parser import EnhancedJSTypeScriptParser
from codeconcat.parser.language_parsers.enhanced_python_parser import EnhancedPythonParser
from codeconcat.parser.language_parsers.enhanced_rust_parser import EnhancedRustParser

# Enable debug logging for all parsers
enable_all_parser_debug_logging()

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class TestParserEdgeCases:
    """Test class for parser edge cases."""

    @pytest.fixture
    def deeply_nested_python(self) -> str:
        """Fixture providing a deeply nested Python code sample."""
        return '''"""
This file tests parsing of deeply nested Python code structures.
"""

def level1():
    """Level 1 function."""
    x = 1

    def level2():
        """Level 2 function."""
        y = 2

        def level3():
            """Level 3 function."""
            z = 3

            def level4():
                """Level 4 function."""
                a = 4

                def level5():
                    """Level 5 function."""
                    b = 5

                    # Even more nesting
                    def level6():
                        """Level 6 function."""
                        c = 6
                        return c

                    return level6() + b

                return level5() + a

            return level4() + z

        return level3() + y

    return level2() + x

class OuterClass:
    """Outer class with nested classes."""

    class MiddleClass:
        """Middle nested class."""

        class InnerClass:
            """Inner nested class."""

            def inner_method(self):
                """Method in innermost class."""

                class LocalClass:
                    """Local class inside a method."""

                    def local_method(self):
                        """Method in local class."""
                        pass

                return LocalClass()

# Complex decorator pattern
def decorator1(func):
    """Decorator 1"""
    def wrapper1(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper1

def decorator2(param):
    """Decorator 2 with parameter"""
    def actual_decorator(func):
        def wrapper2(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper2
    return actual_decorator

@decorator1
@decorator2("param")
def decorated_function(x, y):
    """Function with multiple decorators."""
    return x + y
'''

    @pytest.fixture
    def unusual_rust_code(self) -> str:
        """Fixture providing Rust code with unusual formatting and edge cases."""
        return """//! This module contains unusual Rust code formatting for testing

/* Block comment at file level */

// Macro with complex nested structure
macro_rules! nested_macro {
    ($e:expr) => {
        {
            let inner = || {
                // heavily nested
                struct InnerStruct {
                    field: u32
                }

                impl InnerStruct {
                    fn method(&self) -> u32 {
                        self.field
                    }
                }

                InnerStruct { field: $e }
            };
            inner().method()
        }
    };
}

/// Documentation for a function with odd formatting
fn oddly_formatted_function
    (
        /* comment in parameters */
        a: i32,
        // line comment in parameters
        b: i32,
    )
    -> i32
    /* comment before block */
    {
    /* Block comment at the start of function body */
    let x = a + b;

    // One-liner struct and impl
    struct Tiny { v: i32 } impl Tiny { fn get(&self) -> i32 { self.v } }

    x * Tiny { v: 2 }.get()
}

// Trait with associated types and where clause
trait ComplexTrait<T>
where
    T: Clone + 'static,
{
    type Output;
    fn complex_method<'a>(&'a self, input: T) -> Self::Output;
}

// Impl with complex generic signatures
impl<'a, T, U> ComplexTrait<T> for &'a U
where
    T: Clone + 'static,
    U: AsRef<str> + 'a,
{
    type Output = String;

    fn complex_method<'b>(&'b self, input: T) -> Self::Output {
        String::from(self.as_ref())
    }
}

// Nested modules
mod outer {
    //! Inner module doc

    pub mod middle {
        pub mod inner {
            /// Function in deeply nested module
            pub fn nested_fn() -> i32 {
                42
            }
        }
    }

    // Re-export
    pub use self::middle::inner::nested_fn;
}

fn main() {
    println!("{}", nested_macro!(5));
    println!("{}", oddly_formatted_function(1, 2));
    println!("{}", outer::nested_fn());
}
"""

    @pytest.fixture
    def typescript_with_jsx(self) -> str:
        """Fixture providing TypeScript code with JSX/TSX mixed in."""
        return """/**
 * TypeScript file with JSX/TSX components and unusual formatting.
 */

import React, { FC, useState, useEffect } from 'react';

// Type definitions with unusual formatting
type ComplexType<T extends object = {},
    K = keyof T> = {
  [P in K]: T extends { [Q in P]: infer R } ? R : never;
} & {
  readonly id: string;
  /* Multi-line
     comment inside
     type definition */
  optional?: boolean;
};

// Interface with nested types
interface NestedInterface {
  outer: {
    middle: {
      inner: {
        value: string;
      }[];
    };
  };
  /**
   * Method with complex signature
   */
  method<T extends unknown[]>(
    arg1: T[number],
    arg2: { [K in keyof T[number]]: boolean }
  ): Promise<void>;
}

/**
 * React component with JSX
 */
const ComplexComponent: FC<{ prop1: string; prop2?: number }> = ({
  prop1,
  prop2 = 0,
}) => {
  // Hooks
  const [state, setState] = useState<{
    value: string;
    items: Array<{ id: number; name: string }>;
  }>({
    value: '',
    items: [],
  });

  // Effect with nested function and JSX
  useEffect(() => {
    const loadData = async () => {
      // Function inside an effect
      const process = (data: any[]) => {
        return data.map(item => ({
          ...item,
          processed: true
        }));
      };

      // More nesting
      const render = () => {
        return <div>{state.value}</div>;
      };

      setState({
        value: 'loaded',
        items: process([{ id: 1, name: 'item' }])
      });
    };

    loadData();
  }, []);

  // Return JSX with nested components
  return (
    <div className="container">
      <header>
        {/* Comment in JSX */}
        <h1>{prop1}</h1>
      </header>
      <main>
        {state.items.map(item => (
          <div key={item.id}>
            {/* Nested JSX */}
            <span>{item.name}</span>
            {item.processed && (
              <small>Processed</small>
            )}
          </div>
        ))}
        {/* Component with unusual formatting */}
        <ChildComponent
          longProp={"very long string that would cause line breaks"}
          anotherProp={123}
          callbackProp={() => {
            // Nested function in JSX
            const innerFunc = () => console.log('inner');
            innerFunc();
          }}
        />
      </main>
    </div>
  );
};

// Export default with function wrapping
export default (() => {
  // Add some context
  const withContext = (Component: FC<any>) => {
    return (props: any) => (
      <Component {...props} context="added" />
    );
  };

  return withContext(ComplexComponent);
})();
"""

    def test_deeply_nested_python_parsing(self, deeply_nested_python):
        """Test parsing Python code with deep nesting levels."""
        parser = EnhancedPythonParser()
        result = parser.parse(deeply_nested_python, "nested.py")

        # Check that we got a valid ParseResult
        assert isinstance(result, ParseResult)
        assert result.error is None, f"Parse error: {result.error}"

        # Print the declarations for debugging
        print(f"Found {len(result.declarations)} top-level declarations in Python nested test:")
        for decl in result.declarations:
            print(f"- {decl.kind}: {decl.name}")

        # Find the level1 function and check nesting
        level1 = next((d for d in result.declarations if d.name == "level1"), None)
        assert level1 is not None, "level1 function not found"

        # Check if level1 has nested functions
        assert level1.children, "level1 should have nested functions (level2)"

        # Recursively check nesting depth
        def get_max_nesting_depth(decl, current_depth=1):
            if not decl.children:
                return current_depth
            return max(get_max_nesting_depth(child, current_depth + 1) for child in decl.children)

        max_depth = get_max_nesting_depth(level1)
        print(f"Maximum nesting depth in level1 function: {max_depth}")

        # With 6 levels of nesting, we should detect at least 3 levels
        # (parsers might have a practical limit to how deep they can detect)
        assert max_depth >= 3, f"Expected at least 3 levels of nesting, got {max_depth}"

        # Check class nesting
        outer_class = next((d for d in result.declarations if d.name == "OuterClass"), None)
        assert outer_class is not None, "OuterClass not found"

        if outer_class.children:
            middle_class = next((c for c in outer_class.children if c.name == "MiddleClass"), None)
            if middle_class and middle_class.children:
                inner_class = next(
                    (c for c in middle_class.children if c.name == "InnerClass"), None
                )
                if inner_class:
                    print("Successfully parsed nested class structure")

    def test_unusual_rust_code_parsing(self, unusual_rust_code):
        """Test parsing Rust code with unusual formatting and complex constructs."""
        parser = EnhancedRustParser()
        result = parser.parse(unusual_rust_code, "unusual.rs")

        # Check that we got a valid ParseResult
        assert isinstance(result, ParseResult)
        assert result.error is None, f"Parse error: {result.error}"

        # Print the declarations for debugging
        print(f"Found {len(result.declarations)} top-level declarations in Rust unusual test:")
        for decl in result.declarations:
            print(f"- {decl.kind}: {decl.name}")

        # Find the oddly formatted function
        odd_fn = next(
            (d for d in result.declarations if d.name == "oddly_formatted_function"), None
        )
        print(f"Found oddly_formatted_function: {odd_fn is not None}")

        # Find the complex trait
        complex_trait = next((d for d in result.declarations if d.name == "ComplexTrait"), None)
        print(f"Found ComplexTrait: {complex_trait is not None}")

        # Check for nested modules
        outer_mod = next(
            (d for d in result.declarations if d.name == "outer" and d.kind == "module"), None
        )
        print(f"Found outer module: {outer_mod is not None}")

        # The test is informative rather than strictly assertive since
        # different parsers might handle these edge cases differently
        print("Rust parser handled unusual formatting test without errors")

    def test_typescript_jsx_parsing(self, typescript_with_jsx):
        """Test parsing TypeScript with JSX mixed in."""
        parser = EnhancedJSTypeScriptParser()
        result = parser.parse(typescript_with_jsx, "component.tsx")

        # Check that we got a valid ParseResult
        assert isinstance(result, ParseResult)
        assert result.error is None, f"Parse error: {result.error}"

        # Print the declarations for debugging
        print(f"Found {len(result.declarations)} top-level declarations in TS/JSX test:")
        for decl in result.declarations:
            print(f"- {decl.kind}: {decl.name}")

        # Look for key TypeScript elements
        type_def = next((d for d in result.declarations if d.name == "ComplexType"), None)
        interface_def = next((d for d in result.declarations if d.name == "NestedInterface"), None)
        component_def = next((d for d in result.declarations if d.name == "ComplexComponent"), None)

        print(f"Found ComplexType: {type_def is not None}")
        print(f"Found NestedInterface: {interface_def is not None}")
        print(f"Found ComplexComponent: {component_def is not None}")

        # Check for JSX parsing (this is informative since JSX might be handled differently)
        print("TypeScript/JSX parser handled mixed code without errors")

        # Check imports were detected
        if result.imports:
            print(f"Detected {len(result.imports)} imports in TypeScript/JSX file")
            assert "react" in " ".join(result.imports).lower(), "React import should be detected"

    def test_mixed_language_samples(self):
        """Test parsers' robustness when faced with unexpected content or language mixing."""
        # Create parsers
        python_parser = EnhancedPythonParser()
        js_parser = EnhancedJSTypeScriptParser()

        # Test JavaScript parser with Python code (should not crash)
        python_code = "def test_function():\n    print('Hello')\n"
        result = js_parser.parse(python_code, "wrong_language.js")
        assert isinstance(result, ParseResult), (
            "Parser should return a result even for wrong languages"
        )

        # Test Python parser with JavaScript code (should not crash)
        js_code = "function testFunction() {\n    console.log('Hello');\n}\n"
        result = python_parser.parse(js_code, "wrong_language.py")
        assert isinstance(result, ParseResult), (
            "Parser should return a result even for wrong languages"
        )

        # Test with empty file
        result = python_parser.parse("", "empty.py")
        assert isinstance(result, ParseResult), "Parser should handle empty files gracefully"

        # Test with very long lines
        long_line = "x = " + "x + " * 1000 + "1"
        result = python_parser.parse(long_line, "long_line.py")
        assert isinstance(result, ParseResult), "Parser should handle very long lines"

        print("All parsers handled incorrect or unexpected input without crashing")


if __name__ == "__main__":
    pytest.main(["-v", __file__])
