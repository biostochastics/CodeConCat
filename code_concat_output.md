# CodeConCat Output

# AI-Friendly Code Summary

This document contains a structured representation of a codebase, organized for AI analysis.

## Repository Structure
```
Total code files: 54
Documentation files: 0

File types:
- py: 54 files
```

## Code Organization
The code is organized into sections, each prefixed with clear markers:
- Directory markers show file organization
- File headers contain metadata and imports
- Annotations provide context about code purpose
- Documentation sections contain project documentation

## Navigation
- Each file begins with '---FILE:' followed by its path
- Each section is clearly delimited with markdown headers
- Code blocks are formatted with appropriate language tags

## Content Summary

---
Begin code content below:
## Directory Structure
```
└── .
    ├── setup.py
    ├── app.py
    ├── tests
    │   ├── test_version.py
    │   ├── conftest.py
    │   ├── test_rust_parser.py
    │   ├── test_cpp_parser.py
    │   ├── test_go_parser.py
    │   ├── __init__.py
    │   ├── test_julia_parser.py
    │   ├── test_content_processor.py
    │   ├── test_js_ts_parser.py
    │   ├── test_codeconcat.py
    │   ├── test_python_parser.py
    │   ├── test_php_parser.py
    │   ├── test_java_parser.py
    │   ├── test_annotator.py
    │   └── test_r_parser.py
    └── codeconcat
        ├── version.py
        ├── __init__.py
        ├── base_types.py
        ├── main.py
        ├── config
        │   ├── config_loader.py
        │   └── __init__.py
        ├── transformer
        │   ├── __init__.py
        │   └── annotator.py
        ├── processor
        │   ├── security_types.py
        │   ├── content_processor.py
        │   ├── token_counter.py
        │   ├── __init__.py
        │   └── security_processor.py
        ├── collector
        │   ├── github_collector.py
        │   ├── __init__.py
        │   └── local_collector.py
        ├── parser
        │   ├── doc_extractor.py
        │   ├── file_parser.py
        │   ├── __init__.py
        │   └── language_parsers
        │       ├── csharp_parser.py
        │       ├── c_parser.py
        │       ├── julia_parser.py
        │       ├── __init__.py
        │       ├── php_parser.py
        │       ├── rust_parser.py
        │       ├── js_ts_parser.py
        │       ├── python_parser.py
        │       ├── base_parser.py
        │       ├── java_parser.py
        │       ├── cpp_parser.py
        │       ├── r_parser.py
        │       └── go_parser.py
        └── writer
            ├── markdown_writer.py
            ├── __init__.py
            ├── xml_writer.py
            ├── ai_context.py
            └── json_writer.py
```

## Code Files

### File: ./setup.py
#### Summary
```
File: setup.py
Language: python
```

```python
   1 | import os
   2 | import re
   3 | from setuptools import setup, find_packages
   6 | def get_version():
   8 |     Extracts the CodeConCat version from codeconcat/version.py
  10 |     version_file = os.path.join(os.path.dirname(__file__), "codeconcat", "version.py")
  11 |     with open(version_file, "r", encoding="utf-8") as f:
  12 |         content = f.read()
  13 |         match = re.search(r'__version__\s*=\s*"([^"]+)"', content)
  14 |         if match:
  15 |             return match.group(1)
  16 |     return "0.0.0"
  19 | def get_long_description():
  20 |     try:
  21 |         with open("README.md", "r", encoding="utf-8") as f:
  22 |             return f.read()
  23 |     except FileNotFoundError:
  24 |         return ""
  27 | extras_require = {
  28 |     "web": [
  29 |         "fastapi>=0.68.0",
  30 |         "uvicorn>=0.15.0",
  31 |         "pydantic>=1.8.0",
  32 |     ],
  33 |     "test": [
  34 |         "pytest>=7.4.0",
  35 |         "pytest-cov>=4.1.0",
  36 |         "pytest-asyncio>=0.21.1",
  37 |         "pytest-mock>=3.11.1",
  38 |     ],
  39 |     "all": [
  40 |         "fastapi>=0.68.0",
  41 |         "uvicorn>=0.15.0",
  42 |         "pydantic>=1.8.0",
  43 |         "pytest>=7.4.0",
  44 |         "pytest-cov>=4.1.0",
  45 |         "pytest-asyncio>=0.21.1",
  46 |         "pytest-mock>=3.11.1",
  47 |     ],
  48 | }
  50 | setup(
  51 |     name="codeconcat",
  52 |     version=get_version(),
  53 |     author="Sergey Kornilov",
  54 |     author_email="sergey.kornilov@biostochastics.com",
  55 |     description="An LLM-friendly code parser, aggregator and doc extractor",
  56 |     long_description=get_long_description(),
  57 |     long_description_content_type="text/markdown",
  58 |     packages=find_packages(),
  59 |     install_requires=[
  60 |         "pyyaml>=5.0",
  61 |         "pyperclip>=1.8.0",
  62 |     ],
  63 |     extras_require=extras_require,
  64 |     python_requires=">=3.8",
  65 |     entry_points={"console_scripts": ["codeconcat=codeconcat.main:cli_entry_point"]},
  66 |     classifiers=[
  67 |         "Development Status :: 3 - Alpha",
  68 |         "Intended Audience :: Developers",
  69 |         "Programming Language :: Python :: 3",
  70 |         "Programming Language :: Python :: 3.8",
  71 |         "Programming Language :: Python :: 3.9",
  72 |         "Programming Language :: Python :: 3.10",
  73 |         "Programming Language :: Python :: 3.11",
  74 |         "Operating System :: OS Independent",
  75 |     ],
  76 |     keywords="llm code parser documentation",
  77 |     project_urls={
  78 |         "Source": "https://github.com/biostochastics/codeconcat",
  79 |     },
  80 | )
```

---
### File: ./app.py
#### Summary
```
File: app.py
Language: python
```

```python
   1 | from fastapi import FastAPI, HTTPException
   2 | from pydantic import BaseModel
   3 | from typing import Optional, List
   4 | from codeconcat import run_codeconcat_in_memory, CodeConCatConfig
   6 | app = FastAPI(
   7 |     title="CodeConCat API",
   8 |     description="API for CodeConCat - An LLM-friendly code parser, aggregator and doc extractor",
   9 |     version="1.0.0",
  10 | )
  13 | class CodeConcatRequest(BaseModel):
  14 |     target_path: str
  15 |     format: str = "markdown"
  16 |     github_url: Optional[str] = None
  17 |     github_token: Optional[str] = None
  18 |     github_ref: Optional[str] = None
  19 |     extract_docs: bool = False
  20 |     merge_docs: bool = False
  21 |     include_paths: List[str] = []
  22 |     exclude_paths: List[str] = []
  23 |     include_languages: List[str] = []
  24 |     exclude_languages: List[str] = []
  25 |     disable_tree: bool = False
  26 |     disable_annotations: bool = False
  27 |     disable_copy: bool = True  # Default to True for API usage
  28 |     disable_symbols: bool = False
  29 |     disable_ai_context: bool = False
  30 |     max_workers: int = 4
  33 | @app.post("/concat")
  34 | async def concat_code(request: CodeConcatRequest):
  36 |     Process code files and return concatenated output
  38 |     try:
  39 |         config = CodeConCatConfig(
  40 |             target_path=request.target_path,
  41 |             format=request.format,
  42 |             github_url=request.github_url,
  43 |             github_token=request.github_token,
  44 |             github_ref=request.github_ref,
  45 |             extract_docs=request.extract_docs,
  46 |             merge_docs=request.merge_docs,
  47 |             include_paths=request.include_paths,
  48 |             exclude_paths=request.exclude_paths,
  49 |             include_languages=request.include_languages,
  50 |             exclude_languages=request.exclude_languages,
  51 |             disable_tree=request.disable_tree,
  52 |             disable_annotations=request.disable_annotations,
  53 |             disable_copy=request.disable_copy,
  54 |             disable_symbols=request.disable_symbols,
  55 |             disable_ai_context=request.disable_ai_context,
  56 |             max_workers=request.max_workers,
  57 |         )
  58 |         output = run_codeconcat_in_memory(config)
  59 |         return {"output": output}
  60 |     except Exception as e:
  61 |         raise HTTPException(status_code=500, detail=str(e))
  64 | @app.get("/")
  65 | async def root():
  67 |     Root endpoint returning basic API info
  69 |     return {
  70 |         "name": "CodeConCat API",
  71 |         "version": "1.0.0",
  72 |         "description": "API for code concatenation and documentation extraction",
  73 |     }
```

---
### File: ./tests/test_version.py
#### Summary
```
File: test_version.py
Language: python
```

```python
   1 | import re
   2 | from codeconcat.version import __version__
   5 | def test_version_format():
   7 |     pattern = r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?(?:\+[0-9A-Za-z-]+)?$"
   8 |     assert re.match(pattern, __version__) is not None
```

---
### File: ./tests/conftest.py
#### Summary
```
File: conftest.py
Language: python
```

```python
   1 | import pytest
   4 | @pytest.fixture
   5 | def sample_code():
   6 |     return """
   7 | def hello_world():
   8 |     return "Hello, World!"
```

---
### File: ./tests/test_rust_parser.py
#### Summary
```
File: test_rust_parser.py
Language: python
```

```python
   3 | import pytest
   4 | from codeconcat.parser.language_parsers.rust_parser import parse_rust
   7 | def test_parse_rust_function():
   9 |     code = """
  10 | fn hello() {
  11 |     println!("Hello, World!");
  12 | }
  14 | pub fn add(x: i32, y: i32) -> i32 {
  15 |     x + y
  16 | }
  18 | async fn fetch_data() -> Result<String, Error> {
  19 |     Ok(String::from("data"))
  20 | }
  22 |     result = parse_rust("test.rs", code)
  23 |     assert result is not None
  24 |     assert len(result.declarations) == 3
  26 |     hello = next(d for d in result.declarations if d.name == "hello")
  27 |     assert hello.kind == "function"
  28 |     assert hello.start_line == 2
  30 |     add = next(d for d in result.declarations if d.name == "add")
  31 |     assert add.kind == "function"
  32 |     assert add.start_line == 6
  34 |     fetch = next(d for d in result.declarations if d.name == "fetch_data")
  35 |     assert fetch.kind == "function"
  36 |     assert fetch.start_line == 10
  39 | def test_parse_rust_struct():
  41 |     code = """
  42 | pub struct Person {
  43 |     name: String,
  44 |     age: u32,
  45 | }
  47 | struct Point<T> {
  48 |     x: T,
  49 |     y: T,
  50 | }
  52 |     result = parse_rust("test.rs", code)
  53 |     assert result is not None
  54 |     assert len(result.declarations) == 2
  56 |     person = next(d for d in result.declarations if d.name == "Person")
  57 |     assert person.kind == "struct"
  58 |     assert person.start_line == 2
  60 |     point = next(d for d in result.declarations if d.name == "Point")
  61 |     assert point.kind == "struct"
  62 |     assert point.start_line == 7
  65 | def test_parse_rust_enum():
  67 |     code = """
  68 | pub enum Option<T> {
  69 |     Some(T),
  70 |     None,
  71 | }
  73 | enum Result<T, E> {
  74 |     Ok(T),
  75 |     Err(E),
  76 | }
  78 |     result = parse_rust("test.rs", code)
  79 |     assert result is not None
  80 |     assert len(result.declarations) == 2
  82 |     option = next(d for d in result.declarations if d.name == "Option")
  83 |     assert option.kind == "enum"
  84 |     assert option.start_line == 2
  86 |     result_enum = next(d for d in result.declarations if d.name == "Result")
  87 |     assert result_enum.kind == "enum"
  88 |     assert result_enum.start_line == 7
  91 | def test_parse_rust_trait():
  93 |     code = """
  94 | pub trait Display {
  95 |     fn fmt(&self) -> String;
  96 | }
  98 | trait Debug {
  99 |     fn debug(&self) -> String;
 100 |     fn default() -> Self;
 101 | }
 103 |     result = parse_rust("test.rs", code)
 104 |     assert result is not None
 105 |     assert len(result.declarations) == 2
 107 |     display = next(d for d in result.declarations if d.name == "Display")
 108 |     assert display.kind == "trait"
 109 |     assert display.start_line == 2
 111 |     debug = next(d for d in result.declarations if d.name == "Debug")
 112 |     assert debug.kind == "trait"
 113 |     assert debug.start_line == 6
 116 | def test_parse_rust_impl():
 118 |     code = """
 119 | impl Person {
 120 |     fn new(name: String, age: u32) -> Self {
 121 |         Person { name, age }
 122 |     }
 123 | }
 125 | impl<T> Point<T> {
 126 |     fn origin() -> Self {
 127 |         Point { x: T::default(), y: T::default() }
 128 |     }
 129 | }
 131 |     result = parse_rust("test.rs", code)
 132 |     assert result is not None
 133 |     assert len(result.declarations) == 4
 135 |     person_impl = next(d for d in result.declarations if d.name == "Person")
 136 |     assert person_impl.kind == "impl"
 137 |     assert person_impl.start_line == 2
 139 |     new_fn = next(d for d in result.declarations if d.name == "new")
 140 |     assert new_fn.kind == "function"
 141 |     assert new_fn.start_line == 3
 143 |     point_impl = next(d for d in result.declarations if d.name == "Point")
 144 |     assert point_impl.kind == "impl"
 145 |     assert point_impl.start_line == 8
 147 |     origin_fn = next(d for d in result.declarations if d.name == "origin")
 148 |     assert origin_fn.kind == "function"
 149 |     assert origin_fn.start_line == 9
 152 | def test_parse_rust_empty():
 154 |     result = parse_rust("test.rs", "")
 155 |     assert result is not None
 156 |     assert len(result.declarations) == 0
 159 | def test_parse_rust_invalid():
 161 |     code = """
 162 | this is not valid rust code
 164 |     result = parse_rust("test.rs", code)
 165 |     assert result is not None
 166 |     assert len(result.declarations) == 0
 169 | def test_parse_rust_doc_comments():
 171 |     code = """
 174 | pub struct Person {
 176 |     name: String,
 178 |     age: u32,
 179 | }
 187 | struct Point {
 188 |     x: f64,
 189 |     y: f64,
 190 | }
 192 |     result = parse_rust("test.rs", code)
 193 |     assert result is not None
 194 |     assert len(result.declarations) == 2
 196 |     person = next(d for d in result.declarations if d.name == "Person")
 197 |     assert person.kind == "struct"
 198 |     assert person.docstring == "/// A person in the system\n/// with multiple lines of docs"
 200 |     point = next(d for d in result.declarations if d.name == "Point")
 201 |     assert point.kind == "struct"
 202 |     assert point.docstring == "/** A point in 2D space\n * with coordinates\n */"
 205 | def test_parse_rust_attributes():
 207 |     code = """
 210 | pub struct Data {
 211 |     value: i32,
 212 | }
 215 | mod tests {
 217 |     fn it_works() {
 218 |         assert_eq!(2 + 2, 4);
 219 |     }
 220 | }
 223 |     derive(Serialize, Deserialize)
 224 | )]
 225 | struct Config {
 226 |     setting: String,
 227 | }
 229 |     result = parse_rust("test.rs", code)
 230 |     assert result is not None
 231 |     assert len(result.declarations) == 5
 233 |     data = next(d for d in result.declarations if d.name == "Data")
 234 |     assert data.kind == "struct"
 235 |     assert "#[derive(Debug, Clone)]" in data.modifiers
 236 |     assert "#[repr(C)]" in data.modifiers
 238 |     tests = next(d for d in result.declarations if d.name == "tests")
 239 |     assert tests.kind == "mod"
 240 |     assert "#[cfg(test)]" in tests.modifiers
 242 |     config = next(d for d in result.declarations if d.name == "Config")
 243 |     assert config.kind == "struct"
 244 |     assert any("cfg_attr" in m for m in config.modifiers)
 247 | def test_parse_rust_complex_impl():
 249 |     code = """
 250 | impl<T> Iterator for MyIter<T> {
 251 |     type Item = T;
 253 |     fn next(&mut self) -> Option<Self::Item> {
 254 |         None
 255 |     }
 256 | }
 258 | impl<T: Display> fmt::Debug for Point<T> {
 259 |     fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
 260 |         write!(f, "Point({}, {})", self.x, self.y)
 261 |     }
 262 | }
 264 | impl dyn AsyncRead + Send {
 265 |     fn poll_read(&mut self) -> Poll<()> {
 266 |         Poll::Ready(())
 267 |     }
 268 | }
 270 |     result = parse_rust("test.rs", code)
 271 |     assert result is not None
 272 |     assert len(result.declarations) == 6
 274 |     iter_impl = next(d for d in result.declarations if "Iterator for MyIter" in d.name)
 275 |     assert iter_impl.kind == "impl"
 276 |     assert iter_impl.start_line == 2
 278 |     debug_impl = next(d for d in result.declarations if "Debug for Point" in d.name)
 279 |     assert debug_impl.kind == "impl"
 281 |     async_impl = next(d for d in result.declarations if "AsyncRead + Send" in d.name)
 282 |     assert async_impl.kind == "impl"
 285 | def test_parse_rust_unit_structs():
 287 |     code = """
 288 | pub struct Unit;
 290 | struct Tuple(String, i32);
 292 | struct Empty {}
 294 | pub(crate) struct Visibility;
 296 | struct Generic<T>(T);
 298 |     result = parse_rust("test.rs", code)
 299 |     assert result is not None
 300 |     assert len(result.declarations) == 5
 302 |     unit = next(d for d in result.declarations if d.name == "Unit")
 303 |     assert unit.kind == "struct"
 304 |     assert "pub" in unit.modifiers
 306 |     tuple = next(d for d in result.declarations if d.name == "Tuple")
 307 |     assert tuple.kind == "struct"
 309 |     visibility = next(d for d in result.declarations if d.name == "Visibility")
 310 |     assert visibility.kind == "struct"
 311 |     assert "pub(crate)" in visibility.modifiers
 314 | def test_parse_rust_trait_functions():
 316 |     code = """
 317 | pub trait Service {
 318 |     fn call(&self) -> Result<(), Error>;
 320 |     fn default() -> Self {
 321 |         unimplemented!()
 322 |     }
 324 |     async fn process(&mut self);
 325 | }
 327 | trait Handler {
 328 |     const TIMEOUT: u64 = 30;
 329 |     type Error;
 330 |     fn handle(&self) -> Result<(), Self::Error>;
 331 | }
 333 |     result = parse_rust("test.rs", code)
 334 |     assert result is not None
 335 |     assert len(result.declarations) == 2
 337 |     service = next(d for d in result.declarations if d.name == "Service")
 338 |     assert service.kind == "trait"
 339 |     assert "pub" in service.modifiers
 341 |     handler = next(d for d in result.declarations if d.name == "Handler")
 342 |     assert handler.kind == "trait"
```

---
### File: ./tests/test_cpp_parser.py
#### Summary
```
File: test_cpp_parser.py
Language: python
```

```python
   3 | import unittest
   4 | from codeconcat.parser.language_parsers.cpp_parser import CppParser
   7 | class TestCppParser(unittest.TestCase):
   8 |     def setUp(self):
   9 |         self.parser = CppParser()
  11 |     def test_class_declarations(self):
  12 |         cpp_code = '''
  14 |         class MyClass {
  15 |             int x;
  16 |         };
  19 |         template<typename T>
  20 |         class TemplateClass {
  21 |             T value;
  22 |         };
  25 |         struct MyStruct {
  26 |             double y;
  27 |         };
  29 |         declarations = self.parser.parse(cpp_code)
  30 |         class_names = {d.name for d in declarations if d.kind == 'class'}
  31 |         self.assertEqual(class_names, {'MyClass', 'TemplateClass', 'MyStruct'})
  33 |     def test_function_declarations(self):
  34 |         cpp_code = '''
  36 |         void func1(int x) {
  37 |             return x + 1;
  38 |         }
  41 |         template<typename T>
  42 |         T func2(T x) {
  43 |             return x * 2;
  44 |         }
  47 |         int func3() const noexcept {
  48 |             return 42;
  49 |         }
  52 |         void func4() = default;
  53 |         void func5() = delete;
  55 |         declarations = self.parser.parse(cpp_code)
  56 |         func_names = {d.name for d in declarations if d.kind == 'function'}
  57 |         self.assertEqual(func_names, {'func1', 'func2', 'func3', 'func4', 'func5'})
  59 |     def test_namespace_declarations(self):
  60 |         cpp_code = '''
  61 |         namespace ns1 {
  62 |             void func1() {}
  63 |         }
  65 |         namespace ns2 {
  66 |             class MyClass {};
  67 |         }
  69 |         declarations = self.parser.parse(cpp_code)
  70 |         namespace_names = {d.name for d in declarations if d.kind == 'namespace'}
  71 |         self.assertEqual(namespace_names, {'ns1', 'ns2'})
  73 |     def test_enum_declarations(self):
  74 |         cpp_code = '''
  75 |         enum Color {
  76 |             RED,
  77 |             GREEN,
  78 |             BLUE
  79 |         };
  81 |         enum class Direction {
  82 |             NORTH,
  83 |             SOUTH,
  84 |             EAST,
  85 |             WEST
  86 |         };
  88 |         declarations = self.parser.parse(cpp_code)
  89 |         enum_names = {d.name for d in declarations if d.kind == 'enum'}
  90 |         self.assertEqual(enum_names, {'Color', 'Direction'})
  92 |     def test_typedef_declarations(self):
  93 |         cpp_code = '''
  94 |         typedef int Integer;
  95 |         typedef double* DoublePtr;
  96 |         typedef void (*FuncPtr)(int);
  98 |         declarations = self.parser.parse(cpp_code)
  99 |         typedef_names = {d.name for d in declarations if d.kind == 'typedef'}
 100 |         self.assertEqual(typedef_names, {'Integer', 'DoublePtr', 'FuncPtr'})
 102 |     def test_using_declarations(self):
 103 |         cpp_code = '''
 104 |         using MyInt = int;
 105 |         using MyFunc = void(*)(double);
 107 |         declarations = self.parser.parse(cpp_code)
 108 |         using_names = {d.name for d in declarations if d.kind == 'using'}
 109 |         self.assertEqual(using_names, {'MyInt', 'MyFunc'})
```

---
### File: ./tests/test_go_parser.py
#### Summary
```
File: test_go_parser.py
Language: python
```

```python
   3 | import pytest
   4 | from codeconcat.parser.language_parsers.go_parser import parse_go
   7 | def test_parse_go_function():
   9 |     code = """
  10 | package main
  12 | func hello() {
  13 |     fmt.Println("Hello, World!")
  14 | }
  16 | func add(x, y int) int {
  17 |     return x + y
  18 | }
  20 |     result = parse_go("test.go", code)
  21 |     assert result is not None
  22 |     assert len(result.declarations) == 2
  24 |     hello_func = next(d for d in result.declarations if d.name == "hello")
  25 |     assert hello_func.kind == "function"
  26 |     assert hello_func.start_line == 4
  28 |     add_func = next(d for d in result.declarations if d.name == "add")
  29 |     assert add_func.kind == "function"
  30 |     assert add_func.start_line == 8
  33 | def test_parse_go_struct():
  35 |     code = """
  36 | package main
  38 | type Person struct {
  39 |     Name string
  40 |     Age  int
  41 | }
  43 | type Employee struct {
  44 |     Person
  45 |     Salary float64
  46 | }
  48 |     result = parse_go("test.go", code)
  49 |     assert result is not None
  50 |     assert len(result.declarations) == 2
  52 |     person = next(d for d in result.declarations if d.name == "Person")
  53 |     assert person.kind == "struct"
  54 |     assert person.start_line == 4
  56 |     employee = next(d for d in result.declarations if d.name == "Employee")
  57 |     assert employee.kind == "struct"
  58 |     assert employee.start_line == 9
  61 | def test_parse_go_interface():
  63 |     code = """
  64 | package main
  66 | type Reader interface {
  67 |     Read(p []byte) (n int, err error)
  68 | }
  70 | type Writer interface {
  71 |     Write(p []byte) (n int, err error)
  72 | }
  74 |     result = parse_go("test.go", code)
  75 |     assert result is not None
  76 |     assert len(result.declarations) == 2
  78 |     reader = next(d for d in result.declarations if d.name == "Reader")
  79 |     assert reader.kind == "interface"
  80 |     assert reader.start_line == 4
  82 |     writer = next(d for d in result.declarations if d.name == "Writer")
  83 |     assert writer.kind == "interface"
  84 |     assert writer.start_line == 8
  87 | def test_parse_go_const_var():
  89 |     code = """
  90 | package main
  92 | const (
  93 |     MaxItems = 100
  94 |     MinItems = 1
  95 | )
  97 | var (
  98 |     Debug = false
  99 |     Count = 0
 100 | )
 102 |     result = parse_go("test.go", code)
 103 |     assert result is not None
 104 |     assert len(result.declarations) == 4
 106 |     max_items = next(d for d in result.declarations if d.name == "MaxItems")
 107 |     assert max_items.kind == "const"
 108 |     assert max_items.start_line == 5
 110 |     min_items = next(d for d in result.declarations if d.name == "MinItems")
 111 |     assert min_items.kind == "const"
 112 |     assert min_items.start_line == 6
 114 |     debug = next(d for d in result.declarations if d.name == "Debug")
 115 |     assert debug.kind == "var"
 116 |     assert debug.start_line == 10
 118 |     count = next(d for d in result.declarations if d.name == "Count")
 119 |     assert count.kind == "var"
 120 |     assert count.start_line == 11
 123 | def test_parse_go_empty():
 125 |     result = parse_go("test.go", "")
 126 |     assert result is not None
 127 |     assert len(result.declarations) == 0
 130 | def test_parse_go_invalid():
 132 |     code = """
 133 | this is not valid go code
 135 |     result = parse_go("test.go", code)
 136 |     assert result is not None
 137 |     assert len(result.declarations) == 0
```

---
### File: ./tests/__init__.py
#### Summary
```
File: __init__.py
Language: python
```

```python

```

---
### File: ./tests/test_julia_parser.py
#### Summary
```
File: test_julia_parser.py
Language: python
```

```python
   3 | import pytest
   4 | from codeconcat.parser.language_parsers.julia_parser import parse_julia
   7 | def test_parse_julia_function():
   9 |     code = """
  10 | function greet()
  11 |     println("Hello, World!")
  12 | end
  14 | function add(x::Int, y::Int)::Int
  15 |     return x + y
  16 | end
  19 | square(x) = x * x
  21 |     result = parse_julia("test.jl", code)
  22 |     assert result is not None
  23 |     assert len(result.declarations) == 3
  25 |     greet = next(d for d in result.declarations if d.name == "greet")
  26 |     assert greet.kind == "function"
  27 |     assert greet.start_line == 2
  29 |     add = next(d for d in result.declarations if d.name == "add")
  30 |     assert add.kind == "function"
  31 |     assert add.start_line == 6
  33 |     square = next(d for d in result.declarations if d.name == "square")
  34 |     assert square.kind == "function"
  35 |     assert square.start_line == 10
  38 | def test_parse_julia_struct():
  40 |     code = """
  41 | struct Point
  42 |     x::Float64
  43 |     y::Float64
  44 | end
  46 | mutable struct Person
  47 |     name::String
  48 |     age::Int
  49 | end
  51 |     result = parse_julia("test.jl", code)
  52 |     assert result is not None
  53 |     assert len(result.declarations) == 2
  55 |     point = next(d for d in result.declarations if d.name == "Point")
  56 |     assert point.kind == "struct"
  57 |     assert point.start_line == 2
  59 |     person = next(d for d in result.declarations if d.name == "Person")
  60 |     assert person.kind == "struct"
  61 |     assert person.start_line == 7
  64 | def test_parse_julia_abstract_type():
  66 |     code = """
  67 | abstract type Shape end
  69 | abstract type Animal <: Organism end
  71 |     result = parse_julia("test.jl", code)
  72 |     assert result is not None
  73 |     assert len(result.declarations) == 2
  75 |     shape = next(d for d in result.declarations if d.name == "Shape")
  76 |     assert shape.kind == "abstract"
  77 |     assert shape.start_line == 2
  79 |     animal = next(d for d in result.declarations if d.name == "Animal")
  80 |     assert animal.kind == "abstract"
  81 |     assert animal.start_line == 4
  84 | def test_parse_julia_module():
  86 |     code = """
  87 | module Geometry
  89 | export Point, distance
  91 | struct Point
  92 |     x::Float64
  93 |     y::Float64
  94 | end
  96 | function distance(p1::Point, p2::Point)
  97 |     sqrt((p2.x - p1.x)^2 + (p2.y - p1.y)^2)
  98 | end
 100 | end # module
 102 |     result = parse_julia("test.jl", code)
 103 |     assert result is not None
 104 |     assert len(result.declarations) == 4
 106 |     module_decl = next(d for d in result.declarations if d.name == "Geometry")
 107 |     assert module_decl.kind == "module"
 108 |     assert module_decl.start_line == 2
 110 |     point = next(d for d in result.declarations if d.name == "Point")
 111 |     assert point.kind == "struct"
 112 |     assert point.start_line == 6
 114 |     distance = next(d for d in result.declarations if d.name == "distance")
 115 |     assert distance.kind == "function"
 116 |     assert distance.start_line == 10
 119 | def test_parse_julia_macro():
 121 |     code = """
 122 | macro debug(expr)
 123 |     return :(println("Debug: ", $(esc(expr))))
 124 | end
 126 | @inline function fast_function(x)
 127 |     x + 1
 128 | end
 130 |     result = parse_julia("test.jl", code)
 131 |     assert result is not None
 132 |     assert len(result.declarations) == 2
 134 |     debug = next(d for d in result.declarations if d.name == "debug")
 135 |     assert debug.kind == "macro"
 136 |     assert debug.start_line == 2
 138 |     fast_function = next(d for d in result.declarations if d.name == "fast_function")
 139 |     assert fast_function.kind == "function"
 140 |     assert fast_function.start_line == 6
 143 | def test_parse_julia_empty():
 145 |     result = parse_julia("test.jl", "")
 146 |     assert result is not None
 147 |     assert len(result.declarations) == 0
 150 | def test_parse_julia_invalid():
 152 |     code = """
 153 | this is not valid julia code
 155 |     result = parse_julia("test.jl", code)
 156 |     assert result is not None
 157 |     assert len(result.declarations) == 0
```

---
### File: ./tests/test_content_processor.py
#### Summary
```
File: test_content_processor.py
Language: python
```

