"""Integration tests for R S3/S4 class detection."""

import os

import pytest

from codeconcat.parser.language_parsers.tree_sitter_r_parser import TreeSitterRParser


@pytest.fixture
def r_parser():
    """Create an R parser instance."""
    return TreeSitterRParser()


@pytest.fixture
def s3_s4_sample_file():
    """Path to R S3/S4 sample file."""
    return os.path.join(
        os.path.dirname(__file__), "fixtures", "r_s3_s4_sample.R"
    )


class TestRS3S4Detection:
    """Test R S3/S4 OOP detection."""

    def test_s3_method_detection_with_arrow(self, r_parser, s3_s4_sample_file):
        """Test S3 method detection with <- operator."""
        with open(s3_s4_sample_file, "r", encoding="utf-8") as f:
            code = f.read()

        result = r_parser.parse(code, "test.R")
        declarations = result.declarations

        # Find S3 methods with <- operator
        s3_methods = [
            d for d in declarations
            if d.kind == "s3_method" and "s3" in d.modifiers
        ]

        # Should find print.myclass, [.myclass, +.myclass, data.frame.custom
        assert len(s3_methods) >= 3, f"Expected at least 3 S3 methods with <-, got {len(s3_methods)}"

        # Verify specific methods
        method_names = [d.name for d in s3_methods]
        assert "print.myclass" in method_names
        assert any("myclass" in name and "[" in name for name in method_names)  # [.myclass

    def test_s3_method_detection_with_equals(self, r_parser, s3_s4_sample_file):
        """Test S3 method detection with = operator."""
        with open(s3_s4_sample_file, "r", encoding="utf-8") as f:
            code = f.read()

        result = r_parser.parse(code, "test.R")
        declarations = result.declarations

        # Find summary.myclass method (uses =)
        s3_methods = [d for d in declarations if "summary.myclass" in d.name]
        assert len(s3_methods) >= 1, "Should detect S3 method with = operator"

    def test_s3_generic_detection_with_usemethod(self, r_parser, s3_s4_sample_file):
        """Test S3 generic detection via UseMethod() calls."""
        with open(s3_s4_sample_file, "r", encoding="utf-8") as f:
            code = f.read()

        result = r_parser.parse(code, "test.R")
        declarations = result.declarations

        # Find S3 generics
        s3_generics = [
            d for d in declarations
            if d.kind == "s3_generic" and "s3" in d.modifiers
        ]

        # Should find process and transform generics
        assert len(s3_generics) >= 2, f"Expected at least 2 S3 generics, got {len(s3_generics)}"

        generic_names = [d.name for d in s3_generics]
        # Names captured from UseMethod strings
        assert any("process" in str(name) for name in generic_names)

    def test_s4_class_detection(self, r_parser, s3_s4_sample_file):
        """Test S4 class detection."""
        with open(s3_s4_sample_file, "r", encoding="utf-8") as f:
            code = f.read()

        result = r_parser.parse(code, "test.R")
        declarations = result.declarations

        # Find S4 classes
        s4_classes = [
            d for d in declarations
            if d.kind == "s4_class" and "s4" in d.modifiers
        ]

        # Should find Person and Employee classes
        assert len(s4_classes) >= 2, f"Expected at least 2 S4 classes, got {len(s4_classes)}"

    def test_s4_method_detection(self, r_parser, s3_s4_sample_file):
        """Test S4 method detection."""
        with open(s3_s4_sample_file, "r", encoding="utf-8") as f:
            code = f.read()

        result = r_parser.parse(code, "test.R")
        declarations = result.declarations

        # Find S4 methods
        s4_methods = [
            d for d in declarations
            if d.kind == "s4_method" and "s4" in d.modifiers
        ]

        # Should find show and initialize methods
        assert len(s4_methods) >= 2, f"Expected at least 2 S4 methods, got {len(s4_methods)}"

    def test_s4_generic_detection(self, r_parser, s3_s4_sample_file):
        """Test S4 generic detection."""
        with open(s3_s4_sample_file, "r", encoding="utf-8") as f:
            code = f.read()

        result = r_parser.parse(code, "test.R")
        declarations = result.declarations

        # Find S4 generics
        s4_generics = [
            d for d in declarations
            if d.kind == "s4_generic" and "s4" in d.modifiers
        ]

        # Should find getInfo and updateSalary generics
        assert len(s4_generics) >= 2, f"Expected at least 2 S4 generics, got {len(s4_generics)}"

    def test_regular_functions_not_detected_as_s3(self, r_parser, s3_s4_sample_file):
        """Test that regular functions are not detected as S3/S4."""
        with open(s3_s4_sample_file, "r", encoding="utf-8") as f:
            code = f.read()

        result = r_parser.parse(code, "test.R")
        declarations = result.declarations

        # Find calculate_sum (regular function)
        regular_funcs = [d for d in declarations if d.name == "calculate_sum"]
        assert len(regular_funcs) == 1

        # Should be detected as regular function, not S3
        func = regular_funcs[0]
        assert func.kind == "function"
        assert "s3" not in func.modifiers
        assert "s4" not in func.modifiers

    def test_constants_not_detected_as_s3(self, r_parser, s3_s4_sample_file):
        """Test that constants are not detected as S3/S4."""
        with open(s3_s4_sample_file, "r", encoding="utf-8") as f:
            code = f.read()

        result = r_parser.parse(code, "test.R")
        declarations = result.declarations

        # Find MAX_ITERATIONS constant
        constants = [d for d in declarations if d.name == "MAX_ITERATIONS"]
        assert len(constants) == 1

        # Should be detected as constant, not S3/S4
        const = constants[0]
        assert const.kind == "constant"
        assert "const" in const.modifiers
        assert "s3" not in const.modifiers

    def test_operator_generics_detection(self, r_parser, s3_s4_sample_file):
        """Test detection of operator generics like +.myclass."""
        with open(s3_s4_sample_file, "r", encoding="utf-8") as f:
            code = f.read()

        result = r_parser.parse(code, "test.R")
        declarations = result.declarations

        # Find operator generics
        s3_methods = [d for d in declarations if d.kind == "s3_method"]

        # Should find +.myclass and [.myclass
        method_names = [d.name for d in s3_methods]
        has_operator = any("+" in name or "[" in name for name in method_names)
        assert has_operator, "Should detect operator generics like +.myclass and [.myclass"

    def test_namespaced_s4_detection(self, r_parser, s3_s4_sample_file):
        """Test detection of namespaced S4 calls (methods::setClass)."""
        with open(s3_s4_sample_file, "r", encoding="utf-8") as f:
            code = f.read()

        result = r_parser.parse(code, "test.R")
        declarations = result.declarations

        # Should detect both namespaced and non-namespaced S4 definitions
        s4_all = [
            d for d in declarations
            if "s4" in d.modifiers
        ]

        # At least 6 S4 declarations total (2 classes, 2 methods, 2 generics)
        assert len(s4_all) >= 6, f"Expected at least 6 S4 declarations, got {len(s4_all)}"
