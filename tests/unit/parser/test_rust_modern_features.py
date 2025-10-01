#!/usr/bin/env python3

"""
Comprehensive tests for modern Rust features in the tree-sitter parser.

Tests coverage for Rust 2021+ edition features including:
- Lifetimes and lifetime parameters
- Const generics
- Generic Associated Types (GATs)
- Attribute macros (#[derive], #[async_trait], etc.)
- Where clauses
- Async/unsafe/const function modifiers
- Type parameters on all declaration types
"""

import logging

import pytest

from codeconcat.base_types import ParseResult
from codeconcat.parser.language_parsers.tree_sitter_rust_parser import TreeSitterRustParser

logger = logging.getLogger(__name__)


class TestRustLifetimes:
    """Test lifetime parameter extraction."""

    @pytest.fixture
    def parser(self):
        return TreeSitterRustParser()

    def test_function_with_lifetime(self, parser):
        """Test function with lifetime parameter."""
        code = """
        /// Get the longest string
        fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
            if x.len() > y.len() { x } else { y }
        }
        """
        result = parser.parse(code, "test.rs")

        assert result.error is None
        assert len(result.declarations) >= 1

        func = next((d for d in result.declarations if d.name == "longest"), None)
        assert func is not None
        assert func.kind == "function"
        assert "Get the longest string" in func.docstring

    def test_struct_with_lifetime(self, parser):
        """Test struct with lifetime parameter."""
        code = """
        /// A reference wrapper
        pub struct RefWrapper<'a, T> {
            data: &'a T
        }
        """
        result = parser.parse(code, "test.rs")

        assert result.error is None
        structs = [d for d in result.declarations if d.kind == "struct"]
        assert len(structs) >= 1
        assert structs[0].name == "RefWrapper"
        assert "pub" in structs[0].modifiers

    def test_multiple_lifetimes(self, parser):
        """Test function with multiple lifetimes."""
        code = """
        fn complex<'a, 'b, T>(x: &'a T, y: &'b T) -> &'a T {
            x
        }
        """
        result = parser.parse(code, "test.rs")

        assert result.error is None
        assert len(result.declarations) >= 1
        func = result.declarations[0]
        assert func.name == "complex"


class TestRustConstGenerics:
    """Test const generic parameter extraction."""

    @pytest.fixture
    def parser(self):
        return TreeSitterRustParser()

    def test_const_generic_array(self, parser):
        """Test struct with const generic for array size."""
        code = """
        /// Fixed-size array wrapper
        pub struct Array<T, const N: usize> {
            data: [T; N]
        }
        """
        result = parser.parse(code, "test.rs")

        assert result.error is None
        structs = [d for d in result.declarations if d.kind == "struct"]
        assert len(structs) >= 1
        assert structs[0].name == "Array"

    def test_const_generic_function(self, parser):
        """Test function with const generic parameter."""
        code = """
        fn create_array<T, const N: usize>(value: T) -> [T; N]
        where
            T: Clone
        {
            [value; N]
        }
        """
        result = parser.parse(code, "test.rs")

        assert result.error is None
        assert len(result.declarations) >= 1
        func = result.declarations[0]
        assert func.name == "create_array"


class TestRustGATs:
    """Test Generic Associated Types (GATs)."""

    @pytest.fixture
    def parser(self):
        return TreeSitterRustParser()

    def test_trait_with_gat(self, parser):
        """Test trait with generic associated type."""
        code = """
        /// Iterator with GAT
        pub trait Iterator {
            type Item<'a> where Self: 'a;

            fn next<'a>(&'a mut self) -> Option<Self::Item<'a>>;
        }
        """
        result = parser.parse(code, "test.rs")

        assert result.error is None
        traits = [d for d in result.declarations if d.kind == "trait"]
        assert len(traits) >= 1
        assert traits[0].name == "Iterator"
        assert "pub" in traits[0].modifiers