```python
   3 | import pytest
   4 | from codeconcat.base_types import (
   5 |     CodeConCatConfig,
   6 |     ParsedFileData,
   7 |     TokenStats,
   8 |     SecurityIssue,
   9 |     Declaration
  10 | )
  11 | from codeconcat.processor.content_processor import (
  12 |     process_file_content,
  13 |     generate_file_summary,
  14 |     generate_directory_structure
  15 | )
  18 | def test_process_file_content_basic():
  19 |     content = "line1\nline2\nline3"
  20 |     config = CodeConCatConfig(
  21 |         remove_empty_lines=False,
  22 |         remove_comments=False,
  23 |         show_line_numbers=False
  24 |     )
  25 |     result = process_file_content(content, config)
  26 |     assert result == content
  29 | def test_process_file_content_with_line_numbers():
  30 |     content = "line1\nline2\nline3"
  31 |     config = CodeConCatConfig(
  32 |         remove_empty_lines=False,
  33 |         remove_comments=False,
  34 |         show_line_numbers=True
  35 |     )
  36 |     result = process_file_content(content, config)
  37 |     expected = "   1 | line1\n   2 | line2\n   3 | line3"
  38 |     assert result == expected
  41 | def test_process_file_content_remove_empty_lines():
  42 |     content = "line1\n\nline2\n\nline3"
  43 |     config = CodeConCatConfig(
  44 |         remove_empty_lines=True,
  45 |         remove_comments=False,
  46 |         show_line_numbers=False
  47 |     )
  48 |     result = process_file_content(content, config)
  49 |     assert result == "line1\nline2\nline3"
  52 | def test_process_file_content_remove_comments():
  53 |     content = "line1\n# comment\nline2\n// comment\nline3"
  54 |     config = CodeConCatConfig(
  55 |         remove_empty_lines=False,
  56 |         remove_comments=True,
  57 |         show_line_numbers=False
  58 |     )
  59 |     result = process_file_content(content, config)
  60 |     assert result == "line1\nline2\nline3"
  63 | def test_generate_file_summary():
  64 |     file_data = ParsedFileData(
  65 |         file_path="/path/to/test.py",
  66 |         language="python",
  67 |         content="test content",
  68 |         declarations=[
  69 |             Declaration(
  70 |                 kind="function",
  71 |                 name="test_func",
  72 |                 start_line=1,
  73 |                 end_line=5,
  74 |                 modifiers=set(),
  75 |                 docstring=None
  76 |             )
  77 |         ],
  78 |         token_stats=TokenStats(
  79 |             gpt3_tokens=100,
  80 |             gpt4_tokens=120,
  81 |             davinci_tokens=110,
  82 |             claude_tokens=115
  83 |         ),
  84 |         security_issues=[
  85 |             SecurityIssue(
  86 |                 issue_type="hardcoded_secret",
  87 |                 line_number=3,
  88 |                 line_content="password = 'secret'",
  89 |                 severity="high",
  90 |                 description="Hardcoded password found in source code"
  91 |             )
  92 |         ]
  93 |     )
  95 |     summary = generate_file_summary(file_data)
  96 |     assert "test.py" in summary
  97 |     assert "python" in summary
  98 |     assert "GPT-3.5: 100" in summary
  99 |     assert "hardcoded_secret" in summary
 100 |     assert "function: test_func" in summary
 103 | def test_generate_directory_structure():
 104 |     file_paths = [
 105 |         "src/main.py",
 106 |         "src/utils/helper.py",
 107 |         "tests/test_main.py"
 108 |     ]
 109 |     structure = generate_directory_structure(file_paths)
 110 |     assert "src" in structure
 111 |     assert "main.py" in structure
 112 |     assert "utils" in structure
 113 |     assert "helper.py" in structure
 114 |     assert "tests" in structure
 115 |     assert "test_main.py" in structure
```

---
### File: ./tests/test_js_ts_parser.py
#### Summary
```
File: test_js_ts_parser.py
Language: python
```

```python
   1 | import pytest
   2 | from codeconcat.parser.language_parsers.js_ts_parser import parse_javascript_or_typescript
   5 | def test_basic_class():
   6 |     content = """\
  10 | export class MyClass extends BaseClass {
  12 | }
  14 |     parsed = parse_javascript_or_typescript("MyClass.ts", content, language="typescript")
  15 |     assert len(parsed.declarations) == 1
  17 |     decl = parsed.declarations[0]
  18 |     assert decl.kind == "class"
  19 |     assert decl.name == "MyClass"
  20 |     assert "export" in decl.modifiers
  21 |     assert decl.docstring is not None
  22 |     assert "This is a class doc" in decl.docstring
  25 | def test_function():
  26 |     content = """\
  28 | export function myFunction(a, b) {
  29 |   return a + b;
  30 | }
  32 |     parsed = parse_javascript_or_typescript("func.js", content, language="javascript")
  33 |     assert len(parsed.declarations) == 1
  35 |     decl = parsed.declarations[0]
  36 |     assert decl.kind == "function"
  37 |     assert decl.name == "myFunction"
  38 |     assert "export" in decl.modifiers
  39 |     assert decl.start_line == 2
  40 |     assert decl.end_line == 4
  43 | def test_arrow_function():
  44 |     content = """\
  46 | export const add = (x, y) => {
  47 |   return x + y;
  48 | };
  50 |     parsed = parse_javascript_or_typescript("arrow.js", content, language="javascript")
  51 |     assert len(parsed.declarations) == 1
  53 |     decl = parsed.declarations[0]
  54 |     assert decl.kind == "arrow_function"
  55 |     assert decl.name == "add"
  56 |     assert "export" in decl.modifiers
  57 |     assert "Arrow doc" in decl.docstring
  60 | def test_method_in_class():
  61 |     content = """\
  62 | class MyClass {
  64 |   myMethod(arg) {
  65 |     return arg * 2;
  66 |   }
  67 | }
  69 |     parsed = parse_javascript_or_typescript("MyClass.js", content, language="javascript")
  83 |     assert len(parsed.declarations) == 2
  85 |     class_decl = parsed.declarations[0]
  86 |     method_decl = parsed.declarations[1]
  89 |     assert class_decl.kind == "class"
  90 |     assert class_decl.name == "MyClass"
  93 |     assert method_decl.kind == "method"
  94 |     assert method_decl.name == "myMethod"
  95 |     assert "doc for method" in method_decl.docstring
  98 | def test_interface_typescript():
  99 |     content = """\
 101 | export interface Foo<T> extends Bar, Baz<T> {
 102 |   someProp: string;
 103 | }
 105 |     parsed = parse_javascript_or_typescript("types.ts", content, language="typescript")
 106 |     assert len(parsed.declarations) == 1
 108 |     decl = parsed.declarations[0]
 109 |     assert decl.kind == "interface"
 110 |     assert decl.name == "Foo"
 111 |     assert "export" in decl.modifiers
 112 |     assert "Interface doc" in decl.docstring
 115 | def test_type_alias():
 116 |     content = """\
 118 | export type MyAlias = string | number;
 120 |     parsed = parse_javascript_or_typescript("alias.ts", content, language="typescript")
 121 |     assert len(parsed.declarations) == 1
 123 |     decl = parsed.declarations[0]
 124 |     assert decl.kind == "type"
 125 |     assert decl.name == "MyAlias"
 126 |     assert "export" in decl.modifiers
 127 |     assert "Type doc" in decl.docstring
 130 | def test_enum():
 131 |     content = """\
 132 | @CoolDecorator
 133 | export enum MyEnum {
 134 |   A,
 135 |   B,
 136 |   C
 137 | }
 140 |     parsed = parse_javascript_or_typescript("enum.ts", content, language="typescript")
 141 |     assert len(parsed.declarations) == 1
 143 |     decl = parsed.declarations[0]
 144 |     assert decl.kind == "enum"
 145 |     assert decl.name == "MyEnum"
 147 |     assert "@CoolDecorator" in decl.modifiers
 148 |     assert "export" in decl.modifiers
 151 | def test_deeply_nested():
 152 |     content = """\
 153 | export function outer() {
 154 |   function inner() {
 155 |     class InnerClass {
 156 |       method() {
 157 |         return "hello";
 158 |       }
 159 |     }
 160 |     return new InnerClass();
 161 |   }
 162 |   return inner();
 163 | }
 167 |     parsed = parse_javascript_or_typescript("nested.js", content, language="javascript")
 178 |     assert len(parsed.declarations) >= 3
 181 |     outer_func = parsed.declarations[0]
 182 |     assert outer_func.kind == "function"
 183 |     assert outer_func.name == "outer"
 186 |     inner_func = parsed.declarations[1]
 187 |     assert inner_func.kind == "function"
 188 |     assert inner_func.name == "inner"
 191 |     inner_class = parsed.declarations[2]
 192 |     assert inner_class.kind == "class"
 193 |     assert inner_class.name == "InnerClass"
 196 | def test_multiline_doc_comment():
 197 |     content = """\
 202 | export function multilineDoc() {
 203 |   return true;
 204 | }
 206 |     parsed = parse_javascript_or_typescript("multiline.js", content, language="javascript")
 207 |     assert len(parsed.declarations) == 1
 209 |     decl = parsed.declarations[0]
 210 |     assert decl.kind == "function"
 211 |     assert decl.name == "multilineDoc"
 212 |     assert "multiline doc comment" in decl.docstring
 213 |     assert "spanning multiple lines" in decl.docstring
 216 | def test_no_symbols():
 218 |     content = """\
 222 |     parsed = parse_javascript_or_typescript("empty.js", content, language="javascript")
 223 |     assert len(parsed.declarations) == 0
```

---
### File: ./tests/test_codeconcat.py
#### Summary
```
File: test_codeconcat.py
Language: python
```

```python
   1 | import os
   2 | import time
   3 | import tempfile
   4 | import pytest
   5 | from unittest.mock import Mock, patch
   6 | from codeconcat.base_types import (
   7 |     CodeConCatConfig,
   8 |     Declaration,
   9 |     ParsedFileData,
  10 |     SecurityIssue,
  11 |     TokenStats,
  12 | )
  13 | from codeconcat.collector.local_collector import collect_local_files, should_include_file
  14 | from codeconcat.parser.file_parser import parse_code_files
  15 | from codeconcat.parser.language_parsers.python_parser import parse_python
  16 | from codeconcat.transformer.annotator import annotate
  17 | from codeconcat.processor.security_processor import SecurityProcessor
  18 | from codeconcat.writer.markdown_writer import write_markdown
  22 | @pytest.fixture
  23 | def temp_dir():
  24 |     with tempfile.TemporaryDirectory() as tmpdirname:
  25 |         yield tmpdirname
  28 | @pytest.fixture
  29 | def sample_python_file(temp_dir):
  30 |     content = """
  31 | def hello_world():
  33 |     return "Hello, World!"
  35 | class TestClass:
  36 |     def test_method(self):
  37 |         pass
  39 | CONSTANT = 42
  41 |     file_path = os.path.join(temp_dir, "test.py")
  42 |     with open(file_path, "w") as f:
  43 |         f.write(content)
  44 |     return file_path
  47 | @pytest.fixture
  48 | def sample_config():
  49 |     return CodeConCatConfig(
  50 |         target_path=".",
  51 |         extract_docs=True,
  52 |         merge_docs=False,
  53 |         format="markdown",
  54 |         output="test_output.md",
  55 |     )
  59 | def test_python_parser():
  60 |     content = """
  61 | def hello():
  62 |     return "Hello"
  64 | class TestClass:
  65 |     def method(self):
  66 |         pass
  68 |     parsed = parse_python("test.py", content)
  70 |     assert len(parsed.declarations) == 3
  71 |     assert any(d.name == "hello" and d.kind == "function" for d in parsed.declarations)
  72 |     assert any(d.name == "TestClass" and d.kind == "class" for d in parsed.declarations)
  73 |     assert any(d.name == "method" and d.kind == "function" for d in parsed.declarations)
  76 | def test_python_parser_edge_cases():
  77 |     content = """
  80 |     parsed = parse_python("empty.py", content)
  81 |     assert len(parsed.declarations) == 0
  83 |     content = """
  84 | def func():  # Function with no body
  85 |     pass
  87 | @decorator
  88 | def decorated_func():  # Function with decorator
  89 |     pass
  91 |     parsed = parse_python("decorated.py", content)
  92 |     assert len(parsed.declarations) == 2
  96 | def test_security_processor():
  97 |     content = """
  98 | API_KEY = "super_secret_key_12345"
  99 | password = "password123"
 101 |     issues = SecurityProcessor.scan_content(content, "test.py")
 102 |     assert len(issues) > 0
 103 |     assert any("API Key" in issue.issue_type for issue in issues)
 106 | def test_security_processor_false_positives():
 107 |     content = """
 108 | EXAMPLE_KEY = "example_key"  # Should not trigger
 109 | TEST_PASSWORD = "dummy_password"  # Should not trigger
 111 |     issues = SecurityProcessor.scan_content(content, "test.py")
 112 |     assert len(issues) == 0
 116 | def test_end_to_end_workflow(temp_dir, sample_python_file, sample_config):
 118 |     files = collect_local_files(temp_dir, sample_config)
 119 |     assert len(files) > 0
 120 |     assert any(f.file_path == sample_python_file for f in files)
 123 |     parsed_files = parse_code_files([f.file_path for f in files], sample_config)
 124 |     assert len(parsed_files) > 0
 125 |     first_file = parsed_files[0]
 126 |     assert isinstance(first_file, ParsedFileData)
 127 |     assert len(first_file.declarations) > 0
 130 |     annotated = annotate(first_file, sample_config)
 131 |     assert "hello_world" in annotated.annotated_content
 132 |     assert "TestClass" in annotated.annotated_content
 135 |     output_path = os.path.join(temp_dir, "output.md")
 136 |     sample_config.output = output_path
 137 |     result = write_markdown([annotated], [], sample_config)
 138 |     assert os.path.exists(output_path)
 139 |     with open(output_path, "r") as f:
 140 |         content = f.read()
 141 |         assert "hello_world" in content
 142 |         assert "TestClass" in content
 146 | def test_malformed_files(temp_dir):
 148 |     invalid_file = os.path.join(temp_dir, "invalid.py")
 149 |     with open(invalid_file, "wb") as f:
 150 |         f.write(b"\x80\x81\x82")  # Invalid UTF-8
 152 |     config = CodeConCatConfig(target_path=temp_dir)
 153 |     files = collect_local_files(temp_dir, config)
 154 |     assert len(files) == 0  # Should skip invalid file
 157 | def test_large_file_handling(temp_dir):
 159 |     large_file = os.path.join(temp_dir, "large.py")
 160 |     with open(large_file, "w") as f:
 161 |         for i in range(10000):
 162 |             f.write(f"def func_{i}(): pass\n")
 164 |     config = CodeConCatConfig(target_path=temp_dir)
 165 |     files = collect_local_files(temp_dir, config)
 166 |     parsed_files = parse_code_files([f.file_path for f in files], config)
 167 |     assert len(parsed_files) == 1
 168 |     assert len(parsed_files[0].declarations) == 10000
 171 | def test_special_characters(temp_dir):
 172 |     content = """
 173 | def func_with_unicode_☺():
 174 |     pass
 176 | class TestClass_🐍:
 177 |     def test_method_💻(self):
 178 |         pass
 180 |     file_path = os.path.join(temp_dir, "unicode.py")
 181 |     with open(file_path, "w", encoding="utf-8") as f:
 182 |         f.write(content)
 184 |     config = CodeConCatConfig(target_path=temp_dir)
 185 |     files = collect_local_files(temp_dir, config)
 186 |     parsed_files = parse_code_files([f.file_path for f in files], config)
 187 |     assert len(parsed_files) == 1
 188 |     assert any("☺" in d.name for d in parsed_files[0].declarations)
 189 |     assert any("🐍" in d.name for d in parsed_files[0].declarations)
 190 |     assert any("💻" in d.name for d in parsed_files[0].declarations)
 194 | def test_concurrent_processing(temp_dir):
 196 |     for i in range(10):
 197 |         with open(os.path.join(temp_dir, f"test_{i}.py"), "w") as f:
 198 |             f.write(f"def func_{i}(): pass\n" * 100)
 200 |     config = CodeConCatConfig(target_path=temp_dir, max_workers=4)
 201 |     start_time = time.time()
 202 |     files = collect_local_files(temp_dir, config)
 203 |     parsed_files = parse_code_files([f.file_path for f in files], config)
 204 |     end_time = time.time()
 206 |     assert len(parsed_files) == 10
 207 |     assert end_time - start_time < 5  # Should complete within 5 seconds
 211 | def test_config_validation():
 213 |     with pytest.raises(ValueError):
 214 |         CodeConCatConfig(target_path=".", format="invalid_format")
 217 |     config = CodeConCatConfig(target_path=".", exclude_paths=["*.pyc", "__pycache__"])
 218 |     assert not should_include_file("test.pyc", config)
 219 |     assert not should_include_file("__pycache__/test.py", config)
 220 |     assert should_include_file("test.py", config)
 224 | def test_token_counting():
 225 |     content = "def test_function(): pass"
 226 |     parsed = ParsedFileData(
 227 |         file_path="test.py",
 228 |         language="python",
 229 |         content=content,
 230 |         token_stats=TokenStats(gpt3_tokens=10, gpt4_tokens=10, davinci_tokens=10, claude_tokens=8),
 231 |     )
 233 |     assert parsed.token_stats.gpt3_tokens > 0
 234 |     assert parsed.token_stats.gpt4_tokens > 0
 235 |     assert parsed.token_stats.davinci_tokens > 0
 236 |     assert parsed.token_stats.claude_tokens > 0
 239 | if __name__ == "__main__":
 241 |     import sys
 242 |     import pytest
 244 |     sys.exit(pytest.main(["-v", "--cov=codeconcat", __file__]))
```

---
### File: ./tests/test_python_parser.py
#### Summary
```
File: test_python_parser.py
Language: python
```

```python
   3 | import unittest
   4 | from codeconcat.parser.language_parsers.python_parser import PythonParser, parse_python
   7 | class TestPythonParser(unittest.TestCase):
   8 |     def setUp(self):
   9 |         self.parser = PythonParser()
  11 |     def test_function_declarations(self):
  12 |         python_code = '''
  14 |         def func1(x):
  15 |             return x + 1
  18 |         def func2(x: int) -> int:
  19 |             return x + 1
  22 |         async def func3():
  23 |             pass
  26 |         def complex_func(
  27 |             x: int,
  28 |             y: str,
  31 |         ) -> int:
  32 |             return x
  34 |         declarations = self.parser.parse(python_code)
  35 |         func_names = {d.name for d in declarations if d.kind == 'function'}
  36 |         self.assertEqual(func_names, {'func1', 'func2', 'func3', 'complex_func'})
  38 |     def test_class_declarations(self):
  39 |         python_code = '''
  41 |         class MyClass:
  42 |             pass
  45 |         class ChildClass(MyClass):
  46 |             pass
  49 |         class MultiChild(MyClass, object):
  50 |             pass
  52 |         declarations = self.parser.parse(python_code)
  53 |         class_names = {d.name for d in declarations if d.kind == 'class'}
  54 |         self.assertEqual(class_names, {'MyClass', 'ChildClass', 'MultiChild'})
  56 |     def test_decorators(self):
  57 |         python_code = '''
  59 |         @property
  60 |         def my_prop(self):
  61 |             pass
  64 |         @classmethod
  65 |         @staticmethod
  66 |         def my_method():
  67 |             pass
  70 |         @my_decorator(
  71 |             arg1='value1',
  72 |             arg2='value2'
  73 |         )
  74 |         def decorated_func():
  75 |             pass
  78 |         @singleton
  79 |         class MyClass:
  80 |             pass
  82 |         declarations = self.parser.parse(python_code)
  84 |         prop = next(d for d in declarations if d.name == 'my_prop')
  85 |         method = next(d for d in declarations if d.name == 'my_method')
  86 |         func = next(d for d in declarations if d.name == 'decorated_func')
  87 |         cls = next(d for d in declarations if d.name == 'MyClass')
  89 |         self.assertEqual(prop.modifiers, {'@property'})
  90 |         self.assertEqual(method.modifiers, {'@classmethod', '@staticmethod'})
  91 |         self.assertTrue(any('@my_decorator' in m for m in func.modifiers))
  92 |         self.assertEqual(cls.modifiers, {'@singleton'})
  94 |     def test_docstrings(self):
  95 |         python_code = '''
  96 |         def func_with_docstring():
  99 |             It spans multiple lines.
 101 |             pass
 103 |         class ClassWithDocstring:
 106 |             With multiple lines.
 108 |             pass
 110 |         def func_with_quotes():
 112 |             pass
 114 |         declarations = self.parser.parse(python_code)
 116 |         func = next(d for d in declarations if d.name == 'func_with_docstring')
 117 |         cls = next(d for d in declarations if d.name == 'ClassWithDocstring')
 118 |         quotes_func = next(d for d in declarations if d.name == 'func_with_quotes')
 120 |         self.assertTrue(func.docstring)
 121 |         self.assertTrue(cls.docstring)
 122 |         self.assertTrue(quotes_func.docstring)
 124 |     def test_variables_and_constants(self):
 125 |         python_code = '''
 127 |         x = 1
 130 |         y: int = 2
 133 |         z = (
 134 |             some_function_call()
 135 |         )
 138 |         CONSTANT = 42
 139 |         PI: float = 3.14159
 141 |         declarations = self.parser.parse(python_code)
 143 |         var_names = {d.name for d in declarations if d.kind == 'variable'}
 144 |         const_names = {d.name for d in declarations if d.kind == 'constant'}
 146 |         self.assertEqual(var_names, {'x', 'y', 'z'})
 147 |         self.assertEqual(const_names, {'CONSTANT', 'PI'})
 149 |     def test_nested_functions(self):
 150 |         python_code = '''
 151 |         def outer():
 152 |             def inner1():
 153 |                 def inner2():
 154 |                     pass
 155 |                 return inner2
 156 |             return inner1
 158 |         declarations = self.parser.parse(python_code)
 159 |         func_names = {d.name for d in declarations if d.kind == 'function'}
 160 |         self.assertEqual(func_names, {'outer', 'inner1', 'inner2'})
 162 | if __name__ == '__main__':
 163 |     unittest.main()
```

---
### File: ./tests/test_php_parser.py
#### Summary
```
File: test_php_parser.py
Language: python
```

```python
   3 | import pytest
   4 | from codeconcat.parser.language_parsers.php_parser import parse_php
   7 | def test_parse_php_class():
   9 |     code = """<?php
  10 | class Person {
  11 |     private $name;
  12 |     private $age;
  14 |     public function __construct(string $name, int $age) {
  15 |         $this->name = $name;
  16 |         $this->age = $age;
  17 |     }
  19 |     public function getName(): string {
  20 |         return $this->name;
  21 |     }
  22 | }
  24 | class Employee extends Person {
  25 |     private $salary;
  27 |     public function __construct(string $name, int $age, float $salary) {
  28 |         parent::__construct($name, $age);
  29 |         $this->salary = $salary;
  30 |     }
  31 | }
  33 |     result = parse_php("test.php", code)
  34 |     assert result is not None
  35 |     assert len(result.declarations) == 2
  37 |     person = next(d for d in result.declarations if d.name == "Person")
  38 |     assert person.kind == "class"
  39 |     assert person.start_line == 2
  41 |     employee = next(d for d in result.declarations if d.name == "Employee")
  42 |     assert employee.kind == "class"
  43 |     assert employee.start_line == 15
  46 | def test_parse_php_interface():
  48 |     code = """<?php
  49 | interface Readable {
  50 |     public function read(): string;
  51 | }
  53 | interface Writable {
  54 |     public function write(string $data): void;
  55 | }
  57 |     result = parse_php("test.php", code)
  58 |     assert result is not None
  59 |     assert len(result.declarations) == 2
  61 |     readable = next(d for d in result.declarations if d.name == "Readable")
  62 |     assert readable.kind == "interface"
  63 |     assert readable.start_line == 2
  65 |     writable = next(d for d in result.declarations if d.name == "Writable")
  66 |     assert writable.kind == "interface"
  67 |     assert writable.start_line == 6
  70 | def test_parse_php_trait():
  72 |     code = """<?php
  73 | trait Logger {
  74 |     private $logFile;
  76 |     public function log(string $message): void {
  77 |         file_put_contents($this->logFile, $message . PHP_EOL, FILE_APPEND);
  78 |     }
  79 | }
  81 | trait Timestampable {
  82 |     private $createdAt;
  83 |     private $updatedAt;
  85 |     public function setCreatedAt(): void {
  86 |         $this->createdAt = new DateTime();
  87 |     }
  88 | }
  90 |     result = parse_php("test.php", code)
  91 |     assert result is not None
  92 |     assert len(result.declarations) == 2
  94 |     logger = next(d for d in result.declarations if d.name == "Logger")
  95 |     assert logger.kind == "trait"
  96 |     assert logger.start_line == 2
  98 |     timestampable = next(d for d in result.declarations if d.name == "Timestampable")
  99 |     assert timestampable.kind == "trait"
 100 |     assert timestampable.start_line == 10
 103 | def test_parse_php_function():
 105 |     code = """<?php
 106 | function hello(): void {
 107 |     echo "Hello, World!";
 108 | }
 110 | function add(int $x, int $y): int {
 111 |     return $x + $y;
 112 | }
 115 | $multiply = fn($x, $y) => $x * $y;
 117 |     result = parse_php("test.php", code)
 118 |     assert result is not None
 119 |     assert len(result.declarations) == 3
 121 |     hello = next(d for d in result.declarations if d.name == "hello")
 122 |     assert hello.kind == "function"
 123 |     assert hello.start_line == 2
 125 |     add = next(d for d in result.declarations if d.name == "add")
 126 |     assert add.kind == "function"
 127 |     assert add.start_line == 6
 129 |     multiply = next(d for d in result.declarations if d.name == "multiply")
 130 |     assert multiply.kind == "function"
 131 |     assert multiply.start_line == 10
 134 | def test_parse_php_namespace():
 136 |     code = """<?php
 137 | namespace App\\Models;
 139 | class User {
 140 |     private $id;
 141 |     private $email;
 142 | }
 144 | namespace App\\Controllers;
 146 | class UserController {
 147 |     public function index(): array {
 148 |         return [];
 149 |     }
 150 | }
 152 |     result = parse_php("test.php", code)
 153 |     assert result is not None
 154 |     assert len(result.declarations) == 4
 156 |     models_ns = next(d for d in result.declarations if d.name == "App\\Models")
 157 |     assert models_ns.kind == "namespace"
 158 |     assert models_ns.start_line == 2
 160 |     user = next(d for d in result.declarations if d.name == "User")
 161 |     assert user.kind == "class"
 162 |     assert user.start_line == 4
 164 |     controllers_ns = next(d for d in result.declarations if d.name == "App\\Controllers")
 165 |     assert controllers_ns.kind == "namespace"
 166 |     assert controllers_ns.start_line == 9
 168 |     controller = next(d for d in result.declarations if d.name == "UserController")
 169 |     assert controller.kind == "class"
 170 |     assert controller.start_line == 11
 173 | def test_parse_php_empty():
 175 |     result = parse_php("test.php", "")
 176 |     assert result is not None
 177 |     assert len(result.declarations) == 0
 180 | def test_parse_php_invalid():
 182 |     code = """
 183 | this is not valid php code
 185 |     result = parse_php("test.php", code)
 186 |     assert result is not None
 187 |     assert len(result.declarations) == 0
```

---
### File: ./tests/test_java_parser.py
#### Summary
```
File: test_java_parser.py
Language: python
```

```python
   3 | import pytest
   4 | from codeconcat.parser.language_parsers.java_parser import parse_java
   7 | def test_parse_java_class():
   9 |     code = """
  10 | public class Person {
  11 |     private String name;
  12 |     private int age;
  14 |     public Person(String name, int age) {
  15 |         this.name = name;
  16 |         this.age = age;
  17 |     }
  19 |     public String getName() {
  20 |         return name;
  21 |     }
  22 | }
  24 | class Employee extends Person {
  25 |     private double salary;
  27 |     public Employee(String name, int age, double salary) {
  28 |         super(name, age);
  29 |         this.salary = salary;
  30 |     }
  31 | }
  33 |     result = parse_java("test.java", code)
  34 |     assert result is not None
  35 |     assert len(result.declarations) == 2
  37 |     person = next(d for d in result.declarations if d.name == "Person")
  38 |     assert person.kind == "class"
  39 |     assert person.start_line == 2
  41 |     employee = next(d for d in result.declarations if d.name == "Employee")
  42 |     assert employee.kind == "class"
  43 |     assert employee.start_line == 15
  46 | def test_parse_java_interface():
  48 |     code = """
  49 | public interface Readable {
  50 |     String read();
  51 | }
  53 | interface Writable {
  54 |     void write(String data);
  55 | }
  57 |     result = parse_java("test.java", code)
  58 |     assert result is not None
  59 |     assert len(result.declarations) == 2
  61 |     readable = next(d for d in result.declarations if d.name == "Readable")
  62 |     assert readable.kind == "interface"
  63 |     assert readable.start_line == 2
  65 |     writable = next(d for d in result.declarations if d.name == "Writable")
  66 |     assert writable.kind == "interface"
  67 |     assert writable.start_line == 6
  70 | def test_parse_java_method():
  72 |     code = """
  73 | public class Calculator {
  74 |     public int add(int a, int b) {
  75 |         return a + b;
  76 |     }
  78 |     private double multiply(double x, double y) {
  79 |         return x * y;
  80 |     }
  82 |     protected static void log(String message) {
  83 |         System.out.println(message);
  84 |     }
  85 | }
  87 |     result = parse_java("test.java", code)
  88 |     assert result is not None
  89 |     assert len(result.declarations) == 4
  91 |     calc = next(d for d in result.declarations if d.name == "Calculator")
  92 |     assert calc.kind == "class"
  93 |     assert calc.start_line == 2
  95 |     add = next(d for d in result.declarations if d.name == "add")
  96 |     assert add.kind == "method"
  97 |     assert add.start_line == 3
  99 |     multiply = next(d for d in result.declarations if d.name == "multiply")
 100 |     assert multiply.kind == "method"
 101 |     assert multiply.start_line == 7
 103 |     log = next(d for d in result.declarations if d.name == "log")
 104 |     assert log.kind == "method"
 105 |     assert log.start_line == 11
 108 | def test_parse_java_field():
 110 |     code = """
 111 | public class Constants {
 112 |     public static final int MAX_VALUE = 100;
 113 |     private static String prefix = "test";
 114 |     protected boolean debug = false;
 115 | }
 117 |     result = parse_java("test.java", code)
 118 |     assert result is not None
 119 |     assert len(result.declarations) == 4
 121 |     constants = next(d for d in result.declarations if d.name == "Constants")
 122 |     assert constants.kind == "class"
 123 |     assert constants.start_line == 2
 125 |     max_value = next(d for d in result.declarations if d.name == "MAX_VALUE")
 126 |     assert max_value.kind == "field"
 127 |     assert max_value.start_line == 3
 129 |     prefix = next(d for d in result.declarations if d.name == "prefix")
 130 |     assert prefix.kind == "field"
 131 |     assert prefix.start_line == 4
 133 |     debug = next(d for d in result.declarations if d.name == "debug")
 134 |     assert debug.kind == "field"
 135 |     assert debug.start_line == 5
 138 | def test_parse_java_empty():
 140 |     result = parse_java("test.java", "")
 141 |     assert result is not None
 142 |     assert len(result.declarations) == 0
 145 | def test_parse_java_invalid():
 147 |     code = """
 148 | this is not valid java code
 150 |     result = parse_java("test.java", code)
 151 |     assert result is not None
 152 |     assert len(result.declarations) == 0
```

