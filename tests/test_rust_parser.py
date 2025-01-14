"""Tests for Rust parser."""

import pytest
from codeconcat.parser.language_parsers.rust_parser import parse_rust


def test_parse_rust_function():
    """Test parsing Rust functions."""
    code = """
fn hello() {
    println!("Hello, World!");
}

pub fn add(x: i32, y: i32) -> i32 {
    x + y
}

async fn fetch_data() -> Result<String, Error> {
    Ok(String::from("data"))
}
"""
    result = parse_rust("test.rs", code)
    assert result is not None
    assert len(result.declarations) == 3
    
    hello = next(d for d in result.declarations if d.name == "hello")
    assert hello.kind == "function"
    assert hello.start_line == 2
    
    add = next(d for d in result.declarations if d.name == "add")
    assert add.kind == "function"
    assert add.start_line == 6
    
    fetch = next(d for d in result.declarations if d.name == "fetch_data")
    assert fetch.kind == "function"
    assert fetch.start_line == 10


def test_parse_rust_struct():
    """Test parsing Rust structs."""
    code = """
pub struct Person {
    name: String,
    age: u32,
}

struct Point<T> {
    x: T,
    y: T,
}
"""
    result = parse_rust("test.rs", code)
    assert result is not None
    assert len(result.declarations) == 2
    
    person = next(d for d in result.declarations if d.name == "Person")
    assert person.kind == "struct"
    assert person.start_line == 2
    
    point = next(d for d in result.declarations if d.name == "Point")
    assert point.kind == "struct"
    assert point.start_line == 7


def test_parse_rust_enum():
    """Test parsing Rust enums."""
    code = """
pub enum Option<T> {
    Some(T),
    None,
}

enum Result<T, E> {
    Ok(T),
    Err(E),
}
"""
    result = parse_rust("test.rs", code)
    assert result is not None
    assert len(result.declarations) == 2
    
    option = next(d for d in result.declarations if d.name == "Option")
    assert option.kind == "enum"
    assert option.start_line == 2
    
    result_enum = next(d for d in result.declarations if d.name == "Result")
    assert result_enum.kind == "enum"
    assert result_enum.start_line == 7


def test_parse_rust_trait():
    """Test parsing Rust traits."""
    code = """
pub trait Display {
    fn fmt(&self) -> String;
}

trait Debug {
    fn debug(&self) -> String;
    fn default() -> Self;
}
"""
    result = parse_rust("test.rs", code)
    assert result is not None
    assert len(result.declarations) == 2
    
    display = next(d for d in result.declarations if d.name == "Display")
    assert display.kind == "trait"
    assert display.start_line == 2
    
    debug = next(d for d in result.declarations if d.name == "Debug")
    assert debug.kind == "trait"
    assert debug.start_line == 6


def test_parse_rust_impl():
    """Test parsing Rust implementations."""
    code = """
impl Person {
    fn new(name: String, age: u32) -> Self {
        Person { name, age }
    }
}

impl<T> Point<T> {
    fn origin() -> Self {
        Point { x: T::default(), y: T::default() }
    }
}
"""
    result = parse_rust("test.rs", code)
    assert result is not None
    assert len(result.declarations) == 4
    
    person_impl = next(d for d in result.declarations if d.name == "Person")
    assert person_impl.kind == "impl"
    assert person_impl.start_line == 2
    
    new_fn = next(d for d in result.declarations if d.name == "new")
    assert new_fn.kind == "function"
    assert new_fn.start_line == 3
    
    point_impl = next(d for d in result.declarations if d.name == "Point")
    assert point_impl.kind == "impl"
    assert point_impl.start_line == 8
    
    origin_fn = next(d for d in result.declarations if d.name == "origin")
    assert origin_fn.kind == "function"
    assert origin_fn.start_line == 9


def test_parse_rust_empty():
    """Test parsing empty Rust file."""
    result = parse_rust("test.rs", "")
    assert result is not None
    assert len(result.declarations) == 0


def test_parse_rust_invalid():
    """Test parsing invalid Rust code."""
    code = """
this is not valid rust code
"""
    result = parse_rust("test.rs", code)
    assert result is not None
    assert len(result.declarations) == 0


