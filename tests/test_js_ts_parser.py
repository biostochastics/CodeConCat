import pytest

from codeconcat.parser.language_parsers.js_ts_parser import parse_javascript_or_typescript


def test_basic_class():
    content = """\
/**
 * This is a class doc
 */
export class MyClass extends BaseClass {
  // some content
}
"""
    parsed = parse_javascript_or_typescript("MyClass.ts", content, language="typescript")
    assert len(parsed.declarations) == 1

    decl = parsed.declarations[0]
    assert decl.kind == "class"
    assert decl.name == "MyClass"
    assert "export" in decl.modifiers
    assert decl.docstring is not None
    assert "This is a class doc" in decl.docstring


def test_function():
    content = """\
// Normal function
export function myFunction(a, b) {
  return a + b;
}
"""
    parsed = parse_javascript_or_typescript("func.js", content, language="javascript")
    assert len(parsed.declarations) == 1

    decl = parsed.declarations[0]
    assert decl.kind == "function"
    assert decl.name == "myFunction"
    assert "export" in decl.modifiers
    assert decl.start_line == 2
    assert decl.end_line == 4


def test_arrow_function():
    content = """\
/** Arrow doc */
export const add = (x, y) => {
  return x + y;
};
"""
    parsed = parse_javascript_or_typescript("arrow.js", content, language="javascript")
    assert len(parsed.declarations) == 1

    decl = parsed.declarations[0]
    assert decl.kind == "arrow_function"
    assert decl.name == "add"
    assert "export" in decl.modifiers
    assert "Arrow doc" in decl.docstring


def test_method_in_class():
    content = """\
class MyClass {
  /** doc for method */
  myMethod(arg) {
    return arg * 2;
  }
}
"""
    parsed = parse_javascript_or_typescript("MyClass.js", content, language="javascript")
    # We expect 1 class symbol, plus 1 method symbol
    # The parser will likely produce 2 "declarations":
    # - The class at lines 1..6
    # - The method at lines 2..5 (depending on how braces are tracked)
    #
    # Implementation detail: The parser treats top-level items as separate declarations,
    # nested symbols might or might not appear as separate depending on your needs.
    # If you want the method as a separate top-level Declaration, you can tweak the code
    # to store nested symbols. Currently, the code appends them to the list once braces
    # close. As an example, let's check for the method as a top-level symbol.

    # Because the parser as provided doesn't fully nest child declarations in "children",
    # it is possible it returns them as separate declarations. We'll check for 2 total.
    assert len(parsed.declarations) == 2

    class_decl = parsed.declarations[0]
    method_decl = parsed.declarations[1]

    # Class checks
    assert class_decl.kind == "class"
    assert class_decl.name == "MyClass"

    # Method checks
    assert method_decl.kind == "method"
    assert method_decl.name == "myMethod"
    assert "doc for method" in method_decl.docstring


def test_interface_typescript():
    content = """\
/** Interface doc */
export interface Foo<T> extends Bar, Baz<T> {
  someProp: string;
}
"""
    parsed = parse_javascript_or_typescript("types.ts", content, language="typescript")
    assert len(parsed.declarations) == 1

    decl = parsed.declarations[0]
    assert decl.kind == "interface"
    assert decl.name == "Foo"
    assert "export" in decl.modifiers
    assert "Interface doc" in decl.docstring


def test_type_alias():
    content = """\
/** Type doc */
export type MyAlias = string | number;
"""
    parsed = parse_javascript_or_typescript("alias.ts", content, language="typescript")
    assert len(parsed.declarations) == 1

    decl = parsed.declarations[0]
    assert decl.kind == "type"
    assert decl.name == "MyAlias"
    assert "export" in decl.modifiers
    assert "Type doc" in decl.docstring


def test_enum():
    content = """\
@CoolDecorator
export enum MyEnum {
  A,
  B,
  C
}
"""
    # We rely on TypeScript mode to parse decorators & enum
    parsed = parse_javascript_or_typescript("enum.ts", content, language="typescript")
    assert len(parsed.declarations) == 1

    decl = parsed.declarations[0]
    assert decl.kind == "enum"
    assert decl.name == "MyEnum"
    # Decorator is included in modifiers
    assert "@CoolDecorator" in decl.modifiers
    assert "export" in decl.modifiers


def test_deeply_nested():
    content = """\
export function outer() {
  function inner() {
    class InnerClass {
      method() {
        return "hello";
      }
    }
    return new InnerClass();
  }
  return inner();
}
"""
    # In the current parser, all discovered items are appended once their braces close.
    # So we might end up with 3 declarations: outer() function, inner() function, and InnerClass
    parsed = parse_javascript_or_typescript("nested.js", content, language="javascript")

    # We expect something like:
    # 1. outer (lines 1..10)
    # 2. inner (lines 2..9)
    # 3. InnerClass (lines 3..7)
    # 4. method (lines 4..6) as a separate "method" symbol if the parser captures it at top level

    # The parser’s logic sets end_line when each block closes.
    # We'll check we have at least the top-level function and the nested function.
    # Because the code also recognizes class and method, we might end up with 4 declarations.
    assert len(parsed.declarations) >= 3

    # Outer function
    outer_func = parsed.declarations[0]
    assert outer_func.kind == "function"
    assert outer_func.name == "outer"

    # Inner function
    inner_func = parsed.declarations[1]
    assert inner_func.kind == "function"
    assert inner_func.name == "inner"

    # Inner class
    inner_class = parsed.declarations[2]
    assert inner_class.kind == "class"
    assert inner_class.name == "InnerClass"


def test_multiline_doc_comment():
    content = """\
/**
 * This is a multiline doc comment
 * spanning multiple lines
 */
export function multilineDoc() {
  return true;
}
"""
    parsed = parse_javascript_or_typescript("multiline.js", content, language="javascript")
    assert len(parsed.declarations) == 1

    decl = parsed.declarations[0]
    assert decl.kind == "function"
    assert decl.name == "multilineDoc"
    assert "multiline doc comment" in decl.docstring
    assert "spanning multiple lines" in decl.docstring


def test_no_symbols():
    # Parser should handle empty or symbol-less code gracefully
    content = """\
// Just a file with comments
// and no actual exported/declared symbols
"""
    parsed = parse_javascript_or_typescript("empty.js", content, language="javascript")
    assert len(parsed.declarations) == 0