---
### File: ./tests/test_annotator.py
#### Summary
```
File: test_annotator.py
Language: python
```

```python
   3 | import pytest
   4 | from codeconcat.base_types import (
   5 |     CodeConCatConfig,
   6 |     ParsedFileData,
   7 |     Declaration
   8 | )
   9 | from codeconcat.transformer.annotator import annotate
  12 | def test_annotate_empty_file():
  13 |     parsed_data = ParsedFileData(
  14 |         file_path="/path/to/empty.py",
  15 |         language="python",
  16 |         content="",
  17 |         declarations=[]
  18 |     )
  19 |     config = CodeConCatConfig()
  21 |     result = annotate(parsed_data, config)
  22 |     assert result.summary == "No declarations found"
  23 |     assert result.tags == ["python"]
  24 |     assert "## File: /path/to/empty.py" in result.annotated_content
  27 | def test_annotate_with_declarations():
  28 |     parsed_data = ParsedFileData(
  29 |         file_path="/path/to/test.py",
  30 |         language="python",
  31 |         content="def test(): pass\nclass Test: pass",
  32 |         declarations=[
  33 |             Declaration(
  34 |                 kind="function",
  35 |                 name="test",
  36 |                 start_line=1,
  37 |                 end_line=1,
  38 |                 modifiers=set(),
  39 |                 docstring=None
  40 |             ),
  41 |             Declaration(
  42 |                 kind="class",
  43 |                 name="Test",
  44 |                 start_line=2,
  45 |                 end_line=2,
  46 |                 modifiers=set(),
  47 |                 docstring=None
  48 |             )
  49 |         ]
  50 |     )
  51 |     config = CodeConCatConfig()
  53 |     result = annotate(parsed_data, config)
  54 |     assert "1 functions, 1 classes" in result.summary
  55 |     assert set(result.tags) == {"has_functions", "has_classes", "python"}
  56 |     assert "### Functions" in result.annotated_content
  57 |     assert "### Classes" in result.annotated_content
  58 |     assert "- test" in result.annotated_content
  59 |     assert "- Test" in result.annotated_content
  62 | def test_annotate_with_structs():
  63 |     parsed_data = ParsedFileData(
  64 |         file_path="/path/to/test.cpp",
  65 |         language="cpp",
  66 |         content="struct Test { int x; };",
  67 |         declarations=[
  68 |             Declaration(
  69 |                 kind="struct",
  70 |                 name="Test",
  71 |                 start_line=1,
  72 |                 end_line=1,
  73 |                 modifiers=set(),
  74 |                 docstring=None
  75 |             )
  76 |         ]
  77 |     )
  78 |     config = CodeConCatConfig()
  80 |     result = annotate(parsed_data, config)
  81 |     assert "1 structs" in result.summary
  82 |     assert set(result.tags) == {"has_structs", "cpp"}
  83 |     assert "### Structs" in result.annotated_content
  84 |     assert "- Test" in result.annotated_content
  87 | def test_annotate_with_symbols():
  88 |     parsed_data = ParsedFileData(
  89 |         file_path="/path/to/test.py",
  90 |         language="python",
  91 |         content="x = 1",
  92 |         declarations=[
  93 |             Declaration(
  94 |                 kind="symbol",
  95 |                 name="x",
  96 |                 start_line=1,
  97 |                 end_line=1,
  98 |                 modifiers=set(),
  99 |                 docstring=None
 100 |             )
 101 |         ]
 102 |     )
 103 |     config = CodeConCatConfig()
 105 |     result = annotate(parsed_data, config)
 106 |     assert "1 symbols" in result.summary
 107 |     assert set(result.tags) == {"has_symbols", "python"}
 108 |     assert "### Symbols" in result.annotated_content
 109 |     assert "- x" in result.annotated_content
```

---
### File: ./tests/test_r_parser.py
#### Summary
```
File: test_r_parser.py
Language: python
```

```python
   1 | import unittest
   2 | from codeconcat.parser.language_parsers.r_parser import RParser, parse_r
   4 | class TestRParser(unittest.TestCase):
   5 |     def setUp(self):
   6 |         self.parser = RParser()
   8 |     def test_function_declarations(self):
   9 |         r_code = '''
  11 |         func1 <- function(x) { x + 1 }
  12 |         func2 = function(x) { x + 1 }
  13 |         function(x) -> func3
  16 |         complex_func <- # comment
  17 |           function(x) {
  18 |             x + 1
  19 |         }
  21 |         declarations = self.parser.parse(r_code)
  22 |         func_names = {d.name for d in declarations if d.kind == 'function'}
  23 |         self.assertEqual(func_names, {'func1', 'func2', 'func3', 'complex_func'})
  25 |     def test_class_declarations(self):
  26 |         r_code = '''
  28 |         setClass("MyS4Class", slots = list(x = "numeric"))
  31 |         MyS3Class <- function(x) {
  32 |             obj <- list(x = x)
  33 |             class(obj) <- "MyS3Class"
  34 |             obj
  35 |         }
  38 |         setGeneric("myMethod", function(x) standardGeneric("myMethod"))
  39 |         setMethod("myMethod", "MyS4Class", function(x) x@x)
  41 |         declarations = self.parser.parse(r_code)
  42 |         class_names = {d.name for d in declarations if d.kind == 'class'}
  43 |         method_names = {d.name for d in declarations if d.kind == 'method'}
  44 |         self.assertEqual(class_names, {'MyS4Class', 'MyS3Class'})
  45 |         self.assertEqual(method_names, {'myMethod'})
  47 |     def test_package_imports(self):
  48 |         r_code = '''
  49 |         library(dplyr)
  50 |         library("tidyr")
  51 |         require(ggplot2)
  52 |         require("data.table")
  55 |         dplyr::select
  56 |         data.table:::fread
  58 |         declarations = self.parser.parse(r_code)
  59 |         package_names = {d.name for d in declarations if d.kind == 'package'}
  60 |         self.assertEqual(
  61 |             package_names,
  62 |             {'dplyr', 'tidyr', 'ggplot2', 'data.table'}
  63 |         )
  65 |     def test_nested_functions(self):
  66 |         r_code = '''
  67 |         outer <- function() {
  68 |             inner1 <- function() {
  69 |                 inner2 <- function() {
  70 |                     x + 1
  71 |                 }
  72 |                 inner2
  73 |             }
  74 |             inner1
  75 |         }
  77 |         declarations = self.parser.parse(r_code)
  78 |         func_names = {d.name for d in declarations if d.kind == 'function'}
  79 |         self.assertEqual(func_names, {'outer', 'inner1', 'inner2'})
  81 |     def test_r6_class(self):
  82 |         r_code = '''
  84 |         Calculator <- R6Class("Calculator",
  85 |             public = list(
  86 |                 value = 0,
  87 |                 add = function(x) {
  88 |                     self$value <- self$value + x
  89 |                 },
  90 |                 subtract = function(x) {
  91 |                     self$value <- self$value - x
  92 |                 }
  93 |             )
  94 |         )
  96 |         declarations = self.parser.parse(r_code)
  97 |         class_decls = [d for d in declarations if d.kind == 'class']
  98 |         method_decls = [d for d in declarations if d.kind == 'method']
 100 |         self.assertEqual(len(class_decls), 1)
 101 |         self.assertEqual(class_decls[0].name, 'Calculator')
 102 |         self.assertEqual({m.name for m in method_decls}, {'Calculator.add', 'Calculator.subtract'})
 104 |     def test_reference_class(self):
 105 |         r_code = '''
 107 |         setRefClass("Employee",
 108 |             fields = list(
 109 |                 name = "character",
 110 |                 salary = "numeric"
 111 |             ),
 112 |             methods = list(
 113 |                 raise = function(amount) {
 114 |                     salary <<- salary + amount
 115 |                 },
 116 |                 get_info = function() {
 117 |                     paste(name, salary)
 118 |                 }
 119 |             )
 120 |         )
 122 |         declarations = self.parser.parse(r_code)
 123 |         class_decls = [d for d in declarations if d.kind == 'class']
 124 |         method_decls = [d for d in declarations if d.kind == 'method']
 126 |         self.assertEqual(len(class_decls), 1)
 127 |         self.assertEqual(class_decls[0].name, 'Employee')
 128 |         self.assertEqual({m.name for m in method_decls}, {'Employee.raise', 'Employee.get_info'})
 130 |     def test_modifiers(self):
 131 |         r_code = '''
 134 |         process_data <- function(data) {
 135 |             data
 136 |         }
 139 |         MyClass <- R6Class("MyClass")
 141 |         declarations = self.parser.parse(r_code)
 143 |         process_data = next(d for d in declarations if d.name == 'process_data')
 144 |         my_class = next(d for d in declarations if d.name == 'MyClass')
 146 |         self.assertEqual(process_data.modifiers, {'export', 'internal'})
 147 |         self.assertEqual(my_class.modifiers, {'export'})
 149 |     def test_s3_methods(self):
 150 |         r_code = '''
 152 |         print.myclass <- function(x) {
 153 |             cat("MyClass object\\n")
 154 |         }
 156 |         plot.myclass = function(x, y, ...) {
 157 |             plot(x$data)
 158 |         }
 160 |         summary.myclass -> function(object) {
 161 |             list(object)
 162 |         }
 164 |         declarations = self.parser.parse(r_code)
 165 |         method_names = {d.name for d in declarations if d.kind == 'method'}
 167 |         expected_methods = {'print.myclass', 'plot.myclass', 'summary.myclass'}
 168 |         self.assertEqual(method_names, expected_methods)
 170 |     def test_complex_assignments(self):
 171 |         r_code = '''
 173 |         func1 <- function(x) x
 174 |         func2 = function(x) x
 175 |         func3 <<- function(x) x
 176 |         function(x) -> func4
 177 |         function(x) ->> func5
 178 |         func6 := function(x) x
 180 |         declarations = self.parser.parse(r_code)
 181 |         func_names = {d.name for d in declarations if d.kind == 'function'}
 183 |         expected_funcs = {'func1', 'func2', 'func3', 'func4', 'func5', 'func6'}
 184 |         self.assertEqual(func_names, expected_funcs)
 186 |     def test_dollar_notation_methods(self):
 187 |         r_code = '''
 189 |         Employee$get_salary <- function(x) {
 190 |             x$salary
 191 |         }
 193 |         Employee$set_salary <- function(x, value) {
 194 |             x$salary <- value
 195 |         }
 198 |         Employee.Department$get_manager <- function(x) {
 199 |             x$manager
 200 |         }
 202 |         declarations = self.parser.parse(r_code)
 203 |         method_names = {d.name for d in declarations if d.kind == 'method'}
 205 |         expected_methods = {
 206 |             'Employee$get_salary',
 207 |             'Employee$set_salary',
 208 |             'Employee.Department$get_manager'
 209 |         }
 210 |         self.assertEqual(method_names, expected_methods)
 212 |     def test_object_methods_with_dots(self):
 213 |         r_code = '''
 215 |         Employee.new <- function(name, salary) {
 216 |             list(name = name, salary = salary)
 217 |         }
 219 |         Employee.get_info <- function(self) {
 220 |             paste(self$name, self$salary)
 221 |         }
 224 |         Department.Employee.create <- function(dept, name) {
 225 |             list(department = dept, name = name)
 226 |         }
 228 |         declarations = self.parser.parse(r_code)
 229 |         method_names = {d.name for d in declarations if d.kind == 'method'}
 231 |         expected_methods = {
 232 |             'Employee.new',
 233 |             'Employee.get_info',
 234 |             'Department.Employee.create'
 235 |         }
 236 |         self.assertEqual(method_names, expected_methods)
 238 | if __name__ == '__main__':
 239 |     unittest.main()
```

---
### File: ./codeconcat/version.py
#### Summary
```
File: version.py
Language: python
```

```python
   3 | __version__ = "0.5.2"
```

---
### File: ./codeconcat/__init__.py
#### Summary
```
File: __init__.py
Language: python
```

```python
   2 | CodeConCat - An LLM-friendly code parser, aggregator and doc extractor.
   5 | from .main import run_codeconcat, run_codeconcat_in_memory
   6 | from .base_types import CodeConCatConfig, AnnotatedFileData, ParsedDocData
   7 | from .version import __version__
   9 | __all__ = [
  10 |     "run_codeconcat",
  11 |     "run_codeconcat_in_memory",
  12 |     "CodeConCatConfig",
  13 |     "AnnotatedFileData",
  14 |     "ParsedDocData",
  15 |     "__version__",
  16 | ]
```

---
### File: ./codeconcat/base_types.py
#### Summary
```
File: base_types.py
Language: python
```

```python
   2 | base_types.py
   4 | Holds data classes and typed structures used throughout CodeConCat.
   8 | from dataclasses import dataclass, field
   9 | from typing import Any, Dict, List, Optional, Set
  11 | PROGRAMMING_QUOTES = [
  12 |     '"Clean code always looks like it was written by someone who cares." - Robert C. Martin',
  13 |     '"First, solve the problem. Then write the code." - John Johnson',
  14 |     '"Any fool can write code that a computer can understand. Good programmers write code that humans can understand." - Martin Fowler',
  15 |     "\"Programming isn't about what you know; it's about what you can figure out.\" - Chris Pine",
  16 |     '"Code is like humor. When you have to explain it, it\'s bad." - Cory House',
  17 |     '"The most important property of a program is whether it accomplishes the intention of its user." - C.A.R. Hoare',
  18 |     "\"Good code is its own best documentation. As you're about to add a comment, ask yourself, 'How can I improve the code so that this comment isn't needed?'\" - Steve McConnell",
  19 |     '"Measuring programming progress by lines of code is like measuring aircraft building progress by weight." - Bill Gates',
  20 |     '"Talk is cheap. Show me the code." - Linus Torvalds',
  21 |     '"Truth can only be found in one place: the code." - Robert C. Martin',
  22 |     '"It is not enough for code to work." - Robert C. Martin',
  23 |     '"Debugging is twice as hard as writing the code in the first place. Therefore, if you write the code as cleverly as possible, you are, by definition, not smart enough to debug it." - Brian W. Kernighan',
  24 |     '"Sometimes it pays to stay in bed on Monday rather than spending the rest of the week debugging Monday\'s code." - Dan Salomon',
  25 |     '"Always code as if the guy who ends up maintaining your code will be a violent psychopath who knows where you live." - Rick Osborne',
  26 | ]
  28 | VALID_FORMATS = {"markdown", "json", "xml"}
  30 | @dataclass
  31 | class SecurityIssue:
  34 |     line_number: int
  35 |     line_content: str
  36 |     issue_type: str
  37 |     severity: str
  38 |     description: str
  41 | @dataclass
  42 | class TokenStats:
  45 |     gpt3_tokens: int
  46 |     gpt4_tokens: int
  47 |     davinci_tokens: int
  48 |     claude_tokens: int
  51 | @dataclass
  52 | class Declaration:
  55 |     kind: str
  56 |     name: str
  57 |     start_line: int
  58 |     end_line: int
  59 |     modifiers: Set[str] = field(default_factory=set)
  60 |     docstring: str = ""
  62 |     def __post_init__(self):
  64 |         pass
  67 | @dataclass
  68 | class ParsedFileData:
  70 |     Parsed output of a single code file.
  73 |     file_path: str
  74 |     language: str
  75 |     content: str
  76 |     declarations: List[Declaration] = field(default_factory=list)
  77 |     token_stats: Optional[TokenStats] = None
  78 |     security_issues: List[SecurityIssue] = field(default_factory=list)
  81 | @dataclass
  82 | class AnnotatedFileData:
  84 |     A file's annotated content, ready to be written (Markdown/JSON).
  87 |     file_path: str
  88 |     language: str
  89 |     annotated_content: str
  90 |     content: str = ""
  91 |     summary: str = ""
  92 |     tags: List[str] = field(default_factory=list)
  95 | @dataclass
  96 | class ParsedDocData:
  98 |     Represents a doc file, storing raw text + file path + doc type (md, rst, etc.).
 101 |     file_path: str
 102 |     doc_type: str
 103 |     content: str
 106 | @dataclass
 107 | class CodeConCatConfig:
 110 |     Fields:
 111 |       - target_path: local directory or placeholder for GitHub
 112 |       - github_url: optional GitHub repository URL
 113 |       - github_token: personal access token for private repos
 114 |       - github_ref: optional GitHub reference (branch/tag)
 115 |       - include_languages / exclude_languages
 116 |       - include_paths / exclude_paths: patterns for including/excluding
 117 |       - extract_docs: whether to parse docs
 118 |       - merge_docs: whether to merge doc content into the same output
 119 |       - doc_extensions: list of recognized doc file extensions
 120 |       - custom_extension_map: user-specified extension→language
 121 |       - output: final file name
 122 |       - format: 'markdown', 'json', or 'xml'
 123 |       - max_workers: concurrency
 124 |       - disable_tree: whether to disable directory structure
 125 |       - disable_copy: whether to disable copying output
 126 |       - disable_annotations: whether to disable annotations
 127 |       - disable_symbols: whether to disable symbol extraction
 128 |       - include_file_summary: whether to include file summaries
 129 |       - include_directory_structure: whether to show directory structure
 130 |       - remove_comments: whether to remove comments from output
 131 |       - remove_empty_lines: whether to remove empty lines
 132 |       - show_line_numbers: whether to show line numbers
 135 |     target_path: str = "."
 136 |     github_url: Optional[str] = None
 137 |     github_token: Optional[str] = None
 138 |     github_ref: Optional[str] = None
 139 |     include_languages: List[str] = field(default_factory=list)
 140 |     exclude_languages: List[str] = field(default_factory=list)
 141 |     include_paths: List[str] = field(default_factory=list)
 142 |     exclude_paths: List[str] = field(default_factory=list)
 143 |     extract_docs: bool = False
 144 |     merge_docs: bool = False
 145 |     doc_extensions: List[str] = field(default_factory=lambda: [".md", ".rst", ".txt", ".rmd"])
 146 |     custom_extension_map: Dict[str, str] = field(default_factory=dict)
 147 |     output: str = "code_concat_output.md"
 148 |     format: str = "markdown"
 149 |     max_workers: int = 4
 150 |     disable_tree: bool = False
 151 |     disable_copy: bool = False
 152 |     disable_annotations: bool = False
 153 |     disable_symbols: bool = False
 154 |     disable_ai_context: bool = False
 155 |     include_file_summary: bool = True
 156 |     include_directory_structure: bool = True
 157 |     remove_comments: bool = False
 158 |     remove_empty_lines: bool = False
 159 |     show_line_numbers: bool = False
 161 |     def __post_init__(self):
 163 |         if self.format not in VALID_FORMATS:
 164 |             raise ValueError(f"Invalid format '{self.format}'. Must be one of: {', '.join(VALID_FORMATS)}")
```

---
### File: ./codeconcat/main.py
#### Summary
```
File: main.py
Language: python
```

```python
   1 | import argparse
   2 | import logging
   3 | import os
   4 | import sys
   5 | from typing import List
   7 | from codeconcat.base_types import AnnotatedFileData, CodeConCatConfig, ParsedDocData
   8 | from codeconcat.collector.github_collector import collect_github_files
   9 | from codeconcat.collector.local_collector import (
  10 |     collect_local_files,
  11 |     should_include_file,
  12 |     should_skip_dir,
  13 | )
  14 | from codeconcat.config.config_loader import load_config
  15 | from codeconcat.parser.doc_extractor import extract_docs
  16 | from codeconcat.parser.file_parser import parse_code_files
  17 | from codeconcat.transformer.annotator import annotate
  18 | from codeconcat.writer.json_writer import write_json
  19 | from codeconcat.writer.markdown_writer import write_markdown
  20 | from codeconcat.writer.xml_writer import write_xml
  23 | logger = logging.getLogger("codeconcat")
  24 | logger.setLevel(logging.WARNING)
  27 | class CodeConcatError(Exception):
  30 |     pass
  33 | class ConfigurationError(CodeConcatError):
  36 |     pass
  39 | class FileProcessingError(CodeConcatError):
  42 |     pass
  45 | class OutputError(CodeConcatError):
  48 |     pass
  51 | def cli_entry_point():
  52 |     parser = argparse.ArgumentParser(
  53 |         prog="codeconcat",
  54 |         description="CodeConCat - An LLM-friendly code aggregator and doc extractor.",
  55 |     )
  57 |     parser.add_argument("target_path", nargs="?", default=".")
  58 |     parser.add_argument(
  59 |         "--github", help="GitHub URL or shorthand (e.g., 'owner/repo')", default=None
  60 |     )
  61 |     parser.add_argument("--github-token", help="GitHub personal access token", default=None)
  62 |     parser.add_argument("--ref", help="Branch, tag, or commit hash for GitHub repo", default=None)
  64 |     parser.add_argument("--docs", action="store_true", help="Enable doc extraction")
  65 |     parser.add_argument(
  66 |         "--merge-docs", action="store_true", help="Merge doc content with code output"
  67 |     )
  69 |     parser.add_argument("--output", default="code_concat_output.md", help="Output file name")
  70 |     parser.add_argument(
  71 |         "--format", choices=["markdown", "json", "xml"], default="markdown", help="Output format"
  72 |     )
  74 |     parser.add_argument("--include", nargs="*", default=[], help="Glob patterns to include")
  75 |     parser.add_argument("--exclude", nargs="*", default=[], help="Glob patterns to exclude")
  76 |     parser.add_argument(
  77 |         "--include-languages", nargs="*", default=[], help="Only include these languages"
  78 |     )
  79 |     parser.add_argument(
  80 |         "--exclude-languages", nargs="*", default=[], help="Exclude these languages"
  81 |     )
  83 |     parser.add_argument("--max-workers", type=int, default=4, help="Number of worker threads")
  84 |     parser.add_argument("--init", action="store_true", help="Initialize default configuration file")
  86 |     parser.add_argument(
  87 |         "--no-tree", action="store_true", help="Disable folder tree generation (enabled by default)"
  88 |     )
  89 |     parser.add_argument(
  90 |         "--no-copy",
  91 |         action="store_true",
  92 |         help="Disable copying output to clipboard (enabled by default)",
  93 |     )
  94 |     parser.add_argument(
  95 |         "--no-ai-context", action="store_true", help="Disable AI context generation"
  96 |     )
  97 |     parser.add_argument("--no-annotations", action="store_true", help="Disable code annotations")
  98 |     parser.add_argument("--no-symbols", action="store_true", help="Disable symbol extraction")
  99 |     parser.add_argument("--debug", action="store_true", help="Enable debug logging")
 101 |     args = parser.parse_args()
 104 |     if args.debug:
 105 |         logger.setLevel(logging.DEBUG)
 107 |         for name in logging.root.manager.loggerDict:
 108 |             if name.startswith("codeconcat"):
 109 |                 logging.getLogger(name).setLevel(logging.DEBUG)
 112 |     if not logger.handlers:
 113 |         ch = logging.StreamHandler()
 114 |         ch.setLevel(logging.DEBUG if args.debug else logging.WARNING)
 115 |         formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
 116 |         ch.setFormatter(formatter)
 117 |         logger.addHandler(ch)
 119 |     logger.debug("Debug logging enabled")
 122 |     if args.init:
 123 |         create_default_config()
 124 |         print("[CodeConCat] Created default configuration file: .codeconcat.yml")
 125 |         sys.exit(0)
 128 |     cli_args = vars(args)
 129 |     logging.debug("CLI args: %s", cli_args)  # Debug print
 130 |     config = load_config(cli_args)
 132 |     try:
 133 |         run_codeconcat(config)
 134 |     except Exception as e:
 135 |         print(f"[CodeConCat] Error: {str(e)}", file=sys.stderr)
 136 |         sys.exit(1)
 139 | def create_default_config():
 141 |     if os.path.exists(".codeconcat.yml"):
 142 |         print("Configuration file already exists. Remove it first to create a new one.")
 143 |         return
 145 |     config_content = """# CodeConCat Configuration
 148 | include_paths:
 152 | exclude_paths:
 154 |   - "**/*.{yml,yaml}"
 155 |   - "**/.codeconcat.yml"
 156 |   - "**/.github/*.{yml,yaml}"
 159 |   - "**/tests/**"
 160 |   - "**/test_*.py"
 161 |   - "**/*_test.py"
 164 |   - "**/build/**"
 165 |   - "**/dist/**"
 166 |   - "**/__pycache__/**"
 167 |   - "**/*.{pyc,pyo,pyd}"
 168 |   - "**/.pytest_cache/**"
 169 |   - "**/.coverage"
 170 |   - "**/htmlcov/**"
 173 |   - "**/*.{md,rst,txt}"
 174 |   - "**/LICENSE*"
 175 |   - "**/README*"
 178 | include_languages:
 182 | exclude_languages:
 187 | output: code_concat_output.md
 188 | format: markdown  # or json, xml
 191 | extract_docs: false
 192 | merge_docs: false
 193 | disable_tree: false
 194 | disable_copy: false
 195 | disable_annotations: false
 196 | disable_symbols: false
 199 | include_file_summary: true
 200 | include_directory_structure: true
 201 | remove_comments: true
 202 | remove_empty_lines: true
 203 | show_line_numbers: true
 206 | max_workers: 4
 207 | custom_extension_map:
 212 |     with open(".codeconcat.yml", "w") as f:
 213 |         f.write(config_content)
 215 |     print("[CodeConCat] Created default configuration file: .codeconcat.yml")
 218 | def generate_folder_tree(root_path: str, config: CodeConCatConfig) -> str:
 220 |     Walk the directory tree starting at root_path and return a string that represents the folder structure.
 221 |     Respects exclusion patterns from the config.
 223 |     from codeconcat.collector.local_collector import should_include_file, should_skip_dir
 225 |     lines = []
 226 |     for root, dirs, files in os.walk(root_path):
 228 |         if should_skip_dir(root, config.exclude_paths):
 229 |             dirs[:] = []  # Clear dirs to prevent descending into this directory
 230 |             continue
 232 |         level = root.replace(root_path, "").count(os.sep)
 233 |         indent = "    " * level
 234 |         folder_name = os.path.basename(root) or root_path
 235 |         lines.append(f"{indent}{folder_name}/")
 238 |         included_files = [f for f in files if should_include_file(os.path.join(root, f), config)]
 240 |         sub_indent = "    " * (level + 1)
 241 |         for f in sorted(included_files):
 242 |             lines.append(f"{sub_indent}{f}")
 245 |         dirs[:] = [
 246 |             d for d in dirs if not should_skip_dir(os.path.join(root, d), config.exclude_paths)
 247 |         ]
 248 |         dirs.sort()  # Sort directories for consistent output
 250 |     return "\n".join(lines)
 253 | def run_codeconcat(config: CodeConCatConfig):
 255 |     try:
 257 |         if not config.target_path:
 258 |             raise ConfigurationError("Target path is required")
 259 |         if config.format not in ["markdown", "json", "xml"]:
 260 |             raise ConfigurationError(f"Invalid format: {config.format}")
 263 |         try:
 264 |             if config.github_url:
 265 |                 code_files = collect_github_files(config)
 266 |             else:
 267 |                 code_files = collect_local_files(config.target_path, config)
 269 |             if not code_files:
 270 |                 raise FileProcessingError("No files found to process")
 271 |         except Exception as e:
 272 |             raise FileProcessingError(f"Error collecting files: {str(e)}")
 275 |         folder_tree_str = ""
 276 |         if not config.disable_tree:
 277 |             try:
 278 |                 folder_tree_str = generate_folder_tree(config.target_path, config)
 279 |             except Exception as e:
 280 |                 print(f"Warning: Failed to generate folder tree: {str(e)}")
 283 |         try:
 284 |             parsed_files = parse_code_files([f.file_path for f in code_files], config)
 285 |             if not parsed_files:
 286 |                 raise FileProcessingError("No files were successfully parsed")
 287 |         except Exception as e:
 288 |             raise FileProcessingError(f"Error parsing files: {str(e)}")
 291 |         docs = []
 292 |         if config.extract_docs:
 293 |             try:
 294 |                 docs = extract_docs([f.file_path for f in code_files], config)
 295 |             except Exception as e:
 296 |                 print(f"Warning: Failed to extract documentation: {str(e)}")
 299 |         try:
 300 |             annotated_files = []
 301 |             if not config.disable_annotations:
 302 |                 for file in parsed_files:
 303 |                     try:
 304 |                         annotated = annotate(file, config)
 305 |                         annotated_files.append(annotated)
 306 |                     except Exception as e:
 307 |                         print(f"Warning: Failed to annotate {file.file_path}: {str(e)}")
 309 |                         annotated_files.append(
 310 |                             AnnotatedFileData(
 311 |                                 file_path=file.file_path,
 312 |                                 language=file.language,
 313 |                                 content=file.content,
 314 |                                 annotated_content=file.content,
 315 |                                 summary="",
 316 |                                 tags=[],
 317 |                             )
 318 |                         )
 319 |             else:
 321 |                 for file in parsed_files:
 322 |                     annotated_files.append(
 323 |                         AnnotatedFileData(
 324 |                             file_path=file.file_path,
 325 |                             language=file.language,
 326 |                             content=file.content,
 327 |                             annotated_content=file.content,
 328 |                             summary="",
 329 |                             tags=[],
 330 |                         )
 331 |                     )
 332 |         except Exception as e:
 333 |             raise FileProcessingError(f"Error during annotation: {str(e)}")
 336 |         try:
 337 |             if config.format == "markdown":
 338 |                 output = write_markdown(annotated_files, docs, config, folder_tree_str)
 339 |             elif config.format == "json":
 340 |                 output = write_json(annotated_files, docs, config, folder_tree_str)
 341 |             elif config.format == "xml":
 342 |                 output = write_xml(
 343 |                     parsed_files, docs, {f.file_path: f for f in annotated_files}, folder_tree_str
 344 |                 )
 345 |         except Exception as e:
 346 |             raise OutputError(f"Error generating {config.format} output: {str(e)}")
 349 |         if not config.disable_copy:
 350 |             try:
 351 |                 import pyperclip
 353 |                 pyperclip.copy(output)
 354 |                 print("[CodeConCat] Output copied to clipboard")
 355 |             except ImportError:
 356 |                 print("[CodeConCat] Warning: pyperclip not installed, skipping clipboard copy")
 357 |             except Exception as e:
 358 |                 print(f"[CodeConCat] Warning: Failed to copy to clipboard: {str(e)}")
 360 |     except CodeConcatError as e:
 361 |         print(f"[CodeConCat] Error: {str(e)}")
 362 |         raise
 363 |     except Exception as e:
 364 |         print(f"[CodeConCat] Unexpected error: {str(e)}")
 365 |         raise
 368 | def run_codeconcat_in_memory(config: CodeConCatConfig) -> str:
 370 |     try:
 371 |         if config.disable_copy is None:
 372 |             config.disable_copy = True  # Always disable clipboard in memory mode
 375 |         if config.github_url:
 376 |             code_files = collect_github_files(config)
 377 |         else:
 378 |             code_files = collect_local_files(config.target_path, config)
 380 |         if not code_files:
 381 |             raise FileProcessingError("No files found to process")
 384 |         folder_tree_str = ""
 385 |         if not config.disable_tree:
 386 |             folder_tree_str = generate_folder_tree(config.target_path, config)
 389 |         parsed_files = parse_code_files([f.file_path for f in code_files], config)
 390 |         if not parsed_files:
 391 |             raise FileProcessingError("No files were successfully parsed")
 394 |         docs = []
 395 |         if config.extract_docs:
 396 |             docs = extract_docs([f.file_path for f in code_files], config)
 399 |         annotated_files = []
 400 |         if not config.disable_annotations:
 401 |             for file in parsed_files:
 402 |                 try:
 403 |                     annotated = annotate(file, config)
 404 |                     annotated_files.append(annotated)
 405 |                 except Exception as e:
 406 |                     print(f"Warning: Failed to annotate {file.file_path}: {str(e)}")
 408 |                     annotated_files.append(
 409 |                         AnnotatedFileData(
 410 |                             file_path=file.file_path,
 411 |                             language=file.language,
 412 |                             content=file.content,
 413 |                             annotated_content=file.content,
 414 |                             summary="",
 415 |                             tags=[],
 416 |                         )
 417 |                     )
 418 |         else:
 419 |             for file in parsed_files:
 420 |                 annotated_files.append(
 421 |                     AnnotatedFileData(
 422 |                         file_path=file.file_path,
 423 |                         language=file.language,
 424 |                         content=file.content,
 425 |                         annotated_content=file.content,
 426 |                         summary="",
 427 |                         tags=[],
 428 |                     )
 429 |                 )
 432 |         if config.format == "markdown":
 433 |             return write_markdown(annotated_files, docs, config, folder_tree_str)
 434 |         elif config.format == "json":
 435 |             return write_json(annotated_files, docs, config, folder_tree_str)
 436 |         elif config.format == "xml":
 437 |             return write_xml(
 438 |                 parsed_files, docs, {f.file_path: f for f in annotated_files}, folder_tree_str
 439 |             )
 440 |         else:
 441 |             raise ConfigurationError(f"Invalid format: {config.format}")
 443 |     except Exception as e:
 444 |         error_msg = f"Error processing code: {str(e)}"
 445 |         print(f"[CodeConCat] {error_msg}")
 446 |         raise CodeConcatError(error_msg) from e
 449 | def main():
 450 |     cli_entry_point()
 453 | if __name__ == "__main__":
 454 |     main()
```