def test_parse_rust_doc_comments():
    """Test parsing Rust doc comments."""
    code = """
/// A person in the system
/// with multiple lines of docs
pub struct Person {
    /// The person's name
    name: String,
    /// The person's age
    age: u32,
}

//! Module-level documentation
//! describing the purpose

/** A point in 2D space
 * with coordinates
 */
struct Point {
    x: f64,
    y: f64,
}
"""
    result = parse_rust("test.rs", code)
    assert result is not None
    assert len(result.declarations) == 2
    
    person = next(d for d in result.declarations if d.name == "Person")
    assert person.kind == "struct"
    assert person.docstring == "/// A person in the system\n/// with multiple lines of docs"
    
    point = next(d for d in result.declarations if d.name == "Point")
    assert point.kind == "struct"
    assert point.docstring == "/** A point in 2D space\n * with coordinates\n */"


def test_parse_rust_attributes():
    """Test parsing Rust attributes."""
    code = """
#[derive(Debug, Clone)]
#[repr(C)]
pub struct Data {
    value: i32,
}

#[cfg(test)]
mod tests {
    #[test]
    fn it_works() {
        assert_eq!(2 + 2, 4);
    }
}

#[cfg_attr(feature = "serde",
    derive(Serialize, Deserialize)
)]
struct Config {
    setting: String,
}
"""
    result = parse_rust("test.rs", code)
    assert result is not None
    assert len(result.declarations) == 5
    
    data = next(d for d in result.declarations if d.name == "Data")
    assert data.kind == "struct"
    assert "#[derive(Debug, Clone)]" in data.modifiers
    assert "#[repr(C)]" in data.modifiers
    
    tests = next(d for d in result.declarations if d.name == "tests")
    assert tests.kind == "mod"
    assert "#[cfg(test)]" in tests.modifiers
    
    config = next(d for d in result.declarations if d.name == "Config")
    assert config.kind == "struct"
    assert any("cfg_attr" in m for m in config.modifiers)


def test_parse_rust_complex_impl():
    """Test parsing complex Rust impl blocks."""
    code = """
impl<T> Iterator for MyIter<T> {
    type Item = T;
    
    fn next(&mut self) -> Option<Self::Item> {
        None
    }
}

impl<T: Display> fmt::Debug for Point<T> {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "Point({}, {})", self.x, self.y)
    }
}

impl dyn AsyncRead + Send {
    fn poll_read(&mut self) -> Poll<()> {
        Poll::Ready(())
    }
}
"""
    result = parse_rust("test.rs", code)
    assert result is not None
    assert len(result.declarations) == 6
    
    iter_impl = next(d for d in result.declarations if "Iterator for MyIter" in d.name)
    assert iter_impl.kind == "impl"
    assert iter_impl.start_line == 2
    
    debug_impl = next(d for d in result.declarations if "Debug for Point" in d.name)
    assert debug_impl.kind == "impl"
    
    async_impl = next(d for d in result.declarations if "AsyncRead + Send" in d.name)
    assert async_impl.kind == "impl"


def test_parse_rust_unit_structs():
    """Test parsing Rust unit and tuple structs."""
    code = """
pub struct Unit;

struct Tuple(String, i32);

struct Empty {}

pub(crate) struct Visibility;

struct Generic<T>(T);
"""
    result = parse_rust("test.rs", code)
    assert result is not None
    assert len(result.declarations) == 5
    
    unit = next(d for d in result.declarations if d.name == "Unit")
    assert unit.kind == "struct"
    assert "pub" in unit.modifiers
    
    tuple = next(d for d in result.declarations if d.name == "Tuple")
    assert tuple.kind == "struct"
    
    visibility = next(d for d in result.declarations if d.name == "Visibility")
    assert visibility.kind == "struct"
    assert "pub(crate)" in visibility.modifiers


def test_parse_rust_trait_functions():
    """Test parsing Rust trait function declarations."""
    code = """
pub trait Service {
    fn call(&self) -> Result<(), Error>;
    
    fn default() -> Self {
        unimplemented!()
    }
    
    async fn process(&mut self);
}

trait Handler {
    const TIMEOUT: u64 = 30;
    type Error;
    fn handle(&self) -> Result<(), Self::Error>;
}
"""
    result = parse_rust("test.rs", code)
    assert result is not None
    assert len(result.declarations) == 2
    
    service = next(d for d in result.declarations if d.name == "Service")
    assert service.kind == "trait"
    assert "pub" in service.modifiers
    
    handler = next(d for d in result.declarations if d.name == "Handler")
    assert handler.kind == "trait"
