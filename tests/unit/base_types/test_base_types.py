#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for the base types in CodeConCat.

Tests the data structures, interfaces, and models that form the foundation
of the codebase, including:
- Declaration
- ParseResult
- WritableItem implementations
- Security-related types
"""

import logging
import pytest
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from codeconcat.base_types import (
    CodeConCatConfig,
    Declaration,
    ParseResult,
    SecurityIssue,
    SecuritySeverity,
    TokenStats,
    AnnotatedFileData,
    ParsedDocData,
)

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class TestDeclaration:
    """Test class for the Declaration data structure."""

    def test_declaration_initialization(self):
        """Test basic initialization of a Declaration."""
        # Create a simple declaration
        decl = Declaration(
            kind="function",
            name="test_func",
            start_line=10,
            end_line=20,
        )
        
        # Check basic properties
        assert decl.kind == "function"
        assert decl.name == "test_func"
        assert decl.start_line == 10
        assert decl.end_line == 20
        assert decl.modifiers == set()  # Empty set by default
        assert decl.docstring == ""  # Empty string by default
        assert decl.children == []  # Empty list by default
        
    def test_declaration_with_modifiers(self):
        """Test Declaration with modifiers."""
        decl = Declaration(
            kind="method",
            name="test_method",
            start_line=15,
            end_line=25,
            modifiers={"public", "static"},
        )
        
        # Check modifiers
        assert len(decl.modifiers) == 2
        assert "public" in decl.modifiers
        assert "static" in decl.modifiers
        
    def test_declaration_with_docstring(self):
        """Test Declaration with a docstring."""
        docstring = "This is a test docstring."
        decl = Declaration(
            kind="class",
            name="TestClass",
            start_line=5,
            end_line=50,
            docstring=docstring,
        )
        
        # Check docstring
        assert decl.docstring == docstring
        
    def test_declaration_with_children(self):
        """Test Declaration with child declarations."""
        # Create parent class
        parent = Declaration(
            kind="class",
            name="ParentClass",
            start_line=1,
            end_line=30,
        )
        
        # Create child method
        child = Declaration(
            kind="method",
            name="child_method",
            start_line=5,
            end_line=10,
        )
        
        # Add child to parent
        parent.children.append(child)
        
        # Check parent-child relationship
        assert len(parent.children) == 1
        assert parent.children[0].name == "child_method"
        assert parent.children[0].kind == "method"
        
    def test_nested_declarations(self):
        """Test deeply nested declarations."""
        # Create class with nested class containing method
        top_class = Declaration(
            kind="class",
            name="TopClass",
            start_line=1,
            end_line=50,
        )
        
        nested_class = Declaration(
            kind="class",
            name="NestedClass",
            start_line=10,
            end_line=40,
        )
        
        nested_method = Declaration(
            kind="method",
            name="nested_method",
            start_line=15,
            end_line=20,
        )
        
        # Build the hierarchy
        nested_class.children.append(nested_method)
        top_class.children.append(nested_class)
        
        # Check the full hierarchy
        assert len(top_class.children) == 1
        assert top_class.children[0].name == "NestedClass"
        assert len(top_class.children[0].children) == 1
        assert top_class.children[0].children[0].name == "nested_method"


class TestParseResult:
    """Test class for the ParseResult data structure."""

    def test_parse_result_initialization(self):
        """Test basic initialization of ParseResult."""
        # Create a simple ParseResult
        result = ParseResult()
        
        # Check default values
        assert result.declarations == []
        assert result.imports == []
        assert result.ast_root is None
        assert result.error is None
        assert result.engine_used == "regex"
        
    def test_parse_result_with_declarations(self):
        """Test ParseResult with declarations."""
        # Create declarations
        decl1 = Declaration(kind="function", name="func1", start_line=1, end_line=5)
        decl2 = Declaration(kind="function", name="func2", start_line=7, end_line=10)
        
        # Create ParseResult with declarations
        result = ParseResult(declarations=[decl1, decl2])
        
        # Check declarations
        assert len(result.declarations) == 2
        assert result.declarations[0].name == "func1"
        assert result.declarations[1].name == "func2"
        
    def test_parse_result_with_imports(self):
        """Test ParseResult with imports."""
        # Create imports
        imports = ["os", "sys", "logging"]
        
        # Create ParseResult with imports
        result = ParseResult(imports=imports)
        
        # Check imports
        assert len(result.imports) == 3
        assert "os" in result.imports
        assert "sys" in result.imports
        assert "logging" in result.imports
        
    def test_parse_result_with_error(self):
        """Test ParseResult with error."""
        # Create ParseResult with error
        error_msg = "Failed to parse file: syntax error"
        result = ParseResult(error=error_msg)
        
        # Check error
        assert result.error == error_msg
        
    def test_parse_result_with_custom_engine(self):
        """Test ParseResult with custom engine."""
        # Create ParseResult with custom engine
        result = ParseResult(engine_used="tree_sitter")
        
        # Check engine
        assert result.engine_used == "tree_sitter"
        
        
class TestSecurityTypes:
    """Test class for security-related types."""

    def test_security_severity_enum(self):
        """Test SecuritySeverity enum values."""
        # Check enum values
        assert SecuritySeverity.CRITICAL.value == "CRITICAL"
        assert SecuritySeverity.HIGH.value == "HIGH"
        assert SecuritySeverity.MEDIUM.value == "MEDIUM"
        assert SecuritySeverity.LOW.value == "LOW"
        assert SecuritySeverity.INFO.value == "INFO"
        
    def test_security_severity_ordering(self):
        """Test that SecuritySeverity can be compared/ordered."""
        # Check ordering
        assert SecuritySeverity.CRITICAL > SecuritySeverity.HIGH
        assert SecuritySeverity.HIGH > SecuritySeverity.MEDIUM
        assert SecuritySeverity.MEDIUM > SecuritySeverity.LOW
        assert SecuritySeverity.LOW > SecuritySeverity.INFO
        
    def test_security_issue_initialization(self):
        """Test SecurityIssue initialization."""
        # Create a security issue
        issue = SecurityIssue(
            rule_id="SEC001",
            description="Hardcoded API key",
            file_path="config.py",
            line_number=42,
            severity=SecuritySeverity.HIGH,
        )
        
        # Check properties
        assert issue.rule_id == "SEC001"
        assert issue.description == "Hardcoded API key"
        assert issue.file_path == "config.py"
        assert issue.line_number == 42
        assert issue.severity == SecuritySeverity.HIGH
        assert issue.context == ""  # Default empty string
        
    def test_security_issue_with_context(self):
        """Test SecurityIssue with context."""
        # Create a security issue with context
        context = "API_KEY = 'abc123'"
        issue = SecurityIssue(
            rule_id="SEC001",
            description="Hardcoded API key",
            file_path="config.py",
            line_number=42,
            severity=SecuritySeverity.HIGH,
            context=context,
        )
        
        # Check context
        assert issue.context == context


class TestTokenStats:
    """Test class for the TokenStats data structure."""

    def test_token_stats_initialization(self):
        """Test TokenStats initialization."""
        # Create token stats
        stats = TokenStats(
            gpt3_tokens=1000,
            gpt4_tokens=1200,
            davinci_tokens=900,
            claude_tokens=1100,
        )
        
        # Check properties
        assert stats.gpt3_tokens == 1000
        assert stats.gpt4_tokens == 1200
        assert stats.davinci_tokens == 900
        assert stats.claude_tokens == 1100


class TestAnnotatedFileData:
    """Test class for the AnnotatedFileData class."""

    @pytest.fixture
    def config(self) -> CodeConCatConfig:
        """Fixture providing a CodeConCatConfig instance."""
        return CodeConCatConfig()

    @pytest.fixture
    def sample_file_data(self) -> AnnotatedFileData:
        """Fixture providing a sample AnnotatedFileData instance."""
        return AnnotatedFileData(
            file_path="test.py",
            language="python",
            content="def test(): pass",
            annotated_content="def test(): pass  # Annotated",
            summary="Test file",
            declarations=[
                Declaration(kind="function", name="test", start_line=1, end_line=1)
            ],
            imports=["os"],
            token_stats=TokenStats(gpt3_tokens=10, gpt4_tokens=12, davinci_tokens=9, claude_tokens=11),
            security_issues=[
                SecurityIssue(
                    rule_id="SEC001", 
                    description="Test issue", 
                    file_path="test.py", 
                    line_number=1, 
                    severity=SecuritySeverity.LOW
                )
            ],
            tags=["test"],
        )

    def test_annotated_file_data_initialization(self, sample_file_data):
        """Test AnnotatedFileData initialization."""
        # Check core properties
        assert sample_file_data.file_path == "test.py"
        assert sample_file_data.language == "python"
        assert sample_file_data.content == "def test(): pass"
        assert sample_file_data.annotated_content == "def test(): pass  # Annotated"
        assert sample_file_data.summary == "Test file"
        
        # Check lists and complex objects
        assert len(sample_file_data.declarations) == 1
        assert sample_file_data.declarations[0].name == "test"
        assert len(sample_file_data.imports) == 1
        assert sample_file_data.imports[0] == "os"
        assert sample_file_data.token_stats.gpt4_tokens == 12
        assert len(sample_file_data.security_issues) == 1
        assert sample_file_data.security_issues[0].rule_id == "SEC001"
        assert len(sample_file_data.tags) == 1
        assert sample_file_data.tags[0] == "test"
        
    def test_writable_item_interface_text(self, sample_file_data, config):
        """Test that AnnotatedFileData implements WritableItem interface for text."""
        # Get text lines
        text_lines = sample_file_data.render_text_lines(config)
        
        # Basic validation that something sensible is returned
        assert isinstance(text_lines, list)
        assert len(text_lines) > 0
        
    def test_writable_item_interface_markdown(self, sample_file_data, config):
        """Test that AnnotatedFileData implements WritableItem interface for markdown."""
        # Get markdown chunks
        md_chunks = sample_file_data.render_markdown_chunks(config)
        
        # Basic validation
        assert isinstance(md_chunks, list)
        assert len(md_chunks) > 0
        
    def test_writable_item_interface_json(self, sample_file_data, config):
        """Test that AnnotatedFileData implements WritableItem interface for JSON."""
        # Get JSON dict
        json_dict = sample_file_data.render_json_dict(config)
        
        # Basic validation
        assert isinstance(json_dict, dict)
        assert "file_path" in json_dict
        assert json_dict["file_path"] == "test.py"
        
    def test_writable_item_interface_xml(self, sample_file_data, config):
        """Test that AnnotatedFileData implements WritableItem interface for XML."""
        # Get XML element
        xml_elem = sample_file_data.render_xml_element(config)
        
        # Basic validation
        assert xml_elem.tag == "file"
        assert xml_elem.get("path") == "test.py"


class TestParsedDocData:
    """Test class for the ParsedDocData class."""

    @pytest.fixture
    def config(self) -> CodeConCatConfig:
        """Fixture providing a CodeConCatConfig instance."""
        return CodeConCatConfig()

    @pytest.fixture
    def sample_doc_data(self) -> ParsedDocData:
        """Fixture providing a sample ParsedDocData instance."""
        return ParsedDocData(
            file_path="docs/README.md",
            content="# Test Docs",
            doc_type="markdown",
            summary="Documentation file",
            tags=["docs"],
        )

    def test_parsed_doc_data_initialization(self, sample_doc_data):
        """Test ParsedDocData initialization."""
        # Check properties
        assert sample_doc_data.file_path == "docs/README.md"
        assert sample_doc_data.content == "# Test Docs"
        assert sample_doc_data.doc_type == "markdown"
        assert sample_doc_data.summary == "Documentation file"
        assert len(sample_doc_data.tags) == 1
        assert sample_doc_data.tags[0] == "docs"
        
    def test_writable_item_interface_text(self, sample_doc_data, config):
        """Test that ParsedDocData implements WritableItem interface for text."""
        # Get text lines
        text_lines = sample_doc_data.render_text_lines(config)
        
        # Basic validation
        assert isinstance(text_lines, list)
        assert len(text_lines) > 0
        
    def test_writable_item_interface_markdown(self, sample_doc_data, config):
        """Test that ParsedDocData implements WritableItem interface for markdown."""
        # Get markdown chunks
        md_chunks = sample_doc_data.render_markdown_chunks(config)
        
        # Basic validation
        assert isinstance(md_chunks, list)
        assert len(md_chunks) > 0
        
    def test_writable_item_interface_json(self, sample_doc_data, config):
        """Test that ParsedDocData implements WritableItem interface for JSON."""
        # Get JSON dict
        json_dict = sample_doc_data.render_json_dict(config)
        
        # Basic validation
        assert isinstance(json_dict, dict)
        assert "file_path" in json_dict
        assert json_dict["file_path"] == "docs/README.md"
        
    def test_writable_item_interface_xml(self, sample_doc_data, config):
        """Test that ParsedDocData implements WritableItem interface for XML."""
        # Get XML element
        xml_elem = sample_doc_data.render_xml_element(config)
        
        # Basic validation
        assert xml_elem.tag == "doc"
        assert xml_elem.get("path") == "docs/README.md"


if __name__ == "__main__":
    pytest.main(["-v", __file__])