---
### File: ./codeconcat/config/config_loader.py
#### Summary
```
File: config_loader.py
Language: python
```

```python
   1 | import logging
   2 | import os
   3 | from typing import Any, Dict
   5 | import yaml
   7 | from codeconcat.base_types import CodeConCatConfig
  10 | def load_config(cli_args: Dict[str, Any]) -> CodeConCatConfig:
  12 |     Load and merge configuration from .codeconcat.yml (if exists) and CLI args.
  13 |     CLI args take precedence over the config file.
  16 |     config_dict = {
  17 |         "target_path": cli_args.get("target_path", "."),
  18 |         "github_url": cli_args.get("github"),
  19 |         "github_token": cli_args.get("github_token"),
  20 |         "github_ref": cli_args.get("ref"),
  21 |         "include_languages": cli_args.get("include_languages", []),
  22 |         "exclude_languages": cli_args.get("exclude_languages", []),
  23 |         "include_paths": cli_args.get("include", []),
  24 |         "exclude_paths": cli_args.get("exclude", []),
  25 |         "extract_docs": cli_args.get("docs", False),
  26 |         "merge_docs": cli_args.get("merge_docs", False),
  27 |         "output": cli_args.get("output", "code_concat_output.md"),
  28 |         "format": cli_args.get("format", "markdown"),
  29 |         "max_workers": cli_args.get("max_workers", 2),
  30 |         "disable_tree": cli_args.get("no_tree", False),
  31 |         "disable_copy": cli_args.get("no_copy", False),
  32 |         "disable_annotations": cli_args.get("no_annotations", False),
  33 |         "disable_symbols": cli_args.get("no_symbols", False),
  34 |         "disable_ai_context": cli_args.get("no_ai_context", False),
  35 |     }
  38 |     yaml_config = {}
  39 |     target_path = cli_args.get("target_path", ".")
  40 |     config_path = os.path.join(target_path, ".codeconcat.yml")
  41 |     if os.path.exists(config_path):
  42 |         try:
  43 |             with open(config_path, "r", encoding="utf-8") as f:
  44 |                 yaml_config = yaml.safe_load(f) or {}
  45 |         except Exception as e:
  46 |             logging.error(f"Failed to load .codeconcat.yml: {e}")
  47 |             yaml_config = {}
  50 |     merged = {**yaml_config, **config_dict}
  52 |     try:
  53 |         return CodeConCatConfig(**merged)
  54 |     except TypeError as e:
  55 |         logging.error(f"Failed to create config: {e}")
  56 |         logging.error(
  57 |             f"Available fields in CodeConCatConfig: {CodeConCatConfig.__dataclass_fields__.keys()}"
  58 |         )
  59 |         logging.error(f"Attempted fields: {merged.keys()}")
  60 |         raise
  63 | def read_config_file(path: str) -> Dict[str, Any]:
  64 |     if not os.path.exists(path):
  65 |         return {}
  66 |     try:
  67 |         with open(path, "r", encoding="utf-8") as f:
  68 |             data = yaml.safe_load(f)
  69 |             if isinstance(data, dict):
  70 |                 return data
  71 |     except Exception:
  72 |         pass
  73 |     return {}
  76 | def apply_dict_to_config(data: Dict[str, Any], config: CodeConCatConfig) -> None:
  77 |     for key, value in data.items():
  78 |         if hasattr(config, key):
  79 |             if key == "custom_extension_map" and isinstance(value, dict):
  80 |                 config.custom_extension_map.update(value)
  81 |             else:
  82 |                 setattr(config, key, value)
```

---
### File: ./codeconcat/config/__init__.py
#### Summary
```
File: __init__.py
Language: python
```

```python

```

---
### File: ./codeconcat/transformer/__init__.py
#### Summary
```
File: __init__.py
Language: python
```

```python

```

---
### File: ./codeconcat/transformer/annotator.py
#### Summary
```
File: annotator.py
Language: python
```

```python
   1 | from codeconcat.base_types import AnnotatedFileData, CodeConCatConfig, ParsedFileData
   4 | def annotate(parsed_data: ParsedFileData, config: CodeConCatConfig) -> AnnotatedFileData:
   5 |     pieces = []
   6 |     pieces.append(f"## File: {parsed_data.file_path}\n")
   9 |     functions = []
  10 |     classes = []
  11 |     structs = []
  12 |     symbols = []
  14 |     for decl in parsed_data.declarations:
  15 |         if decl.kind == "function":
  16 |             functions.append(decl.name)
  17 |         elif decl.kind == "class":
  18 |             classes.append(decl.name)
  19 |         elif decl.kind == "struct":
  20 |             structs.append(decl.name)
  21 |         elif decl.kind == "symbol":
  22 |             symbols.append(decl.name)
  25 |     if functions:
  26 |         pieces.append("### Functions\n")
  27 |         for name in functions:
  28 |             pieces.append(f"- {name}\n")
  30 |     if classes:
  31 |         pieces.append("### Classes\n")
  32 |         for name in classes:
  33 |             pieces.append(f"- {name}\n")
  35 |     if structs:
  36 |         pieces.append("### Structs\n")
  37 |         for name in structs:
  38 |             pieces.append(f"- {name}\n")
  40 |     if symbols:
  41 |         pieces.append("### Symbols\n")
  42 |         for name in symbols:
  43 |             pieces.append(f"- {name}\n")
  45 |     pieces.append(f"```{parsed_data.language}\n{parsed_data.content}\n```\n")
  48 |     summary_parts = []
  49 |     if functions:
  50 |         summary_parts.append(f"{len(functions)} functions")
  51 |     if classes:
  52 |         summary_parts.append(f"{len(classes)} classes")
  53 |     if structs:
  54 |         summary_parts.append(f"{len(structs)} structs")
  55 |     if symbols:
  56 |         summary_parts.append(f"{len(symbols)} symbols")
  58 |     summary = f"Contains {', '.join(summary_parts)}" if summary_parts else "No declarations found"
  61 |     tags = []
  62 |     if functions:
  63 |         tags.append("has_functions")
  64 |     if classes:
  65 |         tags.append("has_classes")
  66 |     if structs:
  67 |         tags.append("has_structs")
  68 |     if symbols:
  69 |         tags.append("has_symbols")
  70 |     tags.append(parsed_data.language)
  72 |     return AnnotatedFileData(
  73 |         file_path=parsed_data.file_path,
  74 |         language=parsed_data.language,
  75 |         content=parsed_data.content,
  76 |         annotated_content="".join(pieces),
  77 |         summary=summary,
  78 |         tags=tags,
  79 |     )
```

---
### File: ./codeconcat/processor/security_types.py
#### Summary
```
File: security_types.py
Language: python
```

```python
   3 | from dataclasses import dataclass
   6 | @dataclass
   7 | class SecurityIssue:
  10 |     line_number: int
  11 |     line_content: str
  12 |     issue_type: str
  13 |     severity: str
  14 |     description: str
```

---
### File: ./codeconcat/processor/content_processor.py
#### Summary
```
File: content_processor.py
Language: python
```

```python
   3 | import os
   4 | from typing import List
   6 | from codeconcat.base_types import CodeConCatConfig, ParsedFileData, SecurityIssue
   7 | from codeconcat.processor.token_counter import TokenStats
  10 | def process_file_content(content: str, config: CodeConCatConfig) -> str:
  12 |     lines = content.split("\n")
  13 |     processed_lines = []
  15 |     for i, line in enumerate(lines):
  17 |         if config.remove_empty_lines and not line.strip():
  18 |             continue
  21 |         if config.remove_comments:
  22 |             stripped = line.strip()
  23 |             if (
  24 |                 stripped.startswith("#")
  25 |                 or stripped.startswith("//")
  26 |                 or stripped.startswith("/*")
  27 |                 or stripped.startswith("*")
  28 |                 or stripped.startswith('"""')
  29 |                 or stripped.startswith("'''")
  30 |                 or stripped.endswith("*/")
  31 |             ):
  32 |                 continue
  35 |         if config.show_line_numbers:
  36 |             line = f"{i+1:4d} | {line}"
  38 |         processed_lines.append(line)
  40 |     return "\n".join(processed_lines)
  43 | def generate_file_summary(file_data: ParsedFileData) -> str:
  45 |     summary = []
  46 |     summary.append(f"File: {os.path.basename(file_data.file_path)}")
  47 |     summary.append(f"Language: {file_data.language}")
  49 |     if file_data.token_stats:
  50 |         summary.append("Token Counts:")
  51 |         summary.append(f"  - GPT-3.5: {file_data.token_stats.gpt3_tokens:,}")
  52 |         summary.append(f"  - GPT-4: {file_data.token_stats.gpt4_tokens:,}")
  53 |         summary.append(f"  - Davinci: {file_data.token_stats.davinci_tokens:,}")
  54 |         summary.append(f"  - Claude: {file_data.token_stats.claude_tokens:,}")
  56 |     if file_data.security_issues:
  57 |         summary.append("\nSecurity Issues:")
  58 |         for issue in file_data.security_issues:
  59 |             summary.append(f"  - {issue.issue_type} (Line {issue.line_number})")
  60 |             summary.append(f"    {issue.line_content}")
  62 |     if file_data.declarations:
  63 |         summary.append("\nDeclarations:")
  64 |         for decl in file_data.declarations:
  65 |             summary.append(
  66 |                 f"  - {decl.kind}: {decl.name} (lines {decl.start_line}-{decl.end_line})"
  67 |             )
  69 |     return "\n".join(summary)
  72 | def generate_directory_structure(file_paths: List[str]) -> str:
  74 |     structure = {}
  75 |     for path in file_paths:
  76 |         parts = path.split(os.sep)
  77 |         current = structure
  78 |         for part in parts[:-1]:
  79 |             if part not in current:
  80 |                 current[part] = {}
  81 |             current = current[part]
  82 |         current[parts[-1]] = None
  84 |     def print_tree(node: dict, prefix: str = "", is_last: bool = True) -> List[str]:
  85 |         lines = []
  86 |         if node is None:
  87 |             return lines
  89 |         items = list(node.items())
  90 |         for i, (name, subtree) in enumerate(items):
  91 |             is_last_item = i == len(items) - 1
  92 |             lines.append(f"{prefix}{'└── ' if is_last_item else '├── '}{name}")
  93 |             if subtree is not None:
  94 |                 extension = "    " if is_last_item else "│   "
  95 |                 lines.extend(print_tree(subtree, prefix + extension, is_last_item))
  96 |         return lines
  98 |     return "\n".join(print_tree(structure))
```

---
### File: ./codeconcat/processor/token_counter.py
#### Summary
```
File: token_counter.py
Language: python
```

```python
   3 | from dataclasses import dataclass
   4 | from typing import Dict
   6 | import tiktoken
   9 | @dataclass
  10 | class TokenStats:
  13 |     gpt3_tokens: int
  14 |     gpt4_tokens: int
  15 |     davinci_tokens: int
  16 |     claude_tokens: int
  20 | _ENCODER_CACHE: Dict[str, tiktoken.Encoding] = {}
  23 | def get_encoder(model: str = "gpt-3.5-turbo") -> tiktoken.Encoding:
  25 |     if model not in _ENCODER_CACHE:
  26 |         _ENCODER_CACHE[model] = tiktoken.encoding_for_model(model)
  27 |     return _ENCODER_CACHE[model]
  30 | def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
  32 |     encoder = get_encoder(model)
  33 |     return len(encoder.encode(text))
  36 | def get_token_stats(text: str) -> TokenStats:
  38 |     return TokenStats(
  39 |         gpt3_tokens=count_tokens(text, "gpt-3.5-turbo"),
  40 |         gpt4_tokens=count_tokens(text, "gpt-4"),
  41 |         davinci_tokens=count_tokens(text, "text-davinci-003"),
  42 |         claude_tokens=int(len(text.encode("utf-8")) / 4),  # Rough approximation for Claude
  43 |     )
```

---
### File: ./codeconcat/processor/__init__.py
#### Summary
```
File: __init__.py
Language: python
```

```python
   3 | from codeconcat.processor.content_processor import (
   4 |     generate_directory_structure,
   5 |     generate_file_summary,
   6 |     process_file_content,
   7 | )
   9 | __all__ = ["process_file_content", "generate_file_summary", "generate_directory_structure"]
```

---
### File: ./codeconcat/processor/security_processor.py
#### Summary
```
File: security_processor.py
Language: python
```

```python
   3 | import re
   4 | from typing import Any, Dict, List, Tuple
   6 | from codeconcat.processor.security_types import SecurityIssue
   9 | class SecurityProcessor:
  13 |     PATTERNS = {
  14 |         "aws_key": (
  15 |             r'(?i)aws[_\-\s]*(?:access)?[_\-\s]*key[_\-\s]*(?:id)?["\'\s:=]+[A-Za-z0-9/\+=]{20,}',
  16 |             "AWS Key",
  17 |         ),
  18 |         "aws_secret": (
  19 |             r'(?i)aws[_\-\s]*secret[_\-\s]*(?:access)?[_\-\s]*key["\'\s:=]+[A-Za-z0-9/\+=]{40,}',
  20 |             "AWS Secret Key",
  21 |         ),
  22 |         "github_token": (
  23 |             r'(?i)(?:github|gh)[_\-\s]*(?:token|key)["\'\s:=]+[A-Za-z0-9_\-]{36,}',
  24 |             "GitHub Token",
  25 |         ),
  26 |         "generic_api_key": (r'(?i)api[_\-\s]*key["\'\s:=]+[A-Za-z0-9_\-]{16,}', "API Key"),
  27 |         "generic_secret": (
  28 |             r'(?i)(?:secret|token|key|password|pwd)["\'\s:=]+[A-Za-z0-9_\-]{16,}',
  29 |             "Generic Secret",
  30 |         ),
  31 |         "private_key": (
  32 |             r"(?i)-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY[^-]*-----.*?-----END",
  33 |             "Private Key",
  34 |         ),
  35 |         "basic_auth": (
  36 |             r'(?i)(?:authorization|auth)\s*[:=]\s*["\']*basic\s+[A-Za-z0-9+/=]+["\']*',
  37 |             "Basic Authentication",
  38 |         ),
  39 |         "bearer_token": (
  40 |             r'(?i)(?:authorization|auth)\s*[:=]\s*["\']*bearer\s+[A-Za-z0-9._\-]+["\']*',
  41 |             "Bearer Token",
  42 |         ),
  43 |     }
  46 |     IGNORE_PATTERNS = [
  47 |         r"(?i)example|sample|test|dummy|fake|mock",
  48 |         r"your.*key.*here",
  49 |         r"xxx+",
  50 |         r"[A-Za-z0-9]{16,}\.example\.com",
  51 |     ]
  53 |     @classmethod
  54 |     def scan_content(cls, content: str, file_path: str) -> List[SecurityIssue]:
  56 |         Scan content for potential security issues.
  58 |         Args:
  59 |             content: The content to scan
  60 |             file_path: Path to the file being scanned (for context)
  62 |         Returns:
  63 |             List of SecurityIssue instances
  65 |         issues = []
  66 |         lines = content.split("\n")
  68 |         for line_num, line in enumerate(lines, 1):
  70 |             if not line.strip():
  71 |                 continue
  74 |             if any(re.search(pattern, line) for pattern in cls.IGNORE_PATTERNS):
  75 |                 continue
  78 |             for pattern_name, (pattern, issue_type) in cls.PATTERNS.items():
  79 |                 if re.search(pattern, line):
  81 |                     masked_line = cls._mask_sensitive_data(line, pattern)
  83 |                     issues.append(
  84 |                         SecurityIssue(
  85 |                             line_number=line_num,
  86 |                             line_content=masked_line,
  87 |                             issue_type=issue_type,
  88 |                             severity="HIGH",
  89 |                             description=f"Potential {issue_type} found in {file_path}",
  90 |                         )
  91 |                     )
  93 |         return issues
  95 |     @staticmethod
  96 |     def _mask_sensitive_data(line: str, pattern: str) -> str:
  99 |         def mask_match(match):
 100 |             return match.group()[:4] + "*" * (len(match.group()) - 8) + match.group()[-4:]
 102 |         return re.sub(pattern, mask_match, line)
 104 |     @classmethod
 105 |     def format_issues(cls, issues: List[SecurityIssue]) -> str:
 107 |         if not issues:
 108 |             return "No security issues found."
 110 |         formatted = ["Security Scan Results:", "=" * 20]
 111 |         for issue in issues:
 112 |             formatted.extend(
 113 |                 [
 114 |                     f"\nIssue Type: {issue.issue_type}",
 115 |                     f"Severity: {issue.severity}",
 116 |                     f"Line {issue.line_number}: {issue.line_content}",
 117 |                     f"Description: {issue.description}",
 118 |                     "-" * 20,
 119 |                 ]
 120 |             )
 122 |         return "\n".join(formatted)
```

---
### File: ./codeconcat/collector/github_collector.py
#### Summary
```
File: github_collector.py
Language: python
```

```python
   1 | import os
   2 | import re
   3 | import shutil
   4 | import subprocess
   5 | import tempfile
   6 | from typing import List, Optional, Tuple
   8 | from github import Github
   9 | from github.ContentFile import ContentFile
  10 | from github.Repository import Repository
  12 | from codeconcat.base_types import CodeConCatConfig
  13 | from codeconcat.collector.local_collector import collect_local_files
  16 | def parse_github_url(url: str) -> Tuple[str, str, Optional[str]]:
  19 |     if "/" in url and not url.startswith("http"):
  20 |         parts = url.split("/")
  21 |         owner = parts[0]
  22 |         repo = parts[1]
  23 |         ref = parts[2] if len(parts) > 2 else None
  24 |         return owner, repo, ref
  27 |     match = re.match(r"https?://github\.com/([^/]+)/([^/]+)(?:/tree/([^/]+))?", url)
  28 |     if match:
  29 |         return match.group(1), match.group(2), match.group(3)
  31 |     raise ValueError(
  32 |         "Invalid GitHub URL or shorthand. Use format 'owner/repo', 'owner/repo/branch', "
  33 |         "or 'https://github.com/owner/repo'"
  34 |     )
  37 | def collect_github_files(github_url: str, config: CodeConCatConfig) -> List[str]:
  38 |     owner, repo_name, url_ref = parse_github_url(github_url)
  41 |     target_ref = config.ref or url_ref or "main"
  43 |     g = Github(config.github_token) if config.github_token else Github()
  44 |     repo = g.get_repo(f"{owner}/{repo_name}")
  46 |     try:
  48 |         repo.get_commit(target_ref)
  49 |     except:
  50 |         try:
  52 |             branches = [b.name for b in repo.get_branches()]
  53 |             tags = [t.name for t in repo.get_tags()]
  54 |             if target_ref not in branches + tags:
  55 |                 raise ValueError(
  56 |                     f"Reference '{target_ref}' not found. Available branches: {branches}, "
  57 |                     f"tags: {tags}"
  58 |                 )
  59 |         except Exception as e:
  60 |             raise ValueError(f"Error accessing repository: {str(e)}")
  62 |     contents = []
  63 |     for content in repo.get_contents("", ref=target_ref):
  64 |         if content.type == "file":
  65 |             contents.append(content.decoded_content.decode("utf-8"))
  66 |         elif content.type == "dir":
  67 |             contents.extend(_collect_dir_contents(repo, content.path, target_ref))
  69 |     return contents
  72 | def _collect_dir_contents(repo: Repository, path: str, ref: str) -> List[str]:
  74 |     contents = []
  75 |     for content in repo.get_contents(path, ref=ref):
  76 |         if content.type == "file":
  77 |             contents.append(content.decoded_content.decode("utf-8"))
  78 |         elif content.type == "dir":
  79 |             contents.extend(_collect_dir_contents(repo, content.path, ref))
  80 |     return contents
  83 | def collect_github_files_legacy(github_url: str, config: CodeConCatConfig) -> List[str]:
  84 |     temp_dir = tempfile.mkdtemp(prefix="codeconcat_github_")
  85 |     try:
  86 |         clone_url = build_clone_url(github_url, config.github_token)
  87 |         print(f"[CodeConCat] Cloning from {clone_url} into {temp_dir}")
  88 |         subprocess.run(["git", "clone", "--depth=1", clone_url, temp_dir], check=True)
  90 |         file_paths = collect_local_files(temp_dir, config)
  91 |         return file_paths
  93 |     except subprocess.CalledProcessError as e:
  94 |         raise RuntimeError(f"Failed to clone GitHub repo: {e}") from e
  95 |     finally:
  98 |         pass
 101 | def build_clone_url(github_url: str, token: str) -> str:
 102 |     if token and "https://" in github_url:
 103 |         parts = github_url.split("https://", 1)
 104 |         return f"https://{token}@{parts[1]}"
 105 |     return github_url
```

---
### File: ./codeconcat/collector/__init__.py
#### Summary
```
File: __init__.py
Language: python
```

```python

```

---
### File: ./codeconcat/collector/local_collector.py
#### Summary
```
File: local_collector.py
Language: python
```

```python
   1 | import fnmatch
   2 | import logging
   3 | import os
   4 | import re
   5 | from concurrent.futures import ThreadPoolExecutor
   6 | from typing import List
   7 | from pathlib import Path
   8 | from codeconcat.base_types import CodeConCatConfig, ParsedFileData
   9 | from pathspec import PathSpec
  10 | from pathspec.patterns import GitWildMatchPattern
  13 | logger = logging.getLogger(__name__)
  14 | logger.setLevel(logging.WARNING)
  17 | ch = logging.StreamHandler()
  18 | ch.setLevel(logging.DEBUG)
  21 | formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
  22 | ch.setFormatter(formatter)
  25 | logger.addHandler(ch)
  27 | DEFAULT_EXCLUDES = [
  29 |     ".git/",  # Match the .git directory itself
  30 |     ".git/**",  # Match contents of .git directory
  31 |     "**/.git/",  # Match .git directory anywhere in tree
  32 |     "**/.git/**",  # Match contents of .git directory anywhere in tree
  33 |     ".gitignore",
  34 |     "**/.gitignore",
  36 |     ".DS_Store",
  37 |     "**/.DS_Store",
  38 |     "Thumbs.db",
  39 |     "**/*.swp",
  40 |     "**/*.swo",
  41 |     ".idea/**",
  42 |     ".vscode/**",
  44 |     "*.yml",
  45 |     "./*.yml",
  46 |     "**/*.yml",
  47 |     "*.yaml",
  48 |     "./*.yaml",
  49 |     "**/*.yaml",
  50 |     ".codeconcat.yml",
  52 |     "node_modules/",
  53 |     "**/node_modules/",
  54 |     "**/node_modules/**",
  55 |     "build/",
  56 |     "**/build/",
  57 |     "**/build/**",
  58 |     "dist/",
  59 |     "**/dist/",
  60 |     "**/dist/**",
  62 |     ".next/",
  63 |     "**/.next/",
  64 |     "**/.next/**",
  65 |     "**/static/chunks/**",
  66 |     "**/server/chunks/**",
  67 |     "**/BUILD_ID",
  68 |     "**/trace",
  69 |     "**/*.map",
  70 |     "**/webpack-*.js",
  71 |     "**/manifest*.js",
  72 |     "**/server-reference-manifest.js",
  73 |     "**/middleware-manifest.js",
  74 |     "**/client-reference-manifest.js",
  75 |     "**/webpack-runtime.js",
  76 |     "**/server-reference-manifest.js",
  77 |     "**/middleware-build-manifest.js",
  78 |     "**/middleware-react-loadable-manifest.js",
  79 |     "**/server-reference-manifest.js",
  80 |     "**/interception-route-rewrite-manifest.js",
  81 |     "**/next-font-manifest.js",
  82 |     "**/polyfills-*.js",
  83 |     "**/main-*.js",
  84 |     "**/framework-*.js",
  86 |     "package-lock.json",
  87 |     "**/package-lock.json",
  88 |     "yarn.lock",
  89 |     "**/yarn.lock",
  90 |     "pnpm-lock.yaml",
  91 |     "**/pnpm-lock.yaml",
  93 |     ".cache/",
  94 |     "**/.cache/",
  95 |     "**/.cache/**",
  96 |     "tmp/",
  97 |     "**/tmp/",
  98 |     "**/tmp/**",
 100 |     "coverage/",
 101 |     "**/coverage/",
 102 |     "**/coverage/**",
 104 |     ".env",
 105 |     "**/.env",
 106 |     ".env.*",
 107 |     "**/.env.*",
 108 | ]
 111 | def get_gitignore_spec(root_path: str) -> PathSpec:
 113 |     Read .gitignore file and create a PathSpec for matching.
 115 |     Args:
 116 |         root_path: Root directory to search for .gitignore
 118 |     Returns:
 119 |         PathSpec object for matching paths against .gitignore patterns
 121 |     gitignore_path = os.path.join(root_path, ".gitignore")
 122 |     patterns = []
 124 |     if os.path.exists(gitignore_path):
 125 |         with open(gitignore_path, "r") as f:
 126 |             patterns = [line.strip() for line in f if line.strip() and not line.startswith("#")]
 129 |     patterns.extend(
 130 |         [
 131 |             "**/__pycache__/**",
 132 |             "**/*.pyc",
 133 |             "**/.git/**",
 134 |             "**/node_modules/**",
 135 |             "**/.pytest_cache/**",
 136 |             "**/.coverage",
 137 |             "**/build/**",
 138 |             "**/dist/**",
 139 |             "**/*.egg-info/**",
 140 |         ]
 141 |     )
 143 |     return PathSpec.from_lines(GitWildMatchPattern, patterns)
 146 | def should_include_file(
 147 |     file_path: str, config: CodeConCatConfig, gitignore_spec: PathSpec = None
 148 | ) -> bool:
 150 |     Check if a file should be included based on configuration and .gitignore.
 152 |     Args:
 153 |         file_path: Path to the file
 154 |         config: Configuration object
 155 |         gitignore_spec: PathSpec object for .gitignore matching
 157 |     Returns:
 158 |         bool: True if file should be included, False otherwise
 161 |     rel_path = os.path.relpath(file_path, config.target_path)
 164 |     if gitignore_spec and gitignore_spec.match_file(rel_path):
 165 |         return False
 168 |     if config.exclude_paths:
 169 |         for pattern in config.exclude_paths:
 171 |             path_parts = Path(rel_path).parts
 172 |             if any(fnmatch.fnmatch(os.path.join(*path_parts[:i+1]), pattern) 
 173 |                   for i in range(len(path_parts))):
 174 |                 return False
 176 |     if config.include_paths:
 177 |         return any(fnmatch.fnmatch(rel_path, pattern) for pattern in config.include_paths)
 179 |     return True
 182 | def collect_local_files(root_path: str, config: CodeConCatConfig):
 185 |     logger.debug(f"[CodeConCat] Collecting files from: {root_path}")
 188 |     if not os.path.exists(root_path):
 189 |         raise FileNotFoundError(f"Path does not exist: {root_path}")
 191 |     gitignore_spec = get_gitignore_spec(root_path)
 194 |     with ThreadPoolExecutor(max_workers=config.max_workers) as executor:
 195 |         futures = []
 197 |         for dirpath, dirnames, filenames in os.walk(root_path):
 199 |             if should_skip_dir(dirpath, config.exclude_paths):
 200 |                 dirnames.clear()  # Clear dirnames to skip subdirectories
 201 |                 continue
 204 |             for filename in filenames:
 205 |                 file_path = os.path.join(dirpath, filename)
 206 |                 futures.append(executor.submit(process_file, file_path, config, gitignore_spec))
 209 |         results = [f.result() for f in futures if f.result()]
 211 |     if not results:
 212 |         logger.warning("[CodeConCat] No files found matching the criteria")
 213 |     else:
 214 |         logger.info(f"[CodeConCat] Collected {len(results)} files")
 216 |     return results
 219 | def process_file(file_path: str, config: CodeConCatConfig, gitignore_spec: PathSpec):
 221 |     try:
 222 |         if not should_include_file(file_path, config, gitignore_spec):
 223 |             return None
 225 |         if is_binary_file(file_path):
 226 |             logger.debug(f"[CodeConCat] Skipping binary file: {file_path}")
 227 |             return None
 229 |         with open(file_path, "r", encoding="utf-8") as f:
 230 |             content = f.read()
 232 |         ext = os.path.splitext(file_path)[1].lstrip(".")
 233 |         language = ext_map(ext, config)
 235 |         logger.debug(f"[CodeConCat] Processed file: {file_path} ({language})")
 236 |         return ParsedFileData(
 237 |             file_path=file_path,
 238 |             language=language,
 239 |             content=content,
 240 |             declarations=[],  # We'll fill this in during parsing phase
 241 |         )
 243 |     except UnicodeDecodeError:
 244 |         logger.debug(f"[CodeConCat] Skipping non-text file: {file_path}")
 245 |         return None
 246 |     except Exception as e:
 247 |         logger.error(f"[CodeConCat] Error processing {file_path}: {str(e)}")
 248 |         return None
 251 | def should_skip_dir(dirpath: str, user_excludes: List[str]) -> bool:
 253 |     all_excludes = DEFAULT_EXCLUDES + (user_excludes or [])
 254 |     logger.debug(f"Checking directory: {dirpath} against patterns: {all_excludes}")
 257 |     if os.path.isabs(dirpath):
 258 |         try:
 259 |             rel_path = os.path.relpath(dirpath, os.getcwd())
 260 |         except ValueError:
 261 |             rel_path = dirpath
 262 |     else:
 263 |         rel_path = dirpath
 266 |     rel_path = rel_path.replace(os.sep, "/").strip("/")
 269 |     for pattern in all_excludes:
 270 |         if matches_pattern(rel_path, pattern):
 271 |             logger.debug(f"Excluding directory {rel_path} due to pattern {pattern}")
 272 |             return True
 275 |     path_parts = [p for p in rel_path.split("/") if p]
 276 |     current_path = ""
 277 |     for part in path_parts:
 278 |         if current_path:
 279 |             current_path += "/"
 280 |         current_path += part
 282 |         for pattern in all_excludes:
 284 |             if matches_pattern(current_path, pattern) or matches_pattern(
 285 |                 current_path + "/", pattern
 286 |             ):
 287 |                 logger.debug(
 288 |                     f"Excluding directory {rel_path} due to parent {current_path} matching pattern {pattern}"
 289 |                 )
 290 |                 return True
 292 |     return False
 295 | def matches_pattern(path_str: str, pattern: str) -> bool:
 298 |     path_str = path_str.replace(os.sep, "/").strip("/")
 299 |     pattern = pattern.replace(os.sep, "/").strip("/")
 302 |     if pattern == "":
 303 |         return path_str == ""
 306 |     pattern = pattern.replace(".", "\\.")  # Escape dots
 307 |     pattern = pattern.replace("**", "__DOUBLE_STAR__")  # Preserve **
 308 |     pattern = pattern.replace("*", "[^/]*")  # Single star doesn't cross directories
 309 |     pattern = pattern.replace("__DOUBLE_STAR__", ".*")  # ** can cross directories
 310 |     pattern = pattern.replace("?", "[^/]")  # ? matches single character
 313 |     if pattern.endswith("/"):
 314 |         pattern = pattern + ".*"  # Match anything after directory
 317 |     if pattern.startswith("/"):
 318 |         pattern = "^" + pattern[1:]  # Keep absolute path requirement
 319 |     elif pattern.startswith("**/"):
 320 |         pattern = ".*" + pattern[2:]  # Allow matching anywhere in path
 321 |     else:
 322 |         pattern = "^" + pattern  # Anchor to start by default
 324 |     if not pattern.endswith("$"):
 325 |         pattern += "$"  # Always anchor to end
 328 |     try:
 329 |         return bool(re.match(pattern, path_str))
 330 |     except re.error as e:
 331 |         logger.warning(f"Invalid pattern {pattern}: {str(e)}")
 332 |         return False
 335 | def ext_map(ext: str, config: CodeConCatConfig) -> str:
 337 |     if ext in config.custom_extension_map:
 338 |         return config.custom_extension_map[ext]
 341 |     non_code_exts = {
 343 |         "svg",
 344 |         "png",
 345 |         "jpg",
 346 |         "jpeg",
 347 |         "gif",
 348 |         "ico",
 349 |         "webp",
 351 |         "woff",
 352 |         "woff2",
 353 |         "ttf",
 354 |         "eot",
 355 |         "otf",
 357 |         "pdf",
 358 |         "doc",
 359 |         "docx",
 360 |         "xls",
 361 |         "xlsx",
 363 |         "zip",
 364 |         "tar",
 365 |         "gz",
 366 |         "tgz",
 367 |         "7z",
 368 |         "rar",
 370 |         "map",
 371 |         "min.js",
 372 |         "min.css",
 373 |         "bundle.js",
 374 |         "bundle.css",
 375 |         "chunk.js",
 376 |         "chunk.css",
 377 |         "nft.json",
 378 |         "rsc",
 379 |         "meta",
 381 |         "mp3",
 382 |         "mp4",
 383 |         "wav",
 384 |         "avi",
 385 |         "mov",
 386 |     }
 388 |     if ext.lower() in non_code_exts:
 389 |         return "non-code"
 392 |     code_exts = {
 394 |         "py": "python",
 395 |         "pyi": "python",
 397 |         "js": "javascript",
 398 |         "jsx": "javascript",
 399 |         "ts": "typescript",
 400 |         "tsx": "typescript",
 401 |         "mjs": "javascript",
 403 |         "r": "r",
 404 |         "jl": "julia",
 405 |         "cpp": "cpp",
 406 |         "hpp": "cpp",
 407 |         "cxx": "cpp",
 408 |         "c": "c",
 409 |         "h": "c",
 411 |         "md": "doc",
 412 |         "rst": "doc",
 413 |         "txt": "doc",
 414 |         "rmd": "doc",
 415 |     }
 417 |     return code_exts.get(ext.lower(), "unknown")
 420 | def is_binary_file(file_path: str) -> bool:
 422 |     try:
 423 |         with open(file_path, "tr") as check_file:
 424 |             check_file.readline()
 425 |             return False
 426 |     except UnicodeDecodeError:
 427 |         return True
```

