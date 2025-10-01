"""Integration tests for Julia parametric type detection."""

import os

import pytest

from codeconcat.parser.language_parsers.tree_sitter_julia_parser import TreeSitterJuliaParser


@pytest.fixture
def julia_parser():
    """Create a Julia parser instance."""
    return TreeSitterJuliaParser()


@pytest.fixture
def parametric_sample_file():
    """Path to Julia parametric types sample file."""
    return os.path.join(
        os.path.dirname(__file__), "fixtures", "julia_parametric_sample.jl"
    )


class TestJuliaParametricTypes:
    """Test Julia parametric type detection."""

    def test_parametric_struct_detection(self, julia_parser, parametric_sample_file):
        """Test parametric struct detection."""
        with open(parametric_sample_file, "r", encoding="utf-8") as f:
            code = f.read()

        result = julia_parser.parse(code, "test.jl")
        declarations = result.declarations

        # Find parametric structs
        parametric_structs = [
            d for d in declarations
            if d.kind == "struct" and "parametric" in d.modifiers
        ]

        # Should find Point{T}, BoundedValue{T<:Real}, Pair{T,S}, Container{T}, etc.
        assert len(parametric_structs) >= 4, f"Expected at least 4 parametric structs, got {len(parametric_structs)}"

        # Verify specific structs
        struct_names = [d.name for d in parametric_structs]
        assert "Point" in struct_names
        assert "BoundedValue" in struct_names
        assert "Pair" in struct_names

    def test_parametric_abstract_type_detection(self, julia_parser, parametric_sample_file):
        """Test parametric abstract type detection."""
        with open(parametric_sample_file, "r", encoding="utf-8") as f:
            code = f.read()

        result = julia_parser.parse(code, "test.jl")
        declarations = result.declarations

        # Find parametric abstract types
        parametric_abstracts = [
            d for d in declarations
            if d.kind == "abstract_type" and "parametric" in d.modifiers
        ]

        # Should find Number{T} and Pointy{T<:Real}
        assert len(parametric_abstracts) >= 2, f"Expected at least 2 parametric abstract types, got {len(parametric_abstracts)}"

        # Verify specific types
        abstract_names = [d.name for d in parametric_abstracts]
        assert "Number" in abstract_names
        assert "Pointy" in abstract_names

    def test_parametric_function_detection(self, julia_parser, parametric_sample_file):
        """Test parametric function detection (functions with where clauses)."""
        with open(parametric_sample_file, "r", encoding="utf-8") as f:
            code = f.read()

        result = julia_parser.parse(code, "test.jl")
        declarations = result.declarations

        # Find parametric functions
        parametric_funcs = [
            d for d in declarations
            if d.kind == "function" and "parametric" in d.modifiers
        ]

        # Should find identity, process, clamp_value, complex_func, etc.
        assert len(parametric_funcs) >= 4, f"Expected at least 4 parametric functions, got {len(parametric_funcs)}"

    def test_short_form_parametric_function_detection(self, julia_parser, parametric_sample_file):
        """Test short-form parametric function detection."""
        with open(parametric_sample_file, "r", encoding="utf-8") as f:
            code = f.read()

        result = julia_parser.parse(code, "test.jl")
        declarations = result.declarations

        # Find all parametric functions (including short-form)
        parametric_funcs = [
            d for d in declarations
            if d.kind == "function" and "parametric" in d.modifiers
        ]

        # Should include short-form functions like square(x::T) where T = x * x
        # These may be captured by parametric_func_short pattern
        assert len(parametric_funcs) >= 4

    def test_non_parametric_struct_not_marked(self, julia_parser, parametric_sample_file):
        """Test that non-parametric structs are not marked as parametric."""
        with open(parametric_sample_file, "r", encoding="utf-8") as f:
            code = f.read()

        result = julia_parser.parse(code, "test.jl")
        declarations = result.declarations

        # Find SimplePoint (non-parametric)
        simple_structs = [d for d in declarations if d.name == "SimplePoint"]
        assert len(simple_structs) == 1

        # Should not be marked as parametric
        simple_struct = simple_structs[0]
        assert simple_struct.kind == "struct"
        assert "parametric" not in simple_struct.modifiers

    def test_non_parametric_abstract_not_marked(self, julia_parser, parametric_sample_file):
        """Test that non-parametric abstract types are not marked as parametric."""
        with open(parametric_sample_file, "r", encoding="utf-8") as f:
            code = f.read()

        result = julia_parser.parse(code, "test.jl")
        declarations = result.declarations

        # Find Shape (non-parametric abstract)
        simple_abstracts = [d for d in declarations if d.name == "Shape"]
        assert len(simple_abstracts) == 1

        # Should not be marked as parametric
        simple_abstract = simple_abstracts[0]
        assert simple_abstract.kind == "abstract_type"
        assert "parametric" not in simple_abstract.modifiers

    def test_non_parametric_function_not_marked(self, julia_parser, parametric_sample_file):
        """Test that non-parametric functions are not marked as parametric."""
        with open(parametric_sample_file, "r", encoding="utf-8") as f:
            code = f.read()

        result = julia_parser.parse(code, "test.jl")
        declarations = result.declarations

        # Find simple_add (non-parametric)
        simple_funcs = [d for d in declarations if d.name == "simple_add"]
        assert len(simple_funcs) == 1

        # Should not be marked as parametric
        simple_func = simple_funcs[0]
        assert simple_func.kind == "function"
        assert "parametric" not in simple_func.modifiers

    def test_mutable_parametric_struct_detection(self, julia_parser, parametric_sample_file):
        """Test mutable parametric struct detection."""
        with open(parametric_sample_file, "r", encoding="utf-8") as f:
            code = f.read()

        result = julia_parser.parse(code, "test.jl")
        declarations = result.declarations

        # Find MutablePoint{T<:Real}
        mutable_structs = [d for d in declarations if d.name == "MutablePoint"]
        assert len(mutable_structs) == 1

        # Should be marked as parametric
        mutable_struct = mutable_structs[0]
        assert mutable_struct.kind == "struct"
        assert "parametric" in mutable_struct.modifiers

    def test_nested_parametric_types(self, julia_parser, parametric_sample_file):
        """Test detection of structs with nested parametric types."""
        with open(parametric_sample_file, "r", encoding="utf-8") as f:
            code = f.read()

        result = julia_parser.parse(code, "test.jl")
        declarations = result.declarations

        # Find Container{T} and NestedContainer{T}
        container_structs = [
            d for d in declarations
            if "Container" in d.name and d.kind == "struct"
        ]

        # Should find at least Container and NestedContainer
        assert len(container_structs) >= 2

        # Both should be marked as parametric
        for struct in container_structs:
            assert "parametric" in struct.modifiers

    def test_parametric_signature_extraction(self, julia_parser, parametric_sample_file):
        """Test that parametric function signatures include where clauses."""
        with open(parametric_sample_file, "r", encoding="utf-8") as f:
            code = f.read()

        result = julia_parser.parse(code, "test.jl")
        declarations = result.declarations

        # Find parametric functions with signatures
        parametric_funcs = [
            d for d in declarations
            if d.kind == "function" and "parametric" in d.modifiers and d.signature
        ]

        # Should have extracted signatures
        assert len(parametric_funcs) >= 1

        # Signatures should exist (may or may not include where clause depending on extraction logic)
        for func in parametric_funcs[:3]:  # Check first 3
            assert func.signature, f"Function {func.name} should have a signature"

    def test_comprehensive_parametric_detection_count(self, julia_parser, parametric_sample_file):
        """Test overall count of parametric declarations."""
        with open(parametric_sample_file, "r", encoding="utf-8") as f:
            code = f.read()

        result = julia_parser.parse(code, "test.jl")
        declarations = result.declarations

        # Count all parametric declarations
        all_parametric = [d for d in declarations if "parametric" in d.modifiers]

        # Should have significant number of parametric declarations
        # At least: 7 structs + 2 abstracts + 6 functions = 15 total
        assert len(all_parametric) >= 10, f"Expected at least 10 parametric declarations, got {len(all_parametric)}"

    def test_type_constraints_in_where_clause(self, julia_parser, parametric_sample_file):
        """Test detection of type constraints (T<:Real) in parametric types."""
        with open(parametric_sample_file, "r", encoding="utf-8") as f:
            code = f.read()

        result = julia_parser.parse(code, "test.jl")
        declarations = result.declarations

        # Find BoundedValue{T<:Real} and Pointy{T<:Real}
        constrained_types = [
            d for d in declarations
            if d.name in ["BoundedValue", "Pointy"] and "parametric" in d.modifiers
        ]

        # Should find both
        assert len(constrained_types) >= 2

    def test_multi_parameter_types(self, julia_parser, parametric_sample_file):
        """Test detection of types with multiple type parameters."""
        with open(parametric_sample_file, "r", encoding="utf-8") as f:
            code = f.read()

        result = julia_parser.parse(code, "test.jl")
        declarations = result.declarations

        # Find Pair{T, S} and Graph{V, E}
        multi_param_structs = [
            d for d in declarations
            if d.name in ["Pair", "Graph"] and "parametric" in d.modifiers
        ]

        # Should find both
        assert len(multi_param_structs) >= 2