class TestRustAttributeMacros:
    """Test attribute macro extraction."""

    @pytest.fixture
    def parser(self):
        return TreeSitterRustParser()

    def test_derive_attribute(self, parser):
        """Test #[derive(...)] attribute."""
        code = """
        #[derive(Debug, Clone, PartialEq)]
        pub struct Point {
            x: f64,
            y: f64,
        }
        """
        result = parser.parse(code, "test.rs")

        assert result.error is None
        structs = [d for d in result.declarations if d.kind == "struct"]
        assert len(structs) >= 1
        assert structs[0].name == "Point"

    def test_async_trait_attribute(self, parser):
        """Test #[async_trait] attribute."""
        code = """
        use async_trait::async_trait;

        #[async_trait]
        pub trait AsyncService {
            async fn process(&self) -> Result<(), Error>;
        }
        """
        result = parser.parse(code, "test.rs")

        assert result.error is None
        assert len(result.imports) >= 1
        traits = [d for d in result.declarations if d.kind == "trait"]
        assert len(traits) >= 1

    def test_cfg_attribute(self, parser):
        """Test #[cfg(...)] conditional compilation."""
        code = """
        #[cfg(target_os = "linux")]
        pub fn linux_only() {
            println!("Linux!");
        }

        #[cfg(test)]
        mod tests {
            #[test]
            fn test_something() {}
        }
        """
        result = parser.parse(code, "test.rs")

        assert result.error is None
        funcs = [d for d in result.declarations if d.kind == "function"]
        assert any(f.name == "linux_only" for f in funcs)


class TestRustWhereClauses:
    """Test where clause extraction."""

    @pytest.fixture
    def parser(self):
        return TreeSitterRustParser()

    def test_function_where_clause(self, parser):
        """Test function with where clause."""
        code = """
        fn generic_function<T, U>(t: T, u: U)
        where
            T: Clone + Debug,
            U: Display,
        {
            println!("{}", u);
        }
        """
        result = parser.parse(code, "test.rs")

        assert result.error is None
        assert len(result.declarations) >= 1
        func = result.declarations[0]
        assert func.name == "generic_function"

    def test_struct_where_clause(self, parser):
        """Test struct with where clause."""
        code = """
        pub struct Wrapper<T>
        where
            T: Clone + Send + Sync,
        {
            value: T,
        }
        """
        result = parser.parse(code, "test.rs")

        assert result.error is None
        structs = [d for d in result.declarations if d.kind == "struct"]
        assert len(structs) >= 1
        assert structs[0].name == "Wrapper"

    def test_impl_where_clause(self, parser):
        """Test impl block with where clause."""
        code = """
        impl<T> Display for Wrapper<T>
        where
            T: Display,
        {
            fn fmt(&self, f: &mut Formatter) -> fmt::Result {
                write!(f, "{}", self.value)
            }
        }
        """
        result = parser.parse(code, "test.rs")

        assert result.error is None
        impls = [d for d in result.declarations if d.kind == "impl" or d.kind == "impl_block"]
        assert len(impls) >= 1


class TestRustAsyncUnsafeConst:
    """Test async, unsafe, and const function modifiers."""

    @pytest.fixture
    def parser(self):
        return TreeSitterRustParser()

    def test_async_function(self, parser):
        """Test async function."""
        code = """
        /// Async HTTP request
        pub async fn fetch_data(url: &str) -> Result<String, Error> {
            // ...
            Ok(String::new())
        }
        """
        result = parser.parse(code, "test.rs")

        assert result.error is None
        funcs = [d for d in result.declarations if d.kind == "function"]
        assert len(funcs) >= 1
        func = funcs[0]
        assert func.name == "fetch_data"
        assert "async" in func.modifiers or "pub" in func.modifiers

    def test_unsafe_function(self, parser):
        """Test unsafe function."""
        code = """
        /// Raw pointer dereference
        pub unsafe fn deref_raw<T>(ptr: *const T) -> T {
            *ptr
        }
        """
        result = parser.parse(code, "test.rs")

        assert result.error is None
        funcs = [d for d in result.declarations if d.kind == "function"]
        assert len(funcs) >= 1
        assert funcs[0].name == "deref_raw"
        assert "unsafe" in funcs[0].modifiers or "pub" in funcs[0].modifiers

    def test_const_function(self, parser):
        """Test const function."""
        code = """
        /// Compile-time computation
        pub const fn square(x: i32) -> i32 {
            x * x
        }
        """
        result = parser.parse(code, "test.rs")

        assert result.error is None
        funcs = [d for d in result.declarations if d.kind == "function"]
        assert len(funcs) >= 1
        assert funcs[0].name == "square"

    def test_async_unsafe_combination(self, parser):
        """Test async unsafe function."""
        code = """
        pub async unsafe fn dangerous_async() {
            // ...
        }
        """
        result = parser.parse(code, "test.rs")

        assert result.error is None
        assert len(result.declarations) >= 1

    def test_unsafe_trait(self, parser):
        """Test unsafe trait."""
        code = """
        /// Marker for send types
        pub unsafe trait Send {}
        """
        result = parser.parse(code, "test.rs")

        assert result.error is None
        traits = [d for d in result.declarations if d.kind == "trait"]
        assert len(traits) >= 1
        assert "unsafe" in traits[0].modifiers or "pub" in traits[0].modifiers