---
### File: ./codeconcat/parser/doc_extractor.py
#### Summary
```
File: doc_extractor.py
Language: python
```

```python
   1 | import os
   2 | from concurrent.futures import ThreadPoolExecutor
   3 | from typing import List
   5 | from codeconcat.base_types import CodeConCatConfig, ParsedDocData
   8 | def extract_docs(file_paths: List[str], config: CodeConCatConfig) -> List[ParsedDocData]:
   9 |     doc_paths = [fp for fp in file_paths if is_doc_file(fp, config.doc_extensions)]
  11 |     with ThreadPoolExecutor(max_workers=config.max_workers) as executor:
  12 |         results = list(executor.map(lambda fp: parse_doc_file(fp), doc_paths))
  13 |     return results
  16 | def is_doc_file(file_path: str, doc_exts: List[str]) -> bool:
  17 |     ext = os.path.splitext(file_path)[1].lower()
  18 |     return ext in doc_exts
  21 | def parse_doc_file(file_path: str) -> ParsedDocData:
  22 |     ext = os.path.splitext(file_path)[1].lower()
  23 |     content = read_doc_content(file_path)
  24 |     doc_type = ext.lstrip(".")
  25 |     return ParsedDocData(file_path=file_path, doc_type=doc_type, content=content)
  28 | def read_doc_content(file_path: str) -> str:
  29 |     try:
  30 |         with open(file_path, "r", encoding="utf-8", errors="replace") as f:
  31 |             return f.read()
  32 |     except Exception:
  33 |         return ""
```

---
### File: ./codeconcat/parser/file_parser.py
#### Summary
```
File: file_parser.py
Language: python
```

```python
   1 | import os
   2 | from concurrent.futures import ThreadPoolExecutor
   3 | from functools import lru_cache
   4 | from typing import Callable, List, Optional, Tuple
   6 | from codeconcat.base_types import CodeConCatConfig, ParsedFileData
   7 | from codeconcat.parser.language_parsers.base_parser import BaseParser
   8 | from codeconcat.parser.language_parsers.c_parser import parse_c_code
   9 | from codeconcat.parser.language_parsers.cpp_parser import parse_cpp_code
  10 | from codeconcat.parser.language_parsers.csharp_parser import parse_csharp_code
  11 | from codeconcat.parser.language_parsers.go_parser import parse_go
  12 | from codeconcat.parser.language_parsers.java_parser import parse_java
  13 | from codeconcat.parser.language_parsers.js_ts_parser import parse_javascript_or_typescript
  14 | from codeconcat.parser.language_parsers.julia_parser import parse_julia
  15 | from codeconcat.parser.language_parsers.php_parser import parse_php
  16 | from codeconcat.parser.language_parsers.python_parser import parse_python
  17 | from codeconcat.parser.language_parsers.r_parser import parse_r
  18 | from codeconcat.parser.language_parsers.rust_parser import parse_rust
  19 | from codeconcat.processor.token_counter import get_token_stats
  22 | @lru_cache(maxsize=100)
  23 | def _parse_single_file(file_path: str, language: str) -> Optional[ParsedFileData]:
  25 |     Parse a single file with caching. This function is memoized to improve performance
  26 |     when the same file is processed multiple times.
  28 |     Args:
  29 |         file_path: Path to the file to parse
  30 |         language: Programming language of the file
  32 |     Returns:
  33 |         ParsedFileData if successful, None if parsing failed
  35 |     Note:
  36 |         The function is cached based on file_path and language. The cache is cleared
  37 |         when the file content changes (detected by modification time).
  39 |     try:
  40 |         if not os.path.exists(file_path):
  41 |             raise FileNotFoundError(f"File not found: {file_path}")
  43 |         with open(file_path, "r", encoding="utf-8") as f:
  44 |             content = f.read()
  46 |         if language == "python":
  47 |             return parse_python(file_path, content)
  48 |         elif language in ["javascript", "typescript"]:
  49 |             return parse_javascript_or_typescript(file_path, content, language)
  50 |         elif language == "c":
  51 |             return parse_c_code(file_path, content)
  52 |         elif language == "cpp":
  53 |             return parse_cpp_code(file_path, content)
  54 |         elif language == "csharp":
  55 |             return parse_csharp_code(file_path, content)
  56 |         elif language == "go":
  57 |             return parse_go(file_path, content)
  58 |         elif language == "java":
  59 |             return parse_java(file_path, content)
  60 |         elif language == "julia":
  61 |             return parse_julia(file_path, content)
  62 |         elif language == "php":
  63 |             return parse_php(file_path, content)
  64 |         elif language == "r":
  65 |             return parse_r(file_path, content)
  66 |         elif language == "rust":
  67 |             return parse_rust(file_path, content)
  68 |         else:
  69 |             raise ValueError(f"Unsupported language: {language}")
  71 |     except UnicodeDecodeError:
  72 |         raise ValueError(
  73 |             f"Failed to decode {file_path}. File may be binary or use an unsupported encoding."
  74 |         )
  75 |     except Exception as e:
  76 |         raise RuntimeError(f"Error parsing {file_path}: {str(e)}")
  79 | def parse_code_files(file_paths: List[str], config: CodeConCatConfig) -> List[ParsedFileData]:
  81 |     Parse multiple code files with improved error handling and caching.
  83 |     Args:
  84 |         file_paths: List of file paths to parse
  85 |         config: Configuration object
  87 |     Returns:
  88 |         List of successfully parsed files
  90 |     Note:
  91 |         Files that fail to parse are logged with detailed error messages but don't
  92 |         cause the entire process to fail.
  94 |     parsed_files = []
  95 |     errors = []
  97 |     for file_path in file_paths:
  98 |         try:
 100 |             language = determine_language(file_path)
 101 |             if not language:
 102 |                 errors.append(f"Could not determine language for {file_path}")
 103 |                 continue
 106 |             parsed_file = _parse_single_file(file_path, language)
 107 |             if parsed_file:
 108 |                 parsed_files.append(parsed_file)
 110 |         except FileNotFoundError as e:
 111 |             errors.append(f"File not found: {file_path}")
 112 |         except UnicodeDecodeError:
 113 |             errors.append(
 114 |                 f"Failed to decode {file_path}. File may be binary or use an unsupported encoding."
 115 |             )
 116 |         except ValueError as e:
 117 |             errors.append(str(e))
 118 |         except Exception as e:
 119 |             errors.append(f"Unexpected error parsing {file_path}: {str(e)}")
 122 |     if errors:
 123 |         error_summary = "\n".join(errors)
 124 |         print(f"Encountered errors while parsing files:\n{error_summary}")
 126 |     return parsed_files
 129 | @lru_cache(maxsize=100)
 130 | def determine_language(file_path: str) -> Optional[str]:
 132 |     Determine the programming language of a file based on its extension.
 133 |     This function is cached to improve performance.
 135 |     Args:
 136 |         file_path: Path to the file
 138 |     Returns:
 139 |         Language identifier or None if unknown
 142 |     basename = os.path.basename(file_path)
 143 |     ext = os.path.splitext(file_path)[1].lower()
 146 |     r_specific_files = {
 147 |         "DESCRIPTION",  # R package description
 148 |         "NAMESPACE",    # R package namespace
 149 |         ".Rproj",      # RStudio project file
 150 |         "configure",    # R package configuration
 151 |         "configure.win",# R package Windows configuration
 152 |     }
 153 |     if basename in r_specific_files:
 154 |         return None
 157 |     language_map = {
 158 |         ".py": "python",
 159 |         ".js": "javascript",
 160 |         ".ts": "typescript",
 161 |         ".jsx": "javascript",
 162 |         ".tsx": "typescript",
 163 |         ".r": "r",
 164 |         ".jl": "julia",
 165 |         ".rs": "rust",
 166 |         ".cpp": "cpp",
 167 |         ".cxx": "cpp",
 168 |         ".cc": "cpp",
 169 |         ".hpp": "cpp",
 170 |         ".hxx": "cpp",
 171 |         ".h": "c",
 172 |         ".c": "c",
 173 |         ".cs": "csharp",
 174 |         ".java": "java",
 175 |         ".go": "go",
 176 |         ".php": "php",
 177 |     }
 178 |     return language_map.get(ext)
 181 | def get_language_parser(file_path: str) -> Optional[Tuple[str, Callable]]:
 183 |     ext = file_path.split(".")[-1].lower() if "." in file_path else ""
 185 |     extension_map = {
 187 |         ".py": ("python", parse_python),
 188 |         ".js": ("javascript", parse_javascript_or_typescript),
 189 |         ".ts": ("typescript", parse_javascript_or_typescript),
 190 |         ".jsx": ("javascript", parse_javascript_or_typescript),
 191 |         ".tsx": ("typescript", parse_javascript_or_typescript),
 192 |         ".r": ("r", parse_r),
 193 |         ".jl": ("julia", parse_julia),
 195 |         ".rs": ("rust", parse_rust),
 196 |         ".cpp": ("cpp", parse_cpp_code),
 197 |         ".cxx": ("cpp", parse_cpp_code),
 198 |         ".cc": ("cpp", parse_cpp_code),
 199 |         ".hpp": ("cpp", parse_cpp_code),
 200 |         ".hxx": ("cpp", parse_cpp_code),
 201 |         ".h": ("c", parse_c_code),  # Note: .h could be C or C++
 202 |         ".c": ("c", parse_c_code),
 203 |         ".cs": ("csharp", parse_csharp_code),
 204 |         ".java": ("java", parse_java),
 205 |         ".go": ("go", parse_go),
 206 |         ".php": ("php", parse_php),
 207 |     }
 209 |     ext_with_dot = f".{ext}" if not ext.startswith(".") else ext
 210 |     return extension_map.get(ext_with_dot)
 213 | def get_language_name(file_path: str) -> str:
 215 |     parser_info = get_language_parser(file_path)
 216 |     if parser_info:
 217 |         return parser_info[0]
 218 |     return "unknown"
 221 | def is_doc_file(file_path: str, doc_exts: List[str]) -> bool:
 222 |     ext = os.path.splitext(file_path)[1].lower()
 223 |     return ext in doc_exts
 226 | def read_file_content(file_path: str) -> str:
 227 |     try:
 228 |         with open(file_path, "r", encoding="utf-8", errors="replace") as f:
 229 |             return f.read()
 230 |     except Exception:
 231 |         return ""
```

---
### File: ./codeconcat/parser/__init__.py
#### Summary
```
File: __init__.py
Language: python
```

```python

```

---
### File: ./codeconcat/parser/language_parsers/csharp_parser.py
#### Summary
```
File: csharp_parser.py
Language: python
```

```python
   3 | import re
   4 | from typing import List, Optional, Set
   5 | from codeconcat.base_types import Declaration, ParsedFileData
   6 | from codeconcat.parser.language_parsers.base_parser import BaseParser, CodeSymbol
   9 | def parse_csharp_code(file_path: str, content: str) -> Optional[ParsedFileData]:
  11 |     parser = CSharpParser()
  12 |     declarations = parser.parse(content)
  13 |     return ParsedFileData(
  14 |         file_path=file_path,
  15 |         language="csharp",
  16 |         content=content,
  17 |         declarations=declarations
  18 |     )
  21 | class CSharpParser(BaseParser):
  24 |     def __init__(self):
  26 |         super().__init__()
  27 |         self._setup_patterns()
  29 |     def _setup_patterns(self):
  31 |         modifiers = r"(?:public|private|protected|internal)?\s*"
  32 |         class_modifiers = r"(?:static|abstract|sealed)?\s*"
  33 |         method_modifiers = r"(?:static|virtual|abstract|override)?\s*"
  34 |         type_pattern = r"(?:[a-zA-Z_][a-zA-Z0-9_<>]*\s+)+"
  36 |         self.patterns = {
  37 |             "class": re.compile(
  38 |                 r"^\s*" + modifiers + class_modifiers +  # Access and class modifiers
  39 |                 r"class\s+" +  # class keyword
  40 |                 r"(?P<class_name>[a-zA-Z_][a-zA-Z0-9_]*)"  # Class name
  41 |             ),
  42 |             "interface": re.compile(
  43 |                 r"^\s*" + modifiers +  # Access modifiers
  44 |                 r"interface\s+" +  # interface keyword
  45 |                 r"(?P<interface_name>[a-zA-Z_][a-zA-Z0-9_]*)"  # Interface name
  46 |             ),
  47 |             "method": re.compile(
  48 |                 r"^\s*" + modifiers + method_modifiers +  # Access and method modifiers
  49 |                 r"(?:async\s+)?" +  # Optional async
  50 |                 type_pattern +  # Return type
  51 |                 r"(?P<method_name>[a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)"  # Method name and args
  52 |             ),
  53 |             "property": re.compile(
  54 |                 r"^\s*" + modifiers + method_modifiers +  # Access and property modifiers
  55 |                 type_pattern +  # Property type
  56 |                 r"(?P<property_name>[a-zA-Z_][a-zA-Z0-9_]*)\s*{\s*(?:get|set)"  # Property name
  57 |             ),
  58 |             "enum": re.compile(
  59 |                 r"^\s*" + modifiers +  # Access modifiers
  60 |                 r"enum\s+" +  # enum keyword
  61 |                 r"(?P<enum_name>[a-zA-Z_][a-zA-Z0-9_]*)"  # Enum name
  62 |             ),
  63 |             "struct": re.compile(
  64 |                 r"^\s*" + modifiers +  # Access modifiers
  65 |                 r"struct\s+" +  # struct keyword
  66 |                 r"(?P<struct_name>[a-zA-Z_][a-zA-Z0-9_]*)"  # Struct name
  67 |             ),
  68 |             "delegate": re.compile(
  69 |                 r"^\s*" + modifiers +  # Access modifiers
  70 |                 r"delegate\s+" +  # delegate keyword
  71 |                 type_pattern +  # Return type
  72 |                 r"(?P<delegate_name>[a-zA-Z_][a-zA-Z0-9_]*)\s*\("  # Delegate name
  73 |             ),
  74 |             "event": re.compile(
  75 |                 r"^\s*" + modifiers +  # Access modifiers
  76 |                 r"event\s+" +  # event keyword
  77 |                 type_pattern +  # Event type
  78 |                 r"(?P<event_name>[a-zA-Z_][a-zA-Z0-9_]*)"  # Event name
  79 |             ),
  80 |             "namespace": re.compile(
  81 |                 r"^\s*namespace\s+" +  # namespace keyword
  82 |                 r"(?P<namespace_name>[a-zA-Z_][a-zA-Z0-9_.]*)"  # Namespace name
  83 |             ),
  84 |         }
  86 |     def _extract_name(self, match: re.Match, kind: str, line: str) -> Optional[str]:
  88 |         if kind == "class":
  89 |             return match.group("class_name")
  90 |         elif kind == "interface":
  91 |             return match.group("interface_name")
  92 |         elif kind == "method":
  93 |             return match.group("method_name")
  94 |         elif kind == "property":
  95 |             return match.group("property_name")
  96 |         elif kind == "enum":
  97 |             return match.group("enum_name")
  98 |         elif kind == "struct":
  99 |             return match.group("struct_name")
 100 |         elif kind == "delegate":
 101 |             return match.group("delegate_name")
 102 |         elif kind == "event":
 103 |             return match.group("event_name")
 104 |         elif kind == "namespace":
 105 |             return match.group("namespace_name")
 106 |         return None
 108 |     def parse(self, content: str) -> List[Declaration]:
 110 |         lines = content.split("\n")
 111 |         symbols: List[CodeSymbol] = []
 112 |         i = 0
 114 |         in_block = False
 115 |         block_start = 0
 116 |         block_name = ""
 117 |         block_kind = ""
 118 |         brace_count = 0
 119 |         in_comment = False
 120 |         in_attribute = False
 122 |         while i < len(lines):
 123 |             line = lines[i].strip()
 126 |             if "/*" in line:
 127 |                 in_comment = True
 128 |             if "*/" in line:
 129 |                 in_comment = False
 130 |                 i += 1
 131 |                 continue
 132 |             if in_comment or line.strip().startswith("//"):
 133 |                 i += 1
 134 |                 continue
 137 |             if line.strip().startswith("["):
 138 |                 in_attribute = True
 139 |             if in_attribute:
 140 |                 if "]" in line:
 141 |                     in_attribute = False
 142 |                 i += 1
 143 |                 continue
 146 |             if not in_block:
 147 |                 for kind, pattern in self.patterns.items():
 148 |                     match = pattern.match(line)
 149 |                     if match:
 150 |                         block_name = self._extract_name(match, kind, line)
 151 |                         if not block_name:
 152 |                             continue
 154 |                         block_start = i
 155 |                         block_kind = kind
 156 |                         in_block = True
 157 |                         brace_count = line.count("{") - line.count("}")
 160 |                         if ";" in line:
 161 |                             symbols.append(
 162 |                                 CodeSymbol(
 163 |                                     name=block_name,
 164 |                                     kind=kind,
 165 |                                     start_line=i,
 166 |                                     end_line=i,
 167 |                                     modifiers=set(),
 168 |                                     parent=None,
 169 |                                 )
 170 |                             )
 171 |                             in_block = False
 172 |                             break
 173 |                         elif brace_count == 0:
 175 |                             j = i + 1
 176 |                             while j < len(lines) and not in_block:
 177 |                                 next_line = lines[j].strip()
 178 |                                 if next_line and not next_line.startswith("//"):
 179 |                                     if "{" in next_line:
 180 |                                         in_block = True
 181 |                                         brace_count = 1
 182 |                                     elif ";" in next_line:
 183 |                                         symbols.append(
 184 |                                             CodeSymbol(
 185 |                                                 name=block_name,
 186 |                                                 kind=kind,
 187 |                                                 start_line=i,
 188 |                                                 end_line=j,
 189 |                                                 modifiers=set(),
 190 |                                                 parent=None,
 191 |                                             )
 192 |                                         )
 193 |                                         in_block = False
 194 |                                         i = j
 195 |                                         break
 196 |                                 j += 1
 197 |                             break
 198 |             else:
 199 |                 brace_count += line.count("{") - line.count("}")
 202 |             if in_block and brace_count == 0 and ("}" in line or ";" in line):
 203 |                 symbols.append(
 204 |                     CodeSymbol(
 205 |                         name=block_name,
 206 |                         kind=block_kind,
 207 |                         start_line=block_start,
 208 |                         end_line=i,
 209 |                         modifiers=set(),
 210 |                         parent=None,
 211 |                     )
 212 |                 )
 213 |                 in_block = False
 215 |             i += 1
 218 |         processed_declarations = []
 219 |         seen_names = set()
 222 |         for symbol in symbols:
 223 |             if symbol.name not in seen_names:
 224 |                 processed_declarations.append(
 225 |                     Declaration(symbol.kind, symbol.name, symbol.start_line + 1, symbol.end_line + 1)
 226 |                 )
 227 |                 seen_names.add(symbol.name)
 229 |         return processed_declarations
```

---
### File: ./codeconcat/parser/language_parsers/c_parser.py
#### Summary
```
File: c_parser.py
Language: python
```

```python
   3 | import re
   4 | from typing import List, Optional, Set
   5 | from codeconcat.base_types import Declaration, ParsedFileData
   6 | from codeconcat.parser.language_parsers.base_parser import BaseParser, CodeSymbol
   8 | def parse_c_code(file_path: str, content: str) -> Optional[ParsedFileData]:
   9 |     parser = CParser()
  10 |     declarations = parser.parse(content)
  11 |     return ParsedFileData(
  12 |         file_path=file_path,
  13 |         language="c",
  14 |         content=content,
  15 |         declarations=declarations
  16 |     )
  18 | class CParser(BaseParser):
  19 |     def _setup_patterns(self):
  21 |         We define capturing groups: 'name' for declarations.
  24 |         storage = r"(?:static|extern)?\s*"
  25 |         inline = r"(?:inline)?\s*"
  26 |         type_pattern = r"(?:[a-zA-Z_][\w*\s]+)+"
  28 |         self.patterns = {
  29 |             "function": re.compile(
  30 |                 rf"^[^#/]*{storage}{inline}"
  31 |                 rf"{type_pattern}\s+"
  32 |                 rf"(?P<name>[a-zA-Z_]\w*)\s*\([^;{{]*"
  33 |             ),
  34 |             "struct": re.compile(
  35 |                 rf"^[^#/]*struct\s+(?P<name>[a-zA-Z_]\w*)"
  36 |             ),
  37 |             "union": re.compile(
  38 |                 rf"^[^#/]*union\s+(?P<name>[a-zA-Z_]\w*)"
  39 |             ),
  40 |             "enum": re.compile(
  41 |                 rf"^[^#/]*enum\s+(?P<name>[a-zA-Z_]\w*)"
  42 |             ),
  43 |             "typedef": re.compile(
  44 |                 r"^[^#/]*typedef\s+"
  45 |                 r"(?:struct|union|enum)?\s*"
  46 |                 r"(?:[a-zA-Z_][\w*\s]+)*"
  47 |                 r"(?:\(\s*\*\s*)?"
  48 |                 r"(?P<name>[a-zA-Z_]\w*)"
  49 |                 r"(?:\s*\))?"
  50 |                 r"\s*(?:\([^)]*\))?\s*;"
  51 |             ),
  52 |             "define": re.compile(
  53 |                 r"^[^#/]*#define\s+(?P<name>[A-Z_][A-Z0-9_]*)"
  54 |             ),
  55 |         }
  58 |         self.block_start = "{"
  59 |         self.block_end = "}"
  60 |         self.line_comment = "//"
  61 |         self.block_comment_start = "/*"
  62 |         self.block_comment_end = "*/"
  64 |     def parse(self, content: str) -> List[Declaration]:
  65 |         lines = content.split("\n")
  66 |         symbols: List[CodeSymbol] = []
  67 |         line_count = len(lines)
  68 |         i = 0
  70 |         while i < line_count:
  71 |             line = lines[i].strip()
  72 |             if not line or line.startswith("//"):
  73 |                 i += 1
  74 |                 continue
  77 |             for kind, pattern in self.patterns.items():
  78 |                 match = pattern.match(line)
  79 |                 if match:
  80 |                     name = match.group("name")
  82 |                     block_end = i
  83 |                     if kind in ["function", "struct", "union", "enum"]:
  84 |                         block_end = self._find_block_end(lines, i)
  86 |                     symbol = CodeSymbol(
  87 |                         name=name,
  88 |                         kind=kind,
  89 |                         start_line=i,
  90 |                         end_line=block_end,
  91 |                         modifiers=set(),
  92 |                     )
  93 |                     symbols.append(symbol)
  94 |                     i = block_end  # skip to block_end
  95 |                     break
  96 |             i += 1
  99 |         declarations = []
 100 |         for sym in symbols:
 101 |             declarations.append(Declaration(
 102 |                 kind=sym.kind,
 103 |                 name=sym.name,
 104 |                 start_line=sym.start_line + 1,
 105 |                 end_line=sym.end_line + 1,
 106 |                 modifiers=sym.modifiers
 107 |             ))
 108 |         return declarations
 110 |     def _find_block_end(self, lines: List[str], start: int) -> int:
 112 |         Naive approach: if we see '{', we try to find matching '}'.
 113 |         If not found, return start.
 115 |         line = lines[start]
 116 |         if "{" not in line:
 117 |             return start
 118 |         brace_count = line.count("{") - line.count("}")
 119 |         if brace_count <= 0:
 120 |             return start
 122 |         for i in range(start + 1, len(lines)):
 123 |             l2 = lines[i]
 125 |             if l2.strip().startswith("//"):
 126 |                 continue
 127 |             brace_count += l2.count("{") - l2.count("}")
 128 |             if brace_count <= 0:
 129 |                 return i
 130 |         return len(lines) - 1
```

---
### File: ./codeconcat/parser/language_parsers/julia_parser.py
#### Summary
```
File: julia_parser.py
Language: python
```

```python
   3 | import re
   4 | from typing import List, Optional, Set
   5 | from codeconcat.base_types import Declaration, ParsedFileData
   6 | from codeconcat.parser.language_parsers.base_parser import BaseParser, CodeSymbol
   8 | def parse_julia(file_path: str, content: str) -> Optional[ParsedFileData]:
   9 |     parser = JuliaParser()
  10 |     declarations = parser.parse(content)
  11 |     return ParsedFileData(
  12 |         file_path=file_path,
  13 |         language="julia",
  14 |         content=content,
  15 |         declarations=declarations
  16 |     )
  18 | class JuliaParser(BaseParser):
  19 |     def _setup_patterns(self):
  21 |         We'll define simpler patterns. Note we must handle single-line vs. multi-line function definitions
  22 |         like:
  23 |           function name(...) ...
  24 |         or
  25 |           name(x) = x+1
  28 |         self.patterns = {
  29 |             "function": re.compile(
  30 |                 r"^[^#]*"
  31 |                 r"(?:function\s+(?P<name>[a-zA-Z_]\w*))|"
  32 |                 r"^(?P<name2>[a-zA-Z_]\w*)\s*\([^)]*\)\s*=\s*"
  33 |             ),
  34 |             "struct": re.compile(
  35 |                 r"^[^#]*(?:mutable\s+)?struct\s+(?P<name>[A-Z][a-zA-Z0-9_]*)"
  36 |             ),
  37 |             "abstract": re.compile(
  38 |                 r"^[^#]*abstract\s+type\s+(?P<name>[A-Z][a-zA-Z0-9_]*)"
  39 |             ),
  40 |             "module": re.compile(
  41 |                 r"^[^#]*module\s+(?P<name>[A-Z][a-zA-Z0-9_]*)"
  42 |             ),
  43 |             "macro": re.compile(
  44 |                 r"^[^#]*macro\s+(?P<name>[a-zA-Z_]\w*)"
  45 |             ),
  46 |         }
  48 |         self.block_start = "begin"  # not always used, but a placeholder
  49 |         self.block_end = "end"
  50 |         self.line_comment = "#"
  51 |         self.block_comment_start = "#="
  52 |         self.block_comment_end = "=#"
  54 |     def parse(self, content: str) -> List[Declaration]:
  55 |         lines = content.split("\n")
  56 |         symbols: List[CodeSymbol] = []
  57 |         i = 0
  58 |         line_count = len(lines)
  60 |         while i < line_count:
  61 |             line = lines[i]
  62 |             stripped = line.strip()
  63 |             if not stripped or stripped.startswith("#"):
  64 |                 i += 1
  65 |                 continue
  67 |             matched = False
  68 |             for kind, pattern in self.patterns.items():
  69 |                 m = pattern.match(stripped)
  70 |                 if m:
  72 |                     name = m.groupdict().get("name") or m.groupdict().get("name2")
  73 |                     if not name:
  74 |                         continue
  75 |                     symbol = CodeSymbol(
  76 |                         name=name,
  77 |                         kind=kind,
  78 |                         start_line=i,
  79 |                         end_line=i,
  80 |                         modifiers=set(),
  81 |                     )
  82 |                     symbols.append(symbol)
  83 |                     matched = True
  84 |                     break
  85 |             i += 1
  87 |         declarations = []
  88 |         for sym in symbols:
  89 |             declarations.append(Declaration(
  90 |                 kind=sym.kind,
  91 |                 name=sym.name,
  92 |                 start_line=sym.start_line + 1,
  93 |                 end_line=sym.end_line + 1,
  94 |                 modifiers=sym.modifiers
  95 |             ))
  96 |         return declarations
```

---
### File: ./codeconcat/parser/language_parsers/__init__.py
#### Summary
```
File: __init__.py
Language: python
```

```python

```

---
### File: ./codeconcat/parser/language_parsers/php_parser.py
#### Summary
```
File: php_parser.py
Language: python
```

```python
   3 | import re
   4 | from typing import List, Optional, Set
   5 | from codeconcat.base_types import Declaration, ParsedFileData
   6 | from codeconcat.parser.language_parsers.base_parser import BaseParser, CodeSymbol
   8 | def parse_php(file_path: str, content: str) -> Optional[ParsedFileData]:
   9 |     parser = PhpParser()
  10 |     declarations = parser.parse(content)
  11 |     return ParsedFileData(
  12 |         file_path=file_path,
  13 |         language="php",
  14 |         content=content,
  15 |         declarations=declarations
  16 |     )
  18 | class PhpParser(BaseParser):
  19 |     def _setup_patterns(self):
  21 |         Using consistent '(?P<name>...)' for all top-level declarations:
  22 |         class, interface, trait, function, etc.
  24 |         self.patterns = {
  25 |             "class": re.compile(
  26 |                 r"^[^#/]*"
  27 |                 r"(?:abstract\s+|final\s+)?"
  28 |                 r"class\s+(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)"
  29 |                 r"(?:\s+extends\s+[a-zA-Z_][a-zA-Z0-9_]*)?"
  30 |                 r"(?:\s+implements\s+[a-zA-Z_][a-zA-Z0-9_]*(?:\s*,\s*[a-zA-Z_][a-zA-Z0-9_]*)*)?"
  31 |                 r"\s*\{"
  32 |             ),
  33 |             "interface": re.compile(
  34 |                 r"^[^#/]*"
  35 |                 r"interface\s+(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)"
  36 |                 r"(?:\s+extends\s+[a-zA-Z_][a-zA-Z0-9_]*(?:\s*,\s*[a-zA-Z_][a-zA-Z0-9_]*)*)?"
  37 |                 r"\s*\{"
  38 |             ),
  39 |             "trait": re.compile(
  40 |                 r"^[^#/]*"
  41 |                 r"trait\s+(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)"
  42 |                 r"\s*\{"
  43 |             ),
  44 |             "function": re.compile(
  45 |                 r"^[^#/]*"
  46 |                 r"(?:public\s+|private\s+|protected\s+|static\s+|final\s+)*"
  47 |                 r"function\s+(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)"
  48 |                 r"\s*\([^)]*\)"
  49 |                 r"(?:\s*:\s*[a-zA-Z_][a-zA-Z0-9_|\\]*)?"
  50 |                 r"\s*\{"
  51 |             ),
  52 |             "namespace": re.compile(
  53 |                 r"^[^#/]*"
  54 |                 r"namespace\s+(?P<name>[a-zA-Z_][a-zA-Z0-9_\\]*)"
  55 |                 r"\s*;?"
  56 |             ),
  57 |         }
  59 |         self.block_start = "{"
  60 |         self.block_end = "}"
  61 |         self.line_comment = "//"
  63 |         self.block_comment_start = "/*"
  64 |         self.block_comment_end = "*/"
  66 |     def parse(self, content: str) -> List[Declaration]:
  67 |         lines = content.split("\n")
  68 |         symbols: List[CodeSymbol] = []
  69 |         i = 0
  70 |         line_count = len(lines)
  72 |         while i < line_count:
  73 |             line = lines[i].strip()
  74 |             if not line or line.startswith("//") or line.startswith("#"):
  75 |                 i += 1
  76 |                 continue
  78 |             matched = False
  79 |             for kind, pattern in self.patterns.items():
  80 |                 match = pattern.match(line)
  81 |                 if match:
  82 |                     name = match.group("name")
  83 |                     block_end = i
  85 |                     if kind in ["class", "interface", "trait", "function"]:
  86 |                         block_end = self._find_block_end(lines, i)
  88 |                     symbol = CodeSymbol(
  89 |                         kind=kind,
  90 |                         name=name,
  91 |                         start_line=i,
  92 |                         end_line=block_end,
  93 |                         modifiers=set()
  94 |                     )
  95 |                     symbols.append(symbol)
  96 |                     i = block_end
  97 |                     matched = True
  98 |                     break
  99 |             if not matched:
 100 |                 i += 1
 102 |         declarations = []
 103 |         for sym in symbols:
 104 |             declarations.append(Declaration(
 105 |                 kind=sym.kind,
 106 |                 name=sym.name,
 107 |                 start_line=sym.start_line + 1,
 108 |                 end_line=sym.end_line + 1,
 109 |                 modifiers=sym.modifiers,
 110 |             ))
 111 |         return declarations
 113 |     def _find_block_end(self, lines: List[str], start: int) -> int:
 114 |         line = lines[start]
 115 |         if "{" not in line:
 116 |             return start
 117 |         brace_count = line.count("{") - line.count("}")
 118 |         if brace_count <= 0:
 119 |             return start
 120 |         for i in range(start + 1, len(lines)):
 121 |             l2 = lines[i]
 122 |             if l2.strip().startswith("//") or l2.strip().startswith("#"):
 123 |                 continue
 124 |             brace_count += l2.count("{") - l2.count("}")
 125 |             if brace_count <= 0:
 126 |                 return i
 127 |         return len(lines) - 1
```

---
### File: ./codeconcat/parser/language_parsers/rust_parser.py
#### Summary
```
File: rust_parser.py
Language: python
```

```python
   2 | import re
   3 | from typing import List, Optional
   4 | from codeconcat.base_types import Declaration, ParsedFileData
   5 | from codeconcat.parser.language_parsers.base_parser import BaseParser, CodeSymbol
   8 | def parse_rust(file_path: str, content: str) -> Optional[ParsedFileData]:
  10 |     parser = RustParser()
  11 |     declarations = parser.parse(content)
  12 |     return ParsedFileData(
  13 |         file_path=file_path,
  14 |         language="rust",
  15 |         content=content,
  16 |         declarations=declarations
  17 |     )
  20 | class RustParser(BaseParser):
  23 |     def __init__(self):
  25 |         super().__init__()
  26 |         self._setup_patterns()
  28 |     def _setup_patterns(self):
  31 |         name = r"[a-zA-Z_][a-zA-Z0-9_]*"
  33 |         type_name = r"[a-zA-Z_][a-zA-Z0-9_<>:'\s,\(\)\[\]\+\-]*"
  34 |         visibility = r"(?:pub(?:\s*\([^)]*\))?\s+)?"
  37 |         self.patterns = {
  38 |             "struct": re.compile(
  39 |                 rf"^[^/]*{visibility}struct\s+(?P<n>[A-Z][a-zA-Z0-9_]*)(?:<[^>]*>)?(?:\s*where\s+[^{{]+)?\s*(?:\{{|;|\()"
  40 |             ),
  41 |             "enum": re.compile(
  42 |                 rf"^[^/]*{visibility}enum\s+(?P<n>[A-Z][a-zA-Z0-9_]*)(?:<[^>]*>)?(?:\s*where\s+[^{{]+)?\s*\{{"
  43 |             ),
  44 |             "trait": re.compile(
  45 |                 rf"^[^/]*{visibility}trait\s+(?P<n>[A-Z][a-zA-Z0-9_]*)(?:<[^>]*>)?(?:\s*:\s*[^{{]+)?(?:\s*where\s+[^{{]+)?\s*\{{"
  46 |             ),
  47 |             "impl": re.compile(
  49 |                 rf"^[^/]*impl\s+(?:<[^>]*>\s*)?(?:(?P<trait>[A-Z][a-zA-Z0-9_]*(?:<[^>]*>)?)\s+for\s+)?(?P<n>{type_name})(?:\s*where\s+[^{{]+)?\s*\{{"
  50 |             ),
  51 |             "function": re.compile(
  52 |                 rf"^[^/]*{visibility}(?:async\s+)?(?:unsafe\s+)?(?:extern\s+[\"'][^\"']+[\"']\s+)?fn\s+(?P<n>[a-z_][a-zA-Z0-9_]*)(?:<[^>]*>)?\s*\([^)]*\)(?:\s*->\s*[^{{;]+)?(?:\s*where\s+[^{{]+)?\s*(?:\{{|;)"
  53 |             ),
  54 |             "type": re.compile(
  55 |                 rf"^[^/]*{visibility}type\s+(?P<n>{name})(?:\s*<[^>]*>)?\s*="
  56 |             ),
  57 |             "constant": re.compile(
  58 |                 rf"^[^/]*{visibility}const\s+(?P<n>{name})\s*:"
  59 |             ),
  60 |             "static": re.compile(
  61 |                 rf"^[^/]*{visibility}static\s+(?:mut\s+)?(?P<n>{name})\s*:"
  62 |             ),
  63 |             "mod": re.compile(
  64 |                 rf"^[^/]*{visibility}mod\s+(?P<n>{name})\s*(?:\{{|;)"
  65 |             ),
  66 |         }
  68 |     def _find_block_end(self, lines: List[str], start: int) -> int:
  70 |         brace_count = 0
  71 |         in_string = False
  72 |         string_char = None
  73 |         in_comment = False
  74 |         line_count = len(lines)
  75 |         first_line = lines[start]
  79 |         if "{" not in first_line and "(" not in first_line:
  80 |             return start
  83 |         for char in first_line:
  84 |             if char == '"':
  85 |                 if not in_string:
  86 |                     in_string = True
  87 |                     string_char = char
  88 |                 elif string_char == char:
  89 |                     in_string = False
  90 |                     string_char = None
  91 |             elif not in_string:
  92 |                 if char == "{":
  93 |                     brace_count += 1
  94 |                 elif char == "}":
  95 |                     brace_count -= 1
  98 |         if brace_count == 0:
  99 |             return start
 102 |         for i in range(start + 1, line_count):
 103 |             line = lines[i]
 106 |             if line.strip().startswith("//"):
 107 |                 continue
 110 |             j = 0
 111 |             while j < len(line):
 113 |                 if j < len(line) - 1:
 114 |                     pair = line[j : j + 2]
 115 |                     if pair == "/*" and not in_string:
 116 |                         in_comment = True
 117 |                         j += 2
 118 |                         continue
 119 |                     elif pair == "*/" and in_comment:
 120 |                         in_comment = False
 121 |                         j += 2
 122 |                         continue
 124 |                 char = line[j]
 127 |                 if char == '"' and not in_comment:
 128 |                     if not in_string:
 129 |                         in_string = True
 130 |                         string_char = char
 131 |                     elif string_char == char:
 132 |                         in_string = False
 133 |                         string_char = None
 134 |                 elif not in_string and not in_comment:
 135 |                     if char == "{":
 136 |                         brace_count += 1
 137 |                     elif char == "}":
 138 |                         brace_count -= 1
 139 |                         if brace_count == 0:
 140 |                             return i
 141 |                 j += 1
 144 |         return start
 146 |     def parse(self, content: str) -> List[Declaration]:
 148 |         lines = content.split("\n")
 149 |         symbols: List[CodeSymbol] = []
 150 |         symbol_stack: List[CodeSymbol] = []
 152 |         brace_depth = 0
 155 |         current_doc_comments: List[str] = []
 156 |         current_attributes: List[str] = []
 158 |         def pop_symbols_up_to(depth: int, line_idx: int):
 160 |             while symbol_stack and int(symbol_stack[-1].modifiers.get("_brace_depth", "0")) >= depth:
 161 |                 top = symbol_stack.pop()
 162 |                 top.end_line = line_idx
 163 |                 symbols.append(top)
 165 |         i = 0
 166 |         while i < len(lines):
 167 |             line = lines[i]
 168 |             stripped = line.strip()
 171 |             if not stripped:
 172 |                 i += 1
 173 |                 continue
 176 |             if stripped.startswith("///") or stripped.startswith("//!"):
 177 |                 current_doc_comments.append(stripped)
 178 |                 i += 1
 179 |                 continue
 182 |             if stripped.startswith("/**"):
 183 |                 current_doc_comments.append(stripped)
 185 |                 while i + 1 < len(lines) and "*/" not in lines[i]:
 186 |                     i += 1
 187 |                     current_doc_comments.append(lines[i].strip())
 188 |                 i += 1
 189 |                 continue
 192 |             if stripped.startswith("//"):
 193 |                 i += 1
 194 |                 continue
 197 |             if stripped.startswith("#["):
 199 |                 attr_line = stripped
 200 |                 while "]" not in attr_line and i + 1 < len(lines):
 201 |                     i += 1
 202 |                     attr_line += " " + lines[i].strip()
 203 |                 current_attributes.append(attr_line)
 204 |                 i += 1
 205 |                 continue
 207 |             matched = False
 210 |             if stripped.startswith("}"):
 211 |                 brace_depth -= 1
 213 |                 pop_symbols_up_to(brace_depth + 1, i + 1)
 214 |                 i += 1
 215 |                 continue
 218 |             for kind, pattern in self.patterns.items():
 219 |                 m = pattern.match(stripped)
 220 |                 if m:
 221 |                     matched = True
 222 |                     name = m.group("n")
 225 |                     if kind == "impl" and m.group("trait"):
 226 |                         name = f"{m.group('trait')} for {name}"
 229 |                     modifiers = {}
 231 |                     if "pub" in stripped:
 233 |                         vis_m = re.search(r"pub(?:\s*\([^)]*\))?", stripped)
 234 |                         if vis_m:
 235 |                             modifiers["pub"] = vis_m.group(0)
 238 |                     for attr in current_attributes:
 239 |                         modifiers[attr] = attr
 240 |                     current_attributes.clear()
 242 |                     if current_doc_comments:
 243 |                         modifiers["_docstring"] = "\n".join(current_doc_comments)
 244 |                     current_doc_comments.clear()
 247 |                     block_end = i
 248 |                     if "{" in stripped:
 249 |                         brace_depth += 1
 250 |                         modifiers["_brace_depth"] = str(brace_depth)
 251 |                         block_end = self._find_block_end(lines, i)
 254 |                         symbol = CodeSymbol(
 255 |                             kind=kind,
 256 |                             name=name,
 257 |                             start_line=i + 1,
 258 |                             end_line=block_end + 1,
 259 |                             modifiers=modifiers,
 260 |                         )
 261 |                         symbol_stack.append(symbol)
 262 |                     else:
 264 |                         block_end = self._find_block_end(lines, i)
 265 |                         symbol = CodeSymbol(
 266 |                             kind=kind,
 267 |                             name=name,
 268 |                             start_line=i + 1,
 269 |                             end_line=block_end + 1,
 270 |                             modifiers=modifiers,
 271 |                         )
 272 |                         symbols.append(symbol)
 275 |                     i = block_end
 276 |                     break
 278 |             if not matched:
 280 |                 i += 1
 283 |         while symbol_stack:
 284 |             top = symbol_stack.pop()
 285 |             top.end_line = len(lines)
 286 |             symbols.append(top)
 289 |         declarations = []
 290 |         for sym in symbols:
 292 |             public_mods = {}
 293 |             docstring = None
 294 |             for k, v in sym.modifiers.items():
 295 |                 if k.startswith("_docstring"):
 296 |                     docstring = v
 297 |                 elif not k.startswith("_"):
 298 |                     public_mods[k] = v
 300 |             declarations.append(
 301 |                 Declaration(
 302 |                     kind=sym.kind,
 303 |                     name=sym.name,
 304 |                     start_line=sym.start_line,
 305 |                     end_line=sym.end_line,
 306 |                     modifiers=set(public_mods.values()),
 307 |                     docstring=docstring,
 308 |                 )
 309 |             )
 311 |         return declarations
```

---
### File: ./codeconcat/parser/language_parsers/js_ts_parser.py
#### Summary
```
File: js_ts_parser.py
Language: python
```

```python
   3 | import re
   4 | from typing import List, Optional, Set
   6 | from codeconcat.base_types import Declaration, ParsedFileData
   7 | from codeconcat.parser.language_parsers.base_parser import BaseParser
  10 | def parse_javascript_or_typescript(file_path: str, content: str, language: str = "javascript") -> Optional[ParsedFileData]:
  12 |     parser = JstsParser(language)
  13 |     declarations = parser.parse(content)
  14 |     return ParsedFileData(
  15 |         file_path=file_path,
  16 |         language=language,
  17 |         content=content,
  18 |         declarations=declarations
  19 |     )
  22 | class CodeSymbol:
  23 |     def __init__(
  24 |         self,
  25 |         name: str,
  26 |         kind: str,
  27 |         start_line: int,
  28 |         end_line: int,
  29 |         modifiers: Set[str],
  30 |         docstring: Optional[str],
  31 |         children: List["CodeSymbol"],
  32 |     ):
  33 |         self.name = name
  34 |         self.kind = kind
  35 |         self.start_line = start_line
  36 |         self.end_line = end_line
  37 |         self.modifiers = modifiers
  38 |         self.docstring = docstring
  39 |         self.children = children
  40 |         self.brace_depth = 0  # Current nesting depth at the time this symbol was "opened"
  43 | class JstsParser(BaseParser):
  45 |     JavaScript/TypeScript language parser with improved brace-handling and 
  46 |     arrow-function detection. Supports classes, functions, methods, arrow functions, 
  47 |     interfaces, type aliases, enums, and basic decorators.
  50 |     def __init__(self, language: str = "javascript"):
  51 |         self.language = language
  52 |         self.patterns = []
  53 |         super().__init__()
  56 |         self.recognized_modifiers = {
  57 |             "export",
  58 |             "default",
  59 |             "async",
  60 |             "public",
  61 |             "private",
  62 |             "protected",
  63 |             "static",
  64 |             "readonly",
  65 |             "abstract",
  66 |             "declare",
  67 |             "const",
  68 |         }
  71 |         self.line_comment = "//"
  72 |         self.block_comment_start = "/*"
  73 |         self.block_comment_end = "*/"
  76 |         self.in_class = False
  78 |         self._setup_patterns()
  80 |     def _setup_patterns(self) -> List[re.Pattern]:
  82 |         return [
  84 |             re.compile(r"^(?:export\s+)?class\s+(?P<symbol_name>\w+)"),
  87 |             re.compile(r"^(?:export\s+)?(?:async\s+)?function\s+(?P<symbol_name>\w+)\s*\("),
  88 |             re.compile(r"^(?:export\s+)?(?:const|let|var)\s+(?P<symbol_name>\w+)\s*=\s*(?:async\s+)?function\s*\("),
  89 |             re.compile(r"^(?:export\s+)?(?:const|let|var)\s+(?P<symbol_name>\w+)\s*=\s*(?:async\s+)?\(.*\)\s*=>"),
  92 |             re.compile(r"^\s*(?:static\s+)?(?:async\s+)?(?P<symbol_name>\w+)\s*\("),
  95 |             re.compile(r"^(?:export\s+)?interface\s+(?P<symbol_name>\w+)"),
  98 |             re.compile(r"^(?:export\s+)?type\s+(?P<symbol_name>\w+)"),
 101 |             re.compile(r"^(?:export\s+)?enum\s+(?P<symbol_name>\w+)"),
 102 |         ]
 104 |     def _get_kind(self, pattern: re.Pattern) -> str:
 106 |         pattern_str = pattern.pattern
 107 |         if "=>" in pattern_str:
 108 |             return "arrow_function"
 109 |         elif "function\\s+" in pattern_str:
 110 |             return "function"
 111 |         elif "class\\s+" in pattern_str:
 112 |             return "class"
 113 |         elif "interface\\s+" in pattern_str:
 114 |             return "interface"
 115 |         elif "type\\s+" in pattern_str:
 116 |             return "type"
 117 |         elif "enum\\s+" in pattern_str:
 118 |             return "enum"
 119 |         elif r"^\s*(?:static\s+)?(?:async\s+)?(?P<symbol_name>\w+)\s*\(" in pattern_str:
 121 |             if self.in_class:
 122 |                 return "method"
 123 |             return "function"
 124 |         return "unknown"  # Default to unknown for any other patterns
 126 |     def parse(self, content: str) -> List[Declaration]:
 128 |         lines = content.split("\n")
 129 |         symbols = []  # List to store all symbols
 130 |         symbol_stack = []  # Stack for tracking nested symbols
 131 |         current_doc_comments = []  # List to store current doc comments
 132 |         current_modifiers = set()  # Set to store current modifiers
 133 |         brace_depth = 0  # Counter for tracking brace depth
 134 |         self.in_class = False  # Initialize class context
 136 |         def pop_symbols_up_to(depth: int, line_idx: int):
 138 |             while symbol_stack and symbol_stack[-1].brace_depth >= depth:
 139 |                 symbol = symbol_stack.pop()
 140 |                 symbol.end_line = line_idx
 141 |                 if symbol_stack:
 143 |                     symbol_stack[-1].children.append(symbol)
 145 |                     if symbol.kind == "method":
 146 |                         continue
 147 |                 symbols.append(symbol)
 148 |                 if symbol.kind == "class":
 149 |                     self.in_class = False
 151 |         i = 0
 152 |         while i < len(lines):
 153 |             line = lines[i].strip()
 154 |             if not line:
 155 |                 i += 1
 156 |                 continue
 159 |             if line.startswith("/**"):
 160 |                 current_doc_comments.append(line)
 161 |                 while i + 1 < len(lines) and "*/" not in lines[i]:
 162 |                     i += 1
 163 |                     current_doc_comments.append(lines[i].strip())
 164 |                 i += 1
 165 |                 continue
 168 |             if line.startswith("//") or line.startswith("/*"):
 169 |                 i += 1
 170 |                 continue
 173 |             if line.startswith("@"):
 174 |                 current_modifiers.add(line)
 175 |                 i += 1
 176 |                 continue
 179 |             brace_depth += line.count("{") - line.count("}")
 182 |             matched = False
 183 |             for pattern in self._setup_patterns():
 184 |                 match = pattern.match(line)
 185 |                 if match:
 186 |                     matched = True
 187 |                     name = match.group("symbol_name")
 188 |                     if not name:
 189 |                         continue
 192 |                     modifiers = set(current_modifiers)
 193 |                     if line.startswith("export"):
 194 |                         modifiers.add("export")
 195 |                     if line.startswith("async"):
 196 |                         modifiers.add("async")
 197 |                     if line.startswith("const"):
 198 |                         modifiers.add("const")
 199 |                     if line.startswith("let"):
 200 |                         modifiers.add("let")
 201 |                     if line.startswith("var"):
 202 |                         modifiers.add("var")
 203 |                     current_modifiers.clear()
 206 |                     kind = self._get_kind(pattern)
 209 |                     symbol = CodeSymbol(
 210 |                         name=name,
 211 |                         kind=kind,
 212 |                         start_line=i + 1,
 213 |                         end_line=0,  # Will be set when popped
 214 |                         modifiers=modifiers,
 215 |                         docstring="\n".join(current_doc_comments) if current_doc_comments else None,
 216 |                         children=[],
 217 |                     )
 218 |                     symbol.brace_depth = brace_depth
 219 |                     current_doc_comments.clear()
 222 |                     if kind == "class":
 223 |                         self.in_class = True
 226 |                     symbol_stack.append(symbol)
 227 |                     break
 230 |             if "}" in line:
 231 |                 pop_symbols_up_to(brace_depth + 1, i + 1)
 233 |             i += 1
 236 |         pop_symbols_up_to(0, len(lines))
 239 |         declarations = []
 240 |         for symbol in symbols:
 241 |             declarations.append(
 242 |                 Declaration(
 243 |                     kind=symbol.kind,
 244 |                     name=symbol.name,
 245 |                     start_line=symbol.start_line,
 246 |                     end_line=symbol.end_line,
 247 |                     modifiers=symbol.modifiers,
 248 |                     docstring=symbol.docstring,
 249 |                 )
 250 |             )
 252 |             for child in symbol.children:
 253 |                 if child.kind == "method":
 254 |                     declarations.append(
 255 |                         Declaration(
 256 |                             kind=child.kind,
 257 |                             name=child.name,
 258 |                             start_line=child.start_line,
 259 |                             end_line=child.end_line,
 260 |                             modifiers=child.modifiers,
 261 |                             docstring=child.docstring,
 262 |                         )
 263 |                     )
 265 |         return declarations
```

---
### File: ./codeconcat/parser/language_parsers/python_parser.py
#### Summary
```
File: python_parser.py
Language: python
```

```python
   3 | import re
   4 | from typing import List, Optional
   6 | from codeconcat.base_types import Declaration, ParsedFileData
   7 | from codeconcat.parser.language_parsers.base_parser import BaseParser, CodeSymbol
  10 | def parse_python(file_path: str, content: str) -> ParsedFileData:
  12 |     parser = PythonParser()
  13 |     declarations = parser.parse(content)
  14 |     return ParsedFileData(
  15 |         file_path=file_path, language="python", content=content, declarations=declarations
  16 |     )
  19 | class PythonParser(BaseParser):
  22 |     def __init__(self):
  23 |         super().__init__()
  24 |         self._setup_patterns()
  26 |     def _setup_patterns(self):
  28 |         Enhanced patterns for Python:
  29 |         - We define one pattern for 'class' and 'function' that can handle decorators,
  30 |           but we rely on the logic in parse() to gather multiple lines if needed.
  33 |         name = r"[a-zA-Z_][a-zA-Z0-9_]*"
  35 |         self.patterns = {
  36 |             "class": re.compile(
  37 |                 r"^class\s+(?P<n>" + name + r")"  # Class name
  38 |                 r"(?:\s*\([^)]*\))?"  # Optional parent class
  39 |                 r"\s*:"  # Class definition end
  40 |             ),
  41 |             "function": re.compile(
  42 |                 r"^(?:async\s+)?def\s+(?P<n>" + name + r")"  # Function name with optional async
  43 |                 r"\s*\([^)]*\)?"  # Function parameters, optional closing parenthesis
  44 |                 r"\s*(?:->[^:]+)?"  # Optional return type
  45 |                 r"\s*:?"  # Optional colon (for multi-line definitions)
  46 |             ),
  47 |             "variable": re.compile(
  48 |                 r"^(?P<n>[a-z_][a-zA-Z0-9_]*)\s*"  # Variable name
  49 |                 r"(?::\s*[^=\s]+)?"  # Optional type annotation
  50 |                 r"\s*=\s*[^=]"  # Assignment but not comparison
  51 |             ),
  52 |             "constant": re.compile(
  53 |                 r"^(?P<n>[A-Z][A-Z0-9_]*)\s*"  # Constant name
  54 |                 r"(?::\s*[^=\s]+)?"  # Optional type annotation
  55 |                 r"\s*=\s*[^=]"  # Assignment but not comparison
  56 |             ),
  57 |             "decorator": re.compile(
  58 |                 r"^@(?P<n>[a-zA-Z_][\w.]*)(?:\s*\([^)]*\))?"  # Decorator with optional args
  59 |             )
  60 |         }
  63 |         self.block_start = ":"
  64 |         self.block_end = None
  65 |         self.line_comment = "#"
  66 |         self.block_comment_start = '"""'
  67 |         self.block_comment_end = '"""'
  70 |         self.modifiers = {
  71 |             "@classmethod",
  72 |             "@staticmethod",
  73 |             "@property",
  74 |             "@abstractmethod",
  75 |         }
  77 |     def parse(self, content: str) -> List[Declaration]:
  79 |         lines = content.split("\n")
  80 |         self.symbols = []
  81 |         self.current_symbol = None
  82 |         self.symbol_stack = []
  85 |         pending_decorators = []
  86 |         current_def_lines = []
  87 |         in_multiline_decorator = False
  88 |         in_function_def = False
  89 |         function_start_line = 0
  91 |         i = 0
  92 |         while i < len(lines):
  93 |             line = lines[i]
  94 |             stripped = line.strip()
  97 |             if not stripped or stripped.startswith("#"):
  98 |                 i += 1
  99 |                 continue
 102 |             if stripped.startswith("@"):
 103 |                 pending_decorators.append(stripped)
 104 |                 if "(" in stripped and ")" not in stripped:
 105 |                     in_multiline_decorator = True
 106 |                 i += 1
 107 |                 continue
 109 |             if in_multiline_decorator:
 110 |                 pending_decorators[-1] += " " + stripped
 111 |                 if ")" in stripped:
 112 |                     in_multiline_decorator = False
 113 |                 i += 1
 114 |                 continue
 117 |             indent = len(line) - len(stripped)
 120 |             while self.symbol_stack and indent <= (len(lines[self.symbol_stack[-1].start_line - 1]) - len(lines[self.symbol_stack[-1].start_line - 1].lstrip())):
 121 |                 self.symbol_stack.pop()
 124 |             if in_function_def:
 125 |                 current_def_lines.append(line)
 126 |                 if stripped.endswith(":"):
 128 |                     combined_def = " ".join(l.strip() for l in current_def_lines)
 130 |                     match = self.patterns["function"].match(combined_def)
 131 |                     if not match:
 133 |                         first_line = current_def_lines[0].strip()
 134 |                         match = self.patterns["function"].match(first_line)
 136 |                     if match:
 137 |                         name = match.group("n")
 138 |                         end_line = self._find_block_end(lines, i, indent)
 139 |                         if end_line <= i:
 140 |                             end_line = i + 1
 143 |                         docstring = self.extract_docstring(lines, i + 1, end_line)
 146 |                         symbol = CodeSymbol(
 147 |                             name=name,
 148 |                             kind="function",
 149 |                             start_line=function_start_line + 1,
 150 |                             end_line=end_line + 1,
 151 |                             modifiers=set(pending_decorators),
 152 |                             docstring=docstring,
 153 |                             parent=self.symbol_stack[-1] if self.symbol_stack else None,
 154 |                             children=[]
 155 |                         )
 158 |                         if self.symbol_stack and symbol.parent:
 159 |                             symbol.parent.children.append(symbol)
 160 |                         else:
 161 |                             self.symbols.append(symbol)
 164 |                         self.symbol_stack.append(symbol)
 167 |                     in_function_def = False
 168 |                     current_def_lines = []
 169 |                     pending_decorators = []
 170 |                 i += 1
 171 |                 continue
 174 |             matched = False
 175 |             for kind, pattern in self.patterns.items():
 176 |                 match = pattern.match(stripped)
 177 |                 if not match:
 178 |                     continue
 180 |                 name = match.group("n")
 182 |                 if kind == "function":
 184 |                     if "(" in stripped and ")" not in stripped or not stripped.endswith(":"):
 185 |                         in_function_def = True
 186 |                         current_def_lines = [line]
 187 |                         function_start_line = i
 188 |                         matched = True
 189 |                         break
 190 |                     else:
 191 |                         end_line = self._find_block_end(lines, i, indent)
 192 |                         if end_line <= i:
 193 |                             end_line = i + 1
 196 |                         docstring = self.extract_docstring(lines, i + 1, end_line)
 198 |                         symbol = CodeSymbol(
 199 |                             name=name,
 200 |                             kind="function",
 201 |                             start_line=i + 1,
 202 |                             end_line=end_line + 1,
 203 |                             modifiers=set(pending_decorators),
 204 |                             docstring=docstring,
 205 |                             parent=self.symbol_stack[-1] if self.symbol_stack else None,
 206 |                             children=[]
 207 |                         )
 210 |                         if self.symbol_stack and symbol.parent:
 211 |                             symbol.parent.children.append(symbol)
 212 |                         else:
 213 |                             self.symbols.append(symbol)
 216 |                         self.symbol_stack.append(symbol)
 219 |                         pending_decorators = []
 220 |                         matched = True
 221 |                         i += 1
 222 |                         break
 223 |                 elif kind == "class":
 224 |                     end_line = self._find_block_end(lines, i, indent)
 225 |                     if end_line <= i:
 226 |                         end_line = i + 1
 229 |                     docstring = self.extract_docstring(lines, i + 1, end_line)
 231 |                     symbol = CodeSymbol(
 232 |                         name=name,
 233 |                         kind=kind,
 234 |                         start_line=i + 1,
 235 |                         end_line=end_line + 1,
 236 |                         modifiers=set(pending_decorators),
 237 |                         docstring=docstring,
 238 |                         parent=self.symbol_stack[-1] if self.symbol_stack else None,
 239 |                         children=[]
 240 |                     )
 242 |                 else:  # variable or constant
 243 |                     symbol = CodeSymbol(
 244 |                         name=name,
 245 |                         kind=kind,
 246 |                         start_line=i + 1,
 247 |                         end_line=i + 1,
 248 |                         modifiers=set(),
 249 |                         parent=self.symbol_stack[-1] if self.symbol_stack else None,
 250 |                         children=[]
 251 |                     )
 254 |                 if self.symbol_stack and symbol.parent:
 255 |                     symbol.parent.children.append(symbol)
 256 |                 else:
 257 |                     self.symbols.append(symbol)
 260 |                 if kind in ("class", "function"):
 261 |                     self.symbol_stack.append(symbol)
 264 |                 pending_decorators = []
 265 |                 matched = True
 266 |                 i += 1
 267 |                 break
 269 |             if not matched and not in_function_def:
 270 |                 pending_decorators = []
 271 |                 i += 1
 274 |         def convert_symbols(symbols: List[CodeSymbol]) -> List[Declaration]:
 275 |             declarations = []
 276 |             for symbol in symbols:
 277 |                 declarations.append(Declaration(
 278 |                     kind=symbol.kind,
 279 |                     name=symbol.name,
 280 |                     start_line=symbol.start_line,
 281 |                     end_line=symbol.end_line,
 282 |                     modifiers=symbol.modifiers,
 283 |                     docstring=symbol.docstring
 284 |                 ))
 285 |                 if symbol.children:
 286 |                     declarations.extend(convert_symbols(symbol.children))
 287 |             return declarations
 289 |         return convert_symbols(self.symbols)
 291 |     def _find_block_end(self, lines: List[str], start: int, base_indent: int) -> int:
 293 |         i = start + 1
 294 |         max_lines = len(lines)
 297 |         if i >= max_lines:
 298 |             return start
 301 |         while i < max_lines and not lines[i].strip():
 302 |             i += 1
 305 |         if i >= max_lines:
 306 |             return max_lines - 1
 309 |         first_line = lines[i]
 310 |         block_indent = len(first_line) - len(first_line.lstrip())
 313 |         if block_indent <= base_indent:
 314 |             return start
 316 |         while i < max_lines:
 317 |             line = lines[i].rstrip()
 320 |             if not line:
 321 |                 i += 1
 322 |                 continue
 325 |             indent = len(line) - len(line.lstrip())
 328 |             if indent <= base_indent:
 329 |                 return i - 1
 331 |             i += 1
 334 |         return max_lines - 1
```