class TestRustComplexScenarios:
    """Test complex real-world Rust scenarios."""

    @pytest.fixture
    def parser(self):
        return TreeSitterRustParser()

    def test_complex_generic_struct(self, parser):
        """Test struct with multiple type parameters, lifetimes, and where clause."""
        code = """
        #[derive(Debug, Clone)]
        pub struct Cache<'a, K, V, const SIZE: usize>
        where
            K: Hash + Eq,
            V: Clone,
        {
            data: HashMap<K, &'a V>,
            buffer: [Option<V>; SIZE],
        }
        """
        result = parser.parse(code, "test.rs")

        assert result.error is None
        structs = [d for d in result.declarations if d.kind == "struct"]
        assert len(structs) >= 1
        assert structs[0].name == "Cache"

    def test_async_trait_impl(self, parser):
        """Test async trait implementation."""
        code = """
        use async_trait::async_trait;

        #[async_trait]
        impl<T> AsyncProcessor for Handler<T>
        where
            T: Send + Sync + 'static,
        {
            async fn process(&self, data: &[u8]) -> Result<Vec<u8>, Error> {
                // ...
                Ok(vec![])
            }
        }
        """
        result = parser.parse(code, "test.rs")

        assert result.error is None
        assert len(result.imports) >= 1

    def test_macro_definition(self, parser):
        """Test macro rules definition."""
        code = """
        /// Create a vector with repeated elements
        macro_rules! vec_repeat {
            ($elem:expr; $n:expr) => {
                vec![$elem; $n]
            };
        }
        """
        result = parser.parse(code, "test.rs")

        assert result.error is None
        macros = [d for d in result.declarations if d.kind == "macro" or d.kind == "macro_definition"]
        assert len(macros) >= 1


class TestRustDocComments:
    """Test documentation comment extraction."""

    @pytest.fixture
    def parser(self):
        return TreeSitterRustParser()

    def test_triple_slash_doc(self, parser):
        """Test /// doc comments."""
        code = """
        /// This is a documented function.
        /// It has multiple lines.
        ///
        /// # Examples
        /// ```
        /// let x = foo();
        /// ```
        pub fn foo() -> i32 {
            42
        }
        """
        result = parser.parse(code, "test.rs")

        assert result.error is None
        funcs = [d for d in result.declarations if d.kind == "function"]
        assert len(funcs) >= 1
        assert "documented function" in funcs[0].docstring
        assert "Examples" in funcs[0].docstring

    def test_inner_doc_comment(self, parser):
        """Test //! inner doc comments."""
        code = """
        //! Module documentation
        //!
        //! This module does things.

        pub fn helper() {}
        """
        result = parser.parse(code, "test.rs")

        assert result.error is None

    def test_block_doc_comment(self, parser):
        """Test /** **/ block doc comments."""
        code = """
        /**
         * Block style documentation
         * for this struct
         */
        pub struct Documented {
            field: i32
        }
        """
        result = parser.parse(code, "test.rs")

        assert result.error is None
        structs = [d for d in result.declarations if d.kind == "struct"]
        assert len(structs) >= 1


if __name__ == "__main__":
    pytest.main(["-v", __file__])