---
### File: ./codeconcat/parser/language_parsers/base_parser.py
#### Summary
```
File: base_parser.py
Language: python
```

```python
   3 | import re
   4 | from abc import ABC, abstractmethod
   5 | from dataclasses import dataclass
   6 | from typing import Dict, List, Optional, Pattern, Set, Tuple
   8 | @dataclass
   9 | class CodeSymbol:
  10 |     name: str
  11 |     kind: str
  12 |     start_line: int
  13 |     end_line: int
  14 |     modifiers: Set[str]
  15 |     parent: Optional["CodeSymbol"] = None
  16 |     children: List["CodeSymbol"] = None
  17 |     docstring: Optional[str] = None
  19 |     def __post_init__(self):
  20 |         if self.children is None:
  21 |             self.children = []
  23 | class BaseParser(ABC):
  25 |     BaseParser defines a minimal interface and partial logic for line-based scanning
  26 |     and comment extraction. Subclasses typically override _setup_patterns() and parse().
  29 |     def __init__(self):
  30 |         self.symbols: List[CodeSymbol] = []
  31 |         self.current_symbol: Optional[CodeSymbol] = None
  32 |         self.symbol_stack: List[CodeSymbol] = []
  33 |         self._setup_patterns()
  35 |     @abstractmethod
  36 |     def _setup_patterns(self):
  37 |         self.patterns: Dict[str, Pattern] = {}
  38 |         self.modifiers: Set[str] = set()
  39 |         self.block_start: str = "{"
  40 |         self.block_end: str = "}"
  41 |         self.line_comment: str = "//"
  42 |         self.block_comment_start: str = "/*"
  43 |         self.block_comment_end: str = "*/"
  45 |     def parse(self, content: str) -> List[Tuple[str, int, int]]:
  47 |         A default naive parse that tries to identify code symbols via line-based scanning.
  48 |         Subclasses often override parse() with a more language-specific approach.
  50 |         self.symbols = []
  51 |         self.current_symbol = None
  52 |         self.symbol_stack = []
  54 |         lines = content.split("\n")
  55 |         in_comment = False
  56 |         comment_buffer = []
  58 |         brace_count = 0  # naive brace count
  60 |         for i, line in enumerate(lines):
  61 |             stripped_line = line.strip()
  64 |             if self.block_comment_start in line and not in_comment:
  65 |                 in_comment = True
  66 |                 comment_start = line.index(self.block_comment_start)
  67 |                 comment_buffer.append(line[comment_start + len(self.block_comment_start):])
  68 |                 continue
  70 |             if in_comment:
  71 |                 if self.block_comment_end in line:
  72 |                     in_comment = False
  73 |                     comment_end = line.index(self.block_comment_end)
  74 |                     comment_buffer.append(line[:comment_end])
  76 |                     comment_buffer = []
  77 |                 else:
  78 |                     comment_buffer.append(line)
  79 |                 continue
  82 |             if stripped_line.startswith(self.line_comment):
  83 |                 continue
  86 |             brace_count += line.count(self.block_start) - line.count(self.block_end)
  89 |             if not self.current_symbol:
  90 |                 for kind, pattern in self.patterns.items():
  91 |                     match = pattern.match(line)
  92 |                     if match:
  94 |                         if "name" in match.groupdict():
  95 |                             name = match.group("name") or ""
  96 |                         else:
  97 |                             continue
 100 |                         mods = set()
 101 |                         if "modifiers" in match.groupdict() and match.group("modifiers"):
 102 |                             raw_mods = match.group("modifiers").split()
 103 |                             mods = {m.strip() for m in raw_mods if m.strip()}
 105 |                         symbol = CodeSymbol(
 106 |                             name=name,
 107 |                             kind=kind,
 108 |                             start_line=i,
 109 |                             end_line=i,
 110 |                             modifiers=mods & self.modifiers,
 111 |                         )
 112 |                         if self.symbol_stack:
 113 |                             symbol.parent = self.symbol_stack[-1]
 114 |                             self.symbol_stack[-1].children.append(symbol)
 116 |                         self.current_symbol = symbol
 117 |                         self.symbol_stack.append(symbol)
 118 |                         break
 120 |             if self.current_symbol and brace_count == 0:
 121 |                 if (self.block_end in line) or (";" in line):
 122 |                     self.current_symbol.end_line = i
 123 |                     self.symbols.append(self.current_symbol)
 124 |                     if self.symbol_stack:
 125 |                         self.symbol_stack.pop()
 126 |                     self.current_symbol = self.symbol_stack[-1] if self.symbol_stack else None
 128 |         return [(s.name, s.start_line, s.end_line) for s in self.symbols]
 130 |     def _create_pattern(self, base_pattern: str, modifiers: Optional[List[str]] = None) -> Pattern:
 131 |         if modifiers:
 132 |             modifier_pattern = f"(?:{'|'.join(modifiers)})\\s+"
 133 |             return re.compile(f"^\\s*(?:{modifier_pattern})?{base_pattern}")
 134 |         return re.compile(f"^\\s*{base_pattern}")
 136 |     @staticmethod
 137 |     def extract_docstring(lines: List[str], start: int, end: int) -> Optional[str]:
 139 |         Example extraction for docstring-like text between triple quotes or similar.
 140 |         Subclasses can override or use as needed.
 142 |         for i in range(start, min(end + 1, len(lines))):
 143 |             line = lines[i].strip()
 144 |             if line.startswith('"""') or line.startswith("'''"):
 145 |                 doc_lines = []
 146 |                 quote = line[:3]
 147 |                 if line.endswith(quote) and len(line) > 3:
 148 |                     return line[3:-3].strip()
 149 |                 doc_lines.append(line[3:])
 150 |                 for j in range(i + 1, end + 1):
 151 |                     line2 = lines[j].strip()
 152 |                     if line2.endswith(quote):
 153 |                         doc_lines.append(line2[:-3])
 154 |                         return "\n".join(doc_lines).strip()
 155 |                     doc_lines.append(line2)
 156 |         return None
```

---
### File: ./codeconcat/parser/language_parsers/java_parser.py
#### Summary
```
File: java_parser.py
Language: python
```

```python
   3 | import re
   4 | from typing import List, Optional, Set
   5 | from codeconcat.base_types import Declaration, ParsedFileData
   6 | from codeconcat.parser.language_parsers.base_parser import BaseParser, CodeSymbol
   8 | def parse_java(file_path: str, content: str) -> Optional[ParsedFileData]:
   9 |     parser = JavaParser()
  10 |     declarations = parser.parse(content)
  11 |     return ParsedFileData(
  12 |         file_path=file_path,
  13 |         language="java",
  14 |         content=content,
  15 |         declarations=declarations
  16 |     )
  18 | class JavaParser(BaseParser):
  19 |     def _setup_patterns(self):
  21 |         We'll define patterns for class, interface, method, field (rough).
  22 |         If the line includes `{` we'll parse the block. We handle constructor vs. method by checking if
  23 |         there's a return type.
  25 |         self.patterns = {
  26 |             "class": re.compile(
  27 |                 r"^[^/]*"
  28 |                 r"(?:public|private|protected|static|final|abstract\s+)*"
  29 |                 r"class\s+(?P<name>[A-Z][a-zA-Z0-9_]*)"
  30 |                 r"(?:\s+extends\s+[a-zA-Z0-9_.]+)?"
  31 |                 r"(?:\s+implements\s+[a-zA-Z0-9_.]+(?:\s*,\s*[a-zA-Z0-9_.]+)*)?"
  32 |                 r"\s*\{"
  33 |             ),
  34 |             "interface": re.compile(
  35 |                 r"^[^/]*"
  36 |                 r"(?:public|private|protected|static\s+)*"
  37 |                 r"interface\s+(?P<name>[A-Z][a-zA-Z0-9_]*)"
  38 |                 r"(?:\s+extends\s+[a-zA-Z0-9_.]+(?:\s*,\s*[a-zA-Z0-9_.]+)*)?"
  39 |                 r"\s*\{"
  40 |             ),
  41 |             "method": re.compile(
  42 |                 r"^[^/]*"
  43 |                 r"(?:public|private|protected|static|final|abstract|synchronized\s+)*"
  44 |                 r"(?:[a-zA-Z_][a-zA-Z0-9_.<>\[\]\s]*\s+)+"   # return type
  45 |                 r"(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)"         # method or constructor name
  46 |                 r"\s*\([^)]*\)\s*"
  47 |                 r"(?:throws\s+[a-zA-Z0-9_.]+(?:\s*,\s*[a-zA-Z0-9_.]+)*)?"
  48 |                 r"\s*\{"
  49 |             ),
  50 |             "field": re.compile(
  51 |                 r"^[^/]*"
  52 |                 r"(?:public|private|protected|static|final|volatile|transient\s+)*"
  53 |                 r"[a-zA-Z_][a-zA-Z0-9_<>\[\]\s]*\s+"
  54 |                 r"(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)\s*;"
  55 |             ),
  56 |         }
  58 |         self.block_start = "{"
  59 |         self.block_end = "}"
  60 |         self.line_comment = "//"
  61 |         self.block_comment_start = "/*"
  62 |         self.block_comment_end = "*/"
  64 |     def parse(self, content: str) -> List[Declaration]:
  65 |         lines = content.split("\n")
  66 |         symbols: List[CodeSymbol] = []
  67 |         i = 0
  68 |         line_count = len(lines)
  70 |         while i < line_count:
  71 |             line = lines[i].strip()
  72 |             if not line or line.startswith("//"):
  73 |                 i += 1
  74 |                 continue
  76 |             matched = False
  77 |             for kind, pattern in self.patterns.items():
  78 |                 match = pattern.match(line)
  79 |                 if match:
  80 |                     name = match.group("name")
  82 |                     if kind == "method":
  86 |                         pass
  88 |                     block_end = i
  89 |                     if kind in ("class", "interface", "method"):
  90 |                         block_end = self._find_block_end(lines, i)
  92 |                     symbol = CodeSymbol(
  93 |                         kind=kind,
  94 |                         name=name,
  95 |                         start_line=i,
  96 |                         end_line=block_end,
  97 |                         modifiers=set(),
  98 |                     )
  99 |                     symbols.append(symbol)
 100 |                     i = block_end
 101 |                     matched = True
 102 |                     break
 103 |             if not matched:
 104 |                 i += 1
 106 |         declarations = []
 107 |         for sym in symbols:
 108 |             declarations.append(Declaration(
 109 |                 kind=sym.kind,
 110 |                 name=sym.name,
 111 |                 start_line=sym.start_line + 1,
 112 |                 end_line=sym.end_line + 1,
 113 |                 modifiers=sym.modifiers
 114 |             ))
 115 |         return declarations
 117 |     def _find_block_end(self, lines: List[str], start: int) -> int:
 118 |         line = lines[start]
 119 |         if "{" not in line:
 120 |             return start
 121 |         brace_count = line.count("{") - line.count("}")
 122 |         if brace_count <= 0:
 123 |             return start
 124 |         for i in range(start + 1, len(lines)):
 125 |             l2 = lines[i].strip()
 126 |             if l2.startswith("//"):
 127 |                 continue
 128 |             brace_count += l2.count("{") - l2.count("}")
 129 |             if brace_count <= 0:
 130 |                 return i
 131 |         return len(lines) - 1
```

---
### File: ./codeconcat/parser/language_parsers/cpp_parser.py
#### Summary
```
File: cpp_parser.py
Language: python
```

```python
   3 | import re
   4 | from typing import List, Optional
   5 | from codeconcat.base_types import Declaration, ParsedFileData
   6 | from codeconcat.parser.language_parsers.base_parser import BaseParser, CodeSymbol
   8 | def parse_cpp_code(file_path: str, content: str) -> Optional[ParsedFileData]:
   9 |     parser = CppParser()
  10 |     declarations = parser.parse(content)
  11 |     return ParsedFileData(
  12 |         file_path=file_path,
  13 |         language="cpp",
  14 |         content=content,
  15 |         declarations=declarations
  16 |     )
  19 | def parse_cpp(file_path: str, content: str) -> Optional[ParsedFileData]:
  20 |     return parse_cpp_code(file_path, content)
  22 | class CppParser(BaseParser):
  23 |     def __init__(self):
  24 |         super().__init__()
  25 |         self._setup_patterns()
  27 |     def _setup_patterns(self):
  29 |         Define the main regex patterns for classes, structs, enums, functions,
  30 |         namespaces, typedefs, usings, and forward declarations.
  33 |         identifier = r"[a-zA-Z_]\w*"
  34 |         qualified_id = rf"(?:{identifier}::)*{identifier}"
  37 |         self.class_pattern = re.compile(
  38 |             r"""
  39 |             ^[^\#/]*?                    # skip if line starts with # or / (comment), handled later
  40 |             (?:template\s*<[^>]*>\s*)?   # optional template
  41 |             (?:class|struct)\s+
  42 |             (?P<name>[a-zA-Z_]\w*)       # capture the class/struct name
  43 |             (?:\s*:[^{]*)?              # optional inheritance, up to but not including brace
  44 |             \s*{                       # opening brace
  46 |             re.VERBOSE
  47 |         )
  50 |         self.forward_decl_pattern = re.compile(
  51 |             r"""
  52 |             ^[^\#/]*?
  53 |             (?:class|struct|union|enum)\s+
  54 |             (?P<name>[a-zA-Z_]\w*)\s*;
  56 |             re.VERBOSE
  57 |         )
  60 |         self.enum_pattern = re.compile(
  61 |             r"""
  62 |             ^[^\#/]*?
  63 |             enum\s+
  64 |             (?:class\s+)?               # enum class?
  65 |             (?P<name>[a-zA-Z_]\w*)
  66 |             (?:\s*:\s+[^\s{]+)?         # optional base type
  67 |             \s*{                       # opening brace
  69 |             re.VERBOSE
  70 |         )
  76 |         self.function_pattern = re.compile(
  77 |             r"""
  78 |             ^[^\#/]*?                    # skip if line starts with # or / (comment), handled later
  79 |             (?:template\s*<[^>]*>\s*)?   # optional template
  80 |             (?:virtual|static|inline|constexpr|explicit|friend\s+)?  # optional specifiers
  81 |             (?:""" + qualified_id + r"""(?:<[^>]+>)?[&*\s]+)*        # optional return type with nested templates
  82 |             (?P<name>                                      # function name capture
  83 |                 ~?[a-zA-Z_]\w*                             # normal name or destructor ~Foo
  84 |                 |operator\s*(?:[^\s\(]+|\(.*?\))          # operator overload
  85 |             )
  86 |             \s*\([^\){;]*\)                                # function params up to ) but not including brace or semicolon
  87 |             (?:\s*const)?                                   # optional const
  88 |             (?:\s*noexcept)?                                # optional noexcept
  89 |             (?:\s*=\s*(?:default|delete|0))?                # optional = default/delete/pure virtual
  90 |             \s*(?:{|;)                                    # must end with { or ;
  92 |             re.VERBOSE
  93 |         )
  96 |         self.namespace_pattern = re.compile(
  97 |             r"""
  98 |             ^[^\#/]*?
  99 |             (?:inline\s+)?         # optional inline
 100 |             namespace\s+
 101 |             (?P<name>[a-zA-Z_]\w*) # namespace name
 102 |             \s*{                  # opening brace
 104 |             re.VERBOSE
 105 |         )
 108 |         self.typedef_pattern = re.compile(
 109 |             r"""
 110 |             ^[^\#/]*?
 111 |             typedef\s+
 112 |             (?:[^;]+?                   # capture everything up to the identifier
 113 |               \s+                       # must have whitespace before identifier
 114 |               (?:\(\s*\*\s*)?          # optional function pointer
 115 |             )
 116 |             (?P<name>[a-zA-Z_]\w*)     # identifier
 117 |             (?:\s*\)[^;]*)?            # rest of function pointer if present
 118 |             \s*;                        # end with semicolon
 120 |             re.VERBOSE
 121 |         )
 124 |         self.using_pattern = re.compile(
 125 |             r"""
 126 |             ^[^\#/]*?
 127 |             using\s+
 128 |             (?P<name>[a-zA-Z_]\w*)
 129 |             \s*=\s*[^;]+;
 131 |             re.VERBOSE
 132 |         )
 134 |         self.patterns = {
 135 |             "class":      self.class_pattern,
 136 |             "forward_decl": self.forward_decl_pattern,
 137 |             "enum":       self.enum_pattern,
 138 |             "function":   self.function_pattern,
 139 |             "namespace":  self.namespace_pattern,
 140 |             "typedef":    self.typedef_pattern,
 141 |             "using":      self.using_pattern,
 142 |         }
 145 |         self.block_start = "{"
 146 |         self.block_end = "}"
 147 |         self.line_comment = "//"
 148 |         self.block_comment_start = "/*"
 149 |         self.block_comment_end = "*/"
 151 |     def parse(self, content: str) -> List[Declaration]:
 153 |         Main parse method:
 154 |         1) Remove block comments.
 155 |         2) Split by lines.
 156 |         3) For each line, strip preprocessor lines (#...), line comments, etc.
 157 |         4) Match patterns in a loop and accumulate symbols.
 158 |         5) For anything with a block, find the end of the block with _find_block_end.
 159 |         6) Convert collected CodeSymbol objects -> Declaration objects.
 162 |         content_no_block = self._remove_block_comments(content)
 163 |         lines = content_no_block.split("\n")
 165 |         symbols: List[CodeSymbol] = []
 166 |         i = 0
 167 |         line_count = len(lines)
 169 |         while i < line_count:
 170 |             raw_line = lines[i]
 171 |             line_stripped = raw_line.strip()
 174 |             if (not line_stripped
 175 |                 or line_stripped.startswith("//")
 176 |                 or line_stripped.startswith("#")):
 177 |                 i += 1
 178 |                 continue
 181 |             comment_pos = raw_line.find("//")
 182 |             if comment_pos >= 0:
 183 |                 raw_line = raw_line[:comment_pos]
 185 |             raw_line_stripped = raw_line.strip()
 186 |             if not raw_line_stripped:
 187 |                 i += 1
 188 |                 continue
 190 |             matched_something = False
 193 |             for kind, pattern in self.patterns.items():
 194 |                 match = pattern.match(raw_line_stripped)
 195 |                 if match:
 196 |                     name = match.group("name")
 197 |                     block_end = i
 199 |                     if kind in ["class", "enum", "namespace", "function"]:
 201 |                         if "{" in raw_line_stripped:
 202 |                             block_end = self._find_block_end(lines, i)
 203 |                         else:
 205 |                             block_end = i
 208 |                     symbol = CodeSymbol(
 209 |                         kind=kind,
 210 |                         name=name,
 211 |                         start_line=i,
 212 |                         end_line=block_end,
 213 |                         modifiers=set(),
 214 |                     )
 215 |                     symbols.append(symbol)
 216 |                     i = block_end + 1
 217 |                     matched_something = True
 218 |                     break
 220 |             if not matched_something:
 221 |                 i += 1
 224 |         declarations: List[Declaration] = []
 225 |         for sym in symbols:
 226 |             decl = Declaration(
 227 |                 kind=sym.kind,
 228 |                 name=sym.name,
 229 |                 start_line=sym.start_line + 1,
 230 |                 end_line=sym.end_line + 1,
 231 |                 modifiers=sym.modifiers,
 232 |             )
 233 |             declarations.append(decl)
 235 |         return declarations
 237 |     def _remove_block_comments(self, text: str) -> str:
 239 |         Remove all /* ... */ comments (including multi-line).
 240 |         Simple approach: repeatedly find the first /* and the next */, remove them,
 241 |         and continue until none remain.
 243 |         pattern = re.compile(r"/\*.*?\*/", re.DOTALL)
 244 |         return re.sub(pattern, "", text)
 246 |     def _find_block_end(self, lines: List[str], start: int) -> int:
 248 |         Find the end of a block that starts at 'start' if there's an unmatched '{'.
 249 |         We'll count braces until balanced or until we run out of lines.
 250 |         We'll skip lines that start with '#' as they are preprocessor directives (not code).
 253 |         line = lines[start]
 254 |         brace_count = 0
 257 |         comment_pos = line.find("//")
 258 |         if comment_pos >= 0:
 259 |             line = line[:comment_pos]
 261 |         brace_count += line.count("{") - line.count("}")
 264 |         if brace_count <= 0:
 265 |             return start
 267 |         n = len(lines)
 268 |         for i in range(start + 1, n):
 269 |             l = lines[i]
 272 |             if l.strip().startswith("#"):
 273 |                 continue
 276 |             comment_pos = l.find("//")
 277 |             if comment_pos >= 0:
 278 |                 l = l[:comment_pos]
 280 |             brace_count += l.count("{") - l.count("}")
 281 |             if brace_count <= 0:
 282 |                 return i
 284 |         return n - 1
```

---
### File: ./codeconcat/parser/language_parsers/r_parser.py
#### Summary
```
File: r_parser.py
Language: python
```

```python
   5 | import re
   6 | from typing import List, Optional, Set, Dict
   7 | from codeconcat.base_types import Declaration, ParsedFileData
   8 | from codeconcat.parser.language_parsers.base_parser import BaseParser, CodeSymbol
  10 | def parse_r(file_path: str, content: str) -> Optional[ParsedFileData]:
  11 |     parser = RParser()
  12 |     declarations = parser.parse(content)
  13 |     return ParsedFileData(
  14 |         file_path=file_path,
  15 |         language="r",
  16 |         content=content,
  17 |         declarations=declarations
  18 |     )
  20 | class RParser(BaseParser):
  22 |     A regex-based R parser that attempts to capture:
  23 |       - Functions (including various assignment operators and nested definitions)
  24 |       - Classes (S3, S4, R6, Reference)
  25 |       - Methods (S3, S4, R6, $-notation, dot-notation)
  26 |       - Package imports (library/require)
  27 |       - Roxygen2 modifiers
  28 |     Then it scans block contents recursively for nested definitions.
  31 |     def __init__(self):
  32 |         super().__init__()
  33 |         self._setup_patterns()
  35 |     def _setup_patterns(self):
  37 |         Compile all regex patterns needed.
  38 |         We'll allow for all assignment operators: <-, <<-, =, ->, ->>, :=
  39 |         We'll handle S3, S4, R6, reference classes, plus roxygen modifiers.
  44 |         qualified_name = r"[a-zA-Z_]\w*(?:[.$][a-zA-Z_]\w*)*"
  48 |         self.method_pattern = re.compile(
  49 |             rf"""
  50 |             ^\s*
  51 |             (?:
  53 |                 (?P<dot_name>{qualified_name}\.[a-zA-Z_]\w*)
  54 |                 \s*(?:<<?-|=|->|->>|:=)
  55 |                 \s*function\s*\(
  56 |                 |
  58 |                 (?P<dollar_obj>{qualified_name})\$(?P<dollar_method>[a-zA-Z_]\w*)
  59 |                 \s*(?:<<?-|=|->|->>|:=)
  60 |                 \s*function\s*\(
  61 |                 |
  63 |                 setMethod\(\s*["'](?P<s4_name>[^"']+)["']
  64 |             )
  66 |             re.VERBOSE,
  67 |         )
  70 |         self.function_pattern = re.compile(
  71 |             rf"""
  72 |             ^\s*
  73 |             (?:
  78 |                (?P<fname1>{qualified_name})\s*(?:<<?-|=|:=)\s*function\s*\(
  79 |                |
  82 |                function\s*\([^)]*\)\s*(?:->|->>)\s*(?P<fname2>{qualified_name})
  83 |             )
  85 |             re.VERBOSE,
  86 |         )
  90 |         self.class_pattern = re.compile(
  91 |             rf"""
  92 |             ^\s*
  93 |             (?:
  97 |                 (?:setClass|setRefClass|R6Class)\(\s*["'](?P<cname1>[a-zA-Z_]\w*)["']
  98 |                 |
 100 |                 (?P<cname2>{qualified_name})\s*(?:<<?-|=|:=)\s*(?:setRefClass|R6Class)\(\s*["'](?P<cname3>[a-zA-Z_]\w*)["']
 101 |             )
 103 |             re.VERBOSE,
 104 |         )
 107 |         self.package_pattern = re.compile(
 108 |             rf"""
 109 |             ^\s*
 110 |             (?:library|require)\s*\(\s*
 111 |             (?:
 112 |                 ["'](?P<pkg1>[^"']+)["']
 113 |                 |
 114 |                 (?P<pkg2>[a-zA-Z_]\w*(?:\.[a-zA-Z_]\w*)*)
 115 |             )
 117 |             re.VERBOSE,
 118 |         )
 121 |         self.block_start = "{"
 122 |         self.block_end = "}"
 123 |         self.line_comment = "#"
 124 |         self.block_comment_start = "#["
 125 |         self.block_comment_end = "]#"
 127 |     def parse(self, content: str) -> List[Declaration]:
 129 |         Main parse entry:
 130 |           1) Merge multiline function/class assignments
 131 |           2) Parse top-level lines
 133 |         raw_lines = content.split("\n")
 135 |         merged_lines = self._merge_multiline_assignments(raw_lines, also_for_classes=True)
 137 |         symbols = self._parse_block(merged_lines, 0, len(merged_lines))
 140 |         declarations = []
 141 |         seen = set()
 142 |         for sym in symbols:
 143 |             key = (sym.kind, sym.name, sym.start_line, sym.end_line)
 144 |             if key not in seen:
 145 |                 seen.add(key)
 147 |                 declarations.append(
 148 |                     Declaration(
 149 |                         kind=sym.kind,
 150 |                         name=sym.name,
 151 |                         start_line=sym.start_line + 1,
 152 |                         end_line=sym.end_line + 1,
 153 |                         modifiers=sym.modifiers,
 154 |                     )
 155 |                 )
 156 |         return declarations
 158 |     def _parse_block(self, lines: List[str], start_idx: int, end_idx: int) -> List[CodeSymbol]:
 160 |         Parse lines from start_idx to end_idx (exclusive),
 161 |         capturing functions/methods/classes/packages, plus nested definitions.
 162 |         Return a list of CodeSymbol objects (with 0-based line indices).
 163 |         Recursively parse the contents of each function/class block to find nested items.
 165 |         symbols: List[CodeSymbol] = []
 166 |         i = start_idx
 169 |         current_modifiers = set()
 170 |         in_roxygen = False
 172 |         while i < end_idx:
 173 |             line = lines[i]
 174 |             stripped = line.strip()
 177 |             if stripped.startswith("#'"):
 178 |                 if not in_roxygen:
 179 |                     current_modifiers.clear()
 180 |                 in_roxygen = True
 181 |                 if "@" in stripped:
 182 |                     after_at = stripped.split("@", 1)[1].strip()
 183 |                     first_token = after_at.split()[0] if after_at else ""
 184 |                     if first_token:
 185 |                         current_modifiers.add(first_token)
 186 |                 i += 1
 187 |                 continue
 188 |             else:
 189 |                 in_roxygen = False
 192 |             if not stripped or stripped.startswith("#"):
 193 |                 i += 1
 194 |                 continue
 197 |             mm = self.method_pattern.match(line)
 198 |             if mm:
 199 |                 method_name = None
 200 |                 if mm.group("dot_name"):
 201 |                     method_name = mm.group("dot_name")
 202 |                 elif mm.group("dollar_obj") and mm.group("dollar_method"):
 203 |                     method_name = f"{mm.group('dollar_obj')}${mm.group('dollar_method')}"
 204 |                 else:
 206 |                     method_name = mm.group("s4_name")
 208 |                 start_blk, end_blk = self._find_function_block(lines, i)
 210 |                 sym = CodeSymbol(
 211 |                     name=method_name,
 212 |                     kind="method",
 213 |                     start_line=start_blk,
 214 |                     end_line=end_blk,
 215 |                     modifiers=current_modifiers.copy(),
 216 |                 )
 217 |                 symbols.append(sym)
 220 |                 nested_lines = lines[start_blk+1 : end_blk+1]
 221 |                 if end_blk >= start_blk:
 222 |                     nested_syms = self._parse_block(nested_lines, 0, len(nested_lines))
 223 |                     symbols.extend(nested_syms)
 225 |                 current_modifiers.clear()
 226 |                 i = end_blk + 1
 227 |                 continue
 230 |             fm = self.function_pattern.match(line)
 231 |             if fm:
 232 |                 fname = fm.group("fname1") or fm.group("fname2")
 233 |                 start_blk, end_blk = self._find_function_block(lines, i)
 235 |                 sym = CodeSymbol(
 236 |                     name=fname,
 237 |                     kind="function",
 238 |                     start_line=start_blk,
 239 |                     end_line=end_blk,
 240 |                     modifiers=current_modifiers.copy(),
 241 |                 )
 242 |                 symbols.append(sym)
 245 |                 if self._function_defines_s3(lines, start_blk, end_blk, fname):
 246 |                     sym.kind = "class"
 249 |                 nested_lines = lines[start_blk+1 : end_blk+1]
 250 |                 if end_blk >= start_blk:
 251 |                     nested_syms = self._parse_block(nested_lines, 0, len(nested_lines))
 252 |                     symbols.extend(nested_syms)
 254 |                 current_modifiers.clear()
 255 |                 i = end_blk + 1
 256 |                 continue
 259 |             cm = self.class_pattern.match(line)
 260 |             if cm:
 261 |                 cname = cm.group("cname1") or cm.group("cname2") or cm.group("cname3") or ""
 262 |                 cls_start, cls_end = self._find_matching_parenthesis_block(lines, i)
 264 |                 csym = CodeSymbol(
 265 |                     name=cname,
 266 |                     kind="class",
 267 |                     start_line=i,
 268 |                     end_line=cls_end,
 269 |                     modifiers=current_modifiers.copy(),
 270 |                 )
 271 |                 symbols.append(csym)
 274 |                 lowered_line = line.lower()
 275 |                 if "r6class" in lowered_line:
 276 |                     methods = self._parse_r6_methods(lines, i, cls_end, class_name=cname)
 277 |                     symbols.extend(methods)
 278 |                 elif "setrefclass" in lowered_line:
 279 |                     methods = self._parse_refclass_methods(lines, i, cls_end, class_name=cname)
 280 |                     symbols.extend(methods)
 283 |                 nested_lines = lines[i+1 : cls_end+1]
 284 |                 nested_syms = self._parse_block(nested_lines, 0, len(nested_lines))
 285 |                 symbols.extend(nested_syms)
 287 |                 current_modifiers.clear()
 288 |                 i = cls_end + 1
 289 |                 continue
 292 |             pm = self.package_pattern.match(line)
 293 |             if pm:
 294 |                 pkg_name = pm.group("pkg1") or pm.group("pkg2")
 295 |                 psym = CodeSymbol(
 296 |                     name=pkg_name,
 297 |                     kind="package",
 298 |                     start_line=i,
 299 |                     end_line=i,
 300 |                     modifiers=current_modifiers.copy(),
 301 |                 )
 302 |                 symbols.append(psym)
 303 |                 current_modifiers.clear()
 304 |                 i += 1
 305 |                 continue
 308 |             current_modifiers.clear()
 309 |             i += 1
 311 |         return symbols
 313 |     def _merge_multiline_assignments(self, raw_lines: List[str], also_for_classes: bool=False) -> List[str]:
 315 |         Fix for cases like:
 316 |           complex_func <- # comment
 317 |              function(x) { ... }
 318 |         We'll merge such lines so the regex sees them on a single line.
 320 |         If also_for_classes=True, we also merge if the line ends with an assignment operator
 321 |         and the next line starts with R6Class(, setRefClass(, or setClass(.
 323 |         merged = []
 324 |         i = 0
 325 |         n = len(raw_lines)
 327 |         while i < n:
 328 |             line = raw_lines[i]
 329 |             strip_line = line.strip()
 331 |             if re.search(r"(?:<<?-|=|->|->>|:=)\s*(?:#.*)?$", strip_line):
 332 |                 j = i + 1
 333 |                 comment_lines = []
 335 |                 while j < n and (not raw_lines[j].strip() or raw_lines[j].strip().startswith("#")):
 336 |                     comment_lines.append(raw_lines[j])
 337 |                     j += 1
 338 |                 if j < n:
 339 |                     next_strip = raw_lines[j].lstrip()
 341 |                     if next_strip.startswith("function"):
 343 |                         base_line = re.sub(r"#.*$", "", line).rstrip()
 344 |                         new_line = base_line + " " + " ".join(l.strip() for l in comment_lines) + " " + raw_lines[j].lstrip()
 345 |                         merged.append(new_line)
 346 |                         i = j + 1
 347 |                         continue
 349 |                     if also_for_classes:
 350 |                         if any(x in next_strip for x in ["R6Class(", "setRefClass(", "setClass("]):
 352 |                             base_line = re.sub(r"#.*$", "", line).rstrip()
 353 |                             new_line = base_line + " " + " ".join(l.strip() for l in comment_lines) + " " + raw_lines[j].lstrip()
 354 |                             merged.append(new_line)
 355 |                             i = j + 1
 356 |                             continue
 357 |             merged.append(line)
 358 |             i += 1
 359 |         return merged
 361 |     def _find_function_block(self, lines: List[str], start_idx: int) -> (int, int):
 363 |         Return (start_line, end_line) for a function (or method) definition starting at start_idx.
 364 |         We'll count braces to find the end of the function body. If no brace on that line,
 365 |         treat it as a single-line function definition (like "func <- function(x) x").
 367 |         line = lines[start_idx]
 369 |         if '{' not in line:
 370 |             return start_idx, start_idx
 372 |         brace_count = line.count("{") - line.count("}")
 373 |         end_idx = start_idx
 374 |         j = start_idx
 375 |         while j < len(lines):
 376 |             if j > start_idx:
 377 |                 brace_count += lines[j].count("{") - lines[j].count("}")
 378 |             if brace_count <= 0 and j > start_idx:
 379 |                 end_idx = j
 380 |                 break
 381 |             j += 1
 382 |         if j == len(lines):
 383 |             end_idx = len(lines) - 1
 384 |         return start_idx, end_idx
 386 |     def _function_defines_s3(self, lines: List[str], start_idx: int, end_idx: int, fname: str) -> bool:
 388 |         Check if between start_idx and end_idx there's 'class(...) <- "fname"'
 389 |         or something that sets 'class(...)' to the same name, indicating an S3 constructor.
 391 |         pattern = re.compile(
 392 |             rf'class\s*\(\s*[^\)]*\)\s*(?:<<?-|=)\s*["\']{re.escape(fname)}["\']'
 393 |         )
 394 |         for idx in range(start_idx, min(end_idx+1, len(lines))):
 395 |             if pattern.search(lines[idx]):
 396 |                 return True
 397 |         return False
 399 |     def _find_matching_parenthesis_block(self, lines: List[str], start_idx: int) -> (int, int):
 401 |         For code like MyClass <- R6Class("MyClass", public=list(...)),
 402 |         we only track parentheses '(' and ')' -- not braces -- so we don't get confused by
 403 |         function bodies inside the class definition. Return (start_line, end_line).
 405 |         line = lines[start_idx]
 406 |         open_parens = line.count("(")
 407 |         close_parens = line.count(")")
 409 |         paren_diff = open_parens - close_parens
 412 |         if paren_diff <= 0:
 413 |             return start_idx, start_idx
 415 |         j = start_idx
 416 |         while j < len(lines) and paren_diff > 0:
 417 |             j += 1
 418 |             if j < len(lines):
 419 |                 open_parens = lines[j].count("(")
 420 |                 close_parens = lines[j].count(")")
 421 |                 paren_diff += open_parens - close_parens
 423 |         return (start_idx, min(j, len(lines) - 1))
 425 |     def _parse_r6_methods(self, lines: List[str], start_idx: int, end_idx: int, class_name: str) -> List[CodeSymbol]:
 427 |         Inside R6Class("class_name", public=list(...), private=list(...)), parse:
 428 |            methodName = function(...) { ... }
 429 |         We'll produce code symbols with name: "class_name.methodName".
 430 |         Ignore fields like 'value = 0'.
 432 |         methods = []
 433 |         block = lines[start_idx:end_idx+1]
 434 |         combined = "\n".join(block)
 437 |         method_pattern = re.compile(
 438 |             r'([a-zA-Z_]\w*)\s*=\s*function\s*\([^{]*\)\s*{',
 439 |             re.MULTILINE
 440 |         )
 443 |         for match in method_pattern.finditer(combined):
 444 |             method_name = match.group(1)
 445 |             if method_name not in ["fields", "methods"]:  # Exclude these special names
 446 |                 full_name = f"{class_name}.{method_name}"
 447 |                 start_line = start_idx + combined[:match.start()].count("\n")
 448 |                 end_line = start_idx + combined[:match.end()].count("\n")
 449 |                 methods.append(
 450 |                     CodeSymbol(
 451 |                         name=full_name,
 452 |                         kind="method",
 453 |                         start_line=start_line,
 454 |                         end_line=end_line,
 455 |                         modifiers=set(),
 456 |                     )
 457 |                 )
 458 |         return methods
 460 |     def _parse_refclass_methods(self, lines: List[str], start_idx: int, end_idx: int, class_name: str) -> List[CodeSymbol]:
 462 |         For setRefClass("Employee", fields=list(...), methods=list(...)), parse methodName = function(...).
 463 |         We'll produce "Employee.methodName".
 465 |         methods = []
 466 |         block = lines[start_idx:end_idx+1]
 467 |         combined = "\n".join(block)
 470 |         method_pattern = re.compile(
 471 |             r'([a-zA-Z_]\w*)\s*=\s*function\s*\([^{]*\)\s*{',
 472 |             re.MULTILINE
 473 |         )
 476 |         for match in method_pattern.finditer(combined):
 477 |             method_name = match.group(1)
 478 |             if method_name not in ["fields", "methods"]:  # Exclude these special names
 479 |                 full_name = f"{class_name}.{method_name}"
 480 |                 start_line = start_idx + combined[:match.start()].count("\n")
 481 |                 end_line = start_idx + combined[:match.end()].count("\n")
 482 |                 methods.append(
 483 |                     CodeSymbol(
 484 |                         name=full_name,
 485 |                         kind="method",
 486 |                         start_line=start_line,
 487 |                         end_line=end_line,
 488 |                         modifiers=set(),
 489 |                     )
 490 |                 )
 491 |         return methods
```

---
### File: ./codeconcat/parser/language_parsers/go_parser.py
#### Summary
```
File: go_parser.py
Language: python
```

```python
   3 | import re
   4 | from typing import List, Optional
   5 | from codeconcat.base_types import Declaration, ParsedFileData
   6 | from codeconcat.parser.language_parsers.base_parser import BaseParser, CodeSymbol
   8 | def parse_go(file_path: str, content: str) -> Optional[ParsedFileData]:
   9 |     parser = GoParser()
  10 |     declarations = parser.parse(content)
  11 |     return ParsedFileData(
  12 |         file_path=file_path,
  13 |         language="go",
  14 |         content=content,
  15 |         declarations=declarations
  16 |     )
  18 | class GoParser(BaseParser):
  19 |     def _setup_patterns(self):
  21 |         We separate out interface vs. struct vs. type in general, to avoid double counting.
  23 |         self.patterns = {
  24 |             "struct": re.compile(
  25 |                 r"^[^/]*type\s+(?P<name>[A-Z][a-zA-Z0-9_]*)\s+struct\s*\{"
  26 |             ),
  27 |             "interface": re.compile(
  28 |                 r"^[^/]*type\s+(?P<name>[A-Z][a-zA-Z0-9_]*)\s+interface\s*\{"
  29 |             ),
  30 |             "function": re.compile(
  31 |                 r"^[^/]*func\s+(?:\([^)]+\)\s+)?(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)"
  32 |                 r"(?:\s*\([^)]*\))?\s*\{"
  33 |             ),
  34 |             "const": re.compile(
  35 |                 r"^[^/]*const\s+(?:\(\s*|(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)\s*=)"
  36 |             ),
  37 |             "var": re.compile(
  38 |                 r"^[^/]*var\s+(?:\(\s*|(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)\s*(?:=|\s+[^=\s]+))"
  39 |             ),
  40 |         }
  42 |         self.block_start = "{"
  43 |         self.block_end = "}"
  44 |         self.line_comment = "//"
  45 |         self.block_comment_start = "/*"
  46 |         self.block_comment_end = "*/"
  48 |     def parse(self, content: str) -> List[Declaration]:
  49 |         lines = content.split("\n")
  50 |         symbols: List[CodeSymbol] = []
  51 |         in_const_block = False
  52 |         in_var_block = False
  53 |         i = 0
  54 |         while i < len(lines):
  55 |             line = lines[i]
  56 |             stripped = line.strip()
  57 |             if not stripped or stripped.startswith("//"):
  58 |                 i += 1
  59 |                 continue
  62 |             if in_const_block or in_var_block:
  63 |                 if ")" in stripped:
  65 |                     in_const_block = False
  66 |                     in_var_block = False
  67 |                     i += 1
  68 |                     continue
  71 |                 if "=" in stripped:
  73 |                     parts = stripped.split("=")
  74 |                     name_part = parts[0].strip()
  76 |                     name = name_part.split()[0]
  77 |                     kind = "const" if in_const_block else "var"
  78 |                     symbol = CodeSymbol(
  79 |                         name=name,
  80 |                         kind=kind,
  81 |                         start_line=i + 1,
  82 |                         end_line=i + 1,
  83 |                         modifiers=set(),
  84 |                     )
  85 |                     symbols.append(symbol)
  86 |                 i += 1
  87 |                 continue
  89 |             matched = False
  90 |             for kind, pattern in self.patterns.items():
  91 |                 m = pattern.match(stripped)
  92 |                 if m:
  93 |                     matched = True
  94 |                     if kind in ("const", "var"):
  96 |                         name = m.groupdict().get("name", None)
  97 |                         if name is None:
  99 |                             if kind == "const":
 100 |                                 in_const_block = True
 101 |                             else:
 102 |                                 in_var_block = True
 103 |                         else:
 105 |                             symbol = CodeSymbol(
 106 |                                 name=name,
 107 |                                 kind=kind,
 108 |                                 start_line=i + 1,
 109 |                                 end_line=i + 1,
 110 |                                 modifiers=set(),
 111 |                             )
 112 |                             symbols.append(symbol)
 113 |                     else:
 115 |                         name = m.group("name")
 116 |                         block_end = self._find_block_end(lines, i)
 117 |                         symbol = CodeSymbol(
 118 |                             name=name,
 119 |                             kind=kind,
 120 |                             start_line=i + 1,
 121 |                             end_line=block_end + 1,
 122 |                             modifiers=set(),
 123 |                         )
 124 |                         symbols.append(symbol)
 125 |                         i = block_end
 126 |                     break
 127 |             if not matched:
 129 |                 pass
 131 |             i += 1
 133 |         declarations = []
 134 |         for sym in symbols:
 135 |             declarations.append(Declaration(
 136 |                 kind=sym.kind,
 137 |                 name=sym.name,
 138 |                 start_line=sym.start_line,
 139 |                 end_line=sym.end_line,
 140 |                 modifiers=sym.modifiers
 141 |             ))
 142 |         return declarations
 144 |     def _find_block_end(self, lines: List[str], start: int) -> int:
 145 |         line = lines[start]
 146 |         if "{" not in line:
 147 |             return start
 148 |         brace_count = line.count("{") - line.count("}")
 149 |         if brace_count <= 0:
 150 |             return start
 151 |         for i in range(start + 1, len(lines)):
 152 |             l2 = lines[i]
 153 |             if l2.strip().startswith("//"):
 154 |                 continue
 155 |             brace_count += l2.count("{") - l2.count("}")
 156 |             if brace_count <= 0:
 157 |                 return i
 158 |         return len(lines) - 1
```

---
### File: ./codeconcat/writer/markdown_writer.py
#### Summary
```
File: markdown_writer.py
Language: python
```

```python
   1 | import random
   2 | from typing import Dict, List
   4 | import tiktoken
   5 | from halo import Halo
   7 | from codeconcat.base_types import (
   8 |     PROGRAMMING_QUOTES,
   9 |     AnnotatedFileData,
  10 |     CodeConCatConfig,
  11 |     ParsedDocData,
  12 |     ParsedFileData,
  13 | )
  14 | from codeconcat.processor.content_processor import (
  15 |     generate_directory_structure,
  16 |     generate_file_summary,
  17 |     process_file_content,
  18 | )
  19 | from codeconcat.writer.ai_context import generate_ai_preamble
  22 | def count_tokens(text: str) -> int:
  24 |     try:
  25 |         encoder = tiktoken.get_encoding("cl100k_base")
  26 |         return len(encoder.encode(text))
  27 |     except Exception as e:
  28 |         print(f"Warning: Tiktoken encoding failed ({str(e)}), falling back to word count")
  29 |         return len(text.split())
  32 | def print_quote_with_ascii(total_output_tokens: int = None):
  34 |     quote = random.choice(PROGRAMMING_QUOTES)
  35 |     quote_tokens = count_tokens(quote)
  38 |     width = max(len(line) for line in quote.split("\n")) + 4
  41 |     top_border = "+" + "=" * (width - 2) + "+"
  42 |     empty_line = "|" + " " * (width - 2) + "|"
  45 |     output_lines = ["\n[CodeConCat] Meow:", top_border, empty_line]
  48 |     words = quote.split()
  49 |     current_line = "|  "
  50 |     for word in words:
  51 |         if len(current_line) + len(word) + 1 > width - 2:
  52 |             output_lines.append(current_line + " " * (width - len(current_line) - 1) + "|")
  53 |             current_line = "|  " + word
  54 |         else:
  55 |             if current_line == "|  ":
  56 |                 current_line += word
  57 |             else:
  58 |                 current_line += " " + word
  59 |     output_lines.append(current_line + " " * (width - len(current_line) - 1) + "|")
  61 |     output_lines.extend([empty_line, top_border])
  64 |     print("\n".join(output_lines))
  65 |     print(f"\nQuote tokens (GPT-4): {quote_tokens:,}")
  66 |     if total_output_tokens:
  67 |         print(f"Total CodeConcat output tokens (GPT-4): {total_output_tokens:,}")
  70 | def write_markdown(
  71 |     annotated_files: List[AnnotatedFileData],
  72 |     docs: List[ParsedDocData],
  73 |     config: CodeConCatConfig,
  74 |     folder_tree_str: str = "",
  75 | ) -> str:
  76 |     spinner = Halo(text="Generating CodeConcat output", spinner="dots")
  77 |     spinner.start()
  79 |     output_chunks = []
  80 |     output_chunks.append("# CodeConCat Output\n\n")
  83 |     spinner.text = "Generating AI preamble"
  84 |     parsed_files = [
  85 |         ParsedFileData(
  86 |             file_path=ann.file_path, language=ann.language, content=ann.content, declarations=[]
  87 |         )
  88 |         for ann in annotated_files
  89 |     ]
  90 |     output_chunks.append(generate_ai_preamble(parsed_files, docs, {}))
  93 |     if config.include_directory_structure:
  94 |         spinner.text = "Generating directory structure"
  95 |         output_chunks.append("## Directory Structure\n")
  96 |         output_chunks.append("```\n")
  97 |         all_files = [f.file_path for f in annotated_files] + [d.file_path for d in docs]
  98 |         dir_structure = generate_directory_structure(all_files)
  99 |         output_chunks.append(dir_structure)
 100 |         output_chunks.append("\n```\n\n")
 101 |     elif folder_tree_str:  # Fallback to provided folder tree
 102 |         output_chunks.append("## Folder Tree\n")
 103 |         output_chunks.append("```\n")
 104 |         output_chunks.append(folder_tree_str)
 105 |         output_chunks.append("\n```\n\n")
 108 |     if annotated_files:
 109 |         spinner.text = "Processing code files"
 110 |         output_chunks.append("## Code Files\n\n")
 111 |         for i, ann in enumerate(annotated_files, 1):
 112 |             spinner.text = f"Processing code file {i}/{len(annotated_files)}: {ann.file_path}"
 113 |             output_chunks.append(f"### File: {ann.file_path}\n")
 114 |             if config.include_file_summary:
 115 |                 summary = generate_file_summary(
 116 |                     ParsedFileData(
 117 |                         file_path=ann.file_path,
 118 |                         language=ann.language,
 119 |                         content=ann.content,
 120 |                         declarations=[],
 121 |                     )
 122 |                 )
 123 |                 output_chunks.append(f"#### Summary\n```\n{summary}\n```\n\n")
 125 |             processed_content = process_file_content(ann.content, config)
 126 |             output_chunks.append(f"```{ann.language}\n{processed_content}\n```\n")
 127 |             output_chunks.append("\n---\n")
 130 |     if docs:
 131 |         spinner.text = "Processing documentation files"
 132 |         output_chunks.append("## Documentation\n\n")
 133 |         for i, doc in enumerate(docs, 1):
 134 |             spinner.text = f"Processing doc file {i}/{len(docs)}: {doc.file_path}"
 135 |             output_chunks.append(f"### File: {doc.file_path}\n")
 136 |             if config.include_file_summary:
 137 |                 summary = generate_file_summary(
 138 |                     ParsedFileData(
 139 |                         file_path=doc.file_path,
 140 |                         language=doc.doc_type,
 141 |                         content=doc.content,
 142 |                         declarations=[],
 143 |                     )
 144 |                 )
 145 |                 output_chunks.append(f"#### Summary\n```\n{summary}\n```\n\n")
 147 |             processed_content = process_file_content(doc.content, config)
 148 |             output_chunks.append(f"```{doc.doc_type}\n{processed_content}\n```\n")
 149 |             output_chunks.append("\n---\n")
 151 |     spinner.text = "Finalizing output"
 152 |     final_str = "".join(output_chunks)
 155 |     spinner.text = "Counting tokens"
 156 |     output_tokens = count_tokens(final_str)
 158 |     with open(config.output, "w", encoding="utf-8") as f:
 159 |         f.write(final_str)
 161 |         f.write("\n\n## Token Statistics\n")
 162 |         f.write(f"Total CodeConcat output tokens (GPT-4): {output_tokens:,}\n")
 164 |     spinner.succeed("CodeConcat output generated successfully")
 165 |     print(f"[CodeConCat] Markdown output written to: {config.output}")
 168 |     print_quote_with_ascii(output_tokens)
 170 |     return final_str
```

---
### File: ./codeconcat/writer/__init__.py
#### Summary
```
File: __init__.py
Language: python
```

```python

```

---
### File: ./codeconcat/writer/xml_writer.py
#### Summary
```
File: xml_writer.py
Language: python
```

```python
   3 | import xml.etree.ElementTree as ET
   4 | from typing import Dict, List, Optional
   5 | from xml.dom import minidom
   7 | from codeconcat.base_types import AnnotatedFileData, ParsedDocData, ParsedFileData
  10 | def write_xml(
  11 |     code_files: List[ParsedFileData],
  12 |     doc_files: List[ParsedDocData],
  13 |     file_annotations: Dict[str, AnnotatedFileData],
  14 |     folder_tree: Optional[str] = None,
  15 | ) -> str:
  18 |     root = ET.Element("codeconcat")
  21 |     metadata = ET.SubElement(root, "metadata")
  22 |     ET.SubElement(metadata, "total_files").text = str(len(code_files) + len(doc_files))
  23 |     ET.SubElement(metadata, "code_files").text = str(len(code_files))
  24 |     ET.SubElement(metadata, "doc_files").text = str(len(doc_files))
  27 |     if folder_tree:
  28 |         tree_elem = ET.SubElement(root, "folder_tree")
  29 |         tree_elem.text = folder_tree
  32 |     code_section = ET.SubElement(root, "code_files")
  33 |     for file in code_files:
  34 |         file_elem = ET.SubElement(code_section, "file")
  35 |         ET.SubElement(file_elem, "path").text = file.file_path
  36 |         ET.SubElement(file_elem, "language").text = file.language
  39 |         annotation = file_annotations.get(file.file_path)
  40 |         if annotation:
  41 |             annotations_elem = ET.SubElement(file_elem, "annotations")
  42 |             if annotation.summary:
  43 |                 ET.SubElement(annotations_elem, "summary").text = annotation.summary
  44 |             if annotation.tags:
  45 |                 tags_elem = ET.SubElement(annotations_elem, "tags")
  46 |                 for tag in annotation.tags:
  47 |                     ET.SubElement(tags_elem, "tag").text = tag
  50 |         content_elem = ET.SubElement(file_elem, "content")
  51 |         content_elem.text = f"<![CDATA[{file.content}]]>"
  54 |     if doc_files:
  55 |         docs_section = ET.SubElement(root, "doc_files")
  56 |         for doc in doc_files:
  57 |             doc_elem = ET.SubElement(docs_section, "file")
  58 |             ET.SubElement(doc_elem, "path").text = doc.file_path
  59 |             ET.SubElement(doc_elem, "format").text = doc.format
  60 |             content_elem = ET.SubElement(doc_elem, "content")
  61 |             content_elem.text = f"<![CDATA[{doc.content}]]>"
  64 |     xml_str = ET.tostring(root, encoding="unicode")
  65 |     pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="  ")
  67 |     return pretty_xml
```

---
### File: ./codeconcat/writer/ai_context.py
#### Summary
```
File: ai_context.py
Language: python
```

```python
   3 | from typing import Dict, List
   5 | from codeconcat.base_types import AnnotatedFileData, ParsedDocData, ParsedFileData
   8 | def generate_ai_preamble(
   9 |     code_files: List[ParsedFileData],
  10 |     doc_files: List[ParsedDocData],
  11 |     file_annotations: Dict[str, AnnotatedFileData],
  12 | ) -> str:
  16 |     file_types = {}
  17 |     for file in code_files:
  18 |         ext = file.file_path.split(".")[-1] if "." in file.file_path else "unknown"
  19 |         file_types[ext] = file_types.get(ext, 0) + 1
  22 |     lines = [
  23 |         "# AI-Friendly Code Summary",
  24 |         "",
  25 |         "This document contains a structured representation of a codebase, organized for AI analysis.",
  26 |         "",
  27 |         "## Repository Structure",
  28 |         "```",
  29 |         f"Total code files: {len(code_files)}",
  30 |         f"Documentation files: {len(doc_files)}",
  31 |         "",
  32 |         "File types:",
  33 |     ]
  35 |     for ext, count in sorted(file_types.items()):
  36 |         lines.append(f"- {ext}: {count} files")
  38 |     lines.extend(
  39 |         [
  40 |             "```",
  41 |             "",
  42 |             "## Code Organization",
  43 |             "The code is organized into sections, each prefixed with clear markers:",
  44 |             "- Directory markers show file organization",
  45 |             "- File headers contain metadata and imports",
  46 |             "- Annotations provide context about code purpose",
  47 |             "- Documentation sections contain project documentation",
  48 |             "",
  49 |             "## Navigation",
  50 |             "- Each file begins with '---FILE:' followed by its path",
  51 |             "- Each section is clearly delimited with markdown headers",
  52 |             "- Code blocks are formatted with appropriate language tags",
  53 |             "",
  54 |             "## Content Summary",
  55 |         ]
  56 |     )
  59 |     for file in code_files:
  60 |         annotation = file_annotations.get(file.file_path, AnnotatedFileData(file.file_path, "", []))
  61 |         if annotation.summary:
  62 |             lines.append(f"- `{file.file_path}`: {annotation.summary}")
  64 |     lines.extend(["", "---", "Begin code content below:", ""])
  66 |     return "\n".join(lines)
```

---
### File: ./codeconcat/writer/json_writer.py
#### Summary
```
File: json_writer.py
Language: python
```

```python
   1 | import json
   2 | from typing import List
   4 | from codeconcat.base_types import AnnotatedFileData, CodeConCatConfig, ParsedDocData
   7 | def write_json(
   8 |     annotated_files: List[AnnotatedFileData],
   9 |     docs: List[ParsedDocData],
  10 |     config: CodeConCatConfig,
  11 |     folder_tree_str: str = "",
  12 | ) -> str:
  13 |     data = {"files": []}  # Single list of all files with clear type indicators
  16 |     if folder_tree_str:
  17 |         data["folder_tree"] = folder_tree_str
  20 |     for ann in annotated_files:
  21 |         data["files"].append(
  22 |             {
  23 |                 "type": "code",
  24 |                 "file_path": ann.file_path,
  25 |                 "language": ann.language,
  26 |                 "content": ann.content,
  27 |                 "annotated_content": ann.annotated_content,
  28 |                 "summary": ann.summary,
  29 |                 "tags": ann.tags,
  30 |             }
  31 |         )
  34 |     for doc in docs:
  35 |         data["files"].append(
  36 |             {
  37 |                 "type": "documentation",
  38 |                 "file_path": doc.file_path,
  39 |                 "doc_type": doc.doc_type,
  40 |                 "content": doc.content,
  41 |             }
  42 |         )
  44 |     final_json = json.dumps(data, indent=2)
  46 |     with open(config.output, "w", encoding="utf-8") as f:
  47 |         f.write(final_json)
  49 |     print(f"[CodeConCat] JSON output written to: {config.output}")
  50 |     return final_json
```

---


## Token Statistics
Total CodeConcat output tokens (GPT-4): 68,881
