#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for the rendering adapters in CodeConCat.

Tests the decoupled rendering logic for different output formats:
- Markdown rendering
- JSON rendering
- XML rendering
- Text rendering
"""

import logging
import xml.etree.ElementTree as ET

import pytest

from codeconcat.base_types import (
    AnnotatedFileData,
    CodeConCatConfig,
    Declaration,
    ParsedDocData,
    SecurityIssue,
    SecuritySeverity,
    TokenStats,
)
from codeconcat.writer.rendering_adapters import (
    MarkdownRenderAdapter,
    JsonRenderAdapter,
    XmlRenderAdapter,
    TextRenderAdapter,
)

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class TestRenderingAdapters:
    """Test class for rendering adapters."""

    @pytest.fixture
    def config(self) -> CodeConCatConfig:
        """Fixture providing a CodeConCatConfig instance."""
        return CodeConCatConfig(
            output_dir="out",
            include_file_summary=True,
            include_declarations_in_summary=True,
            include_imports_in_summary=True,
            include_security_in_summary=True,
            include_tokens_in_summary=True,
            enable_token_counting=True,
        )

    @pytest.fixture
    def sample_declaration(self) -> Declaration:
        """Fixture providing a sample declaration with children."""
        # Create a parent class declaration
        parent = Declaration(
            kind="class",
            name="TestClass",
            start_line=5,
            end_line=30,
            modifiers={"public"},
            docstring="This is a test class docstring.",
        )

        # Add a method as a child
        method = Declaration(
            kind="method",
            name="test_method",
            start_line=10,
            end_line=20,
            modifiers={"public", "static"},
            docstring="This is a test method docstring.",
        )
        parent.children.append(method)

        # Add a nested class
        nested_class = Declaration(
            kind="class",
            name="NestedClass",
            start_line=21,
            end_line=29,
            modifiers={"private"},
            docstring="This is a nested class.",
        )
        parent.children.append(nested_class)

        return parent

    @pytest.fixture
    def sample_security_issue(self) -> SecurityIssue:
        """Fixture providing a sample security issue."""
        return SecurityIssue(
            rule_id="SEC001",
            description="Hardcoded credentials",
            file_path="test.py",
            line_number=42,
            severity=SecuritySeverity.HIGH,
            context="password = 'hardcoded_password'",
        )

    @pytest.fixture
    def sample_token_stats(self) -> TokenStats:
        """Fixture providing sample token statistics."""
        return TokenStats(gpt4_tokens=1200, claude_tokens=1100)

    @pytest.fixture
    def sample_file_data(
        self, sample_declaration, sample_security_issue, sample_token_stats
    ) -> AnnotatedFileData:
        """Fixture providing sample annotated file data."""
        return AnnotatedFileData(
            file_path="test/path/to/file.py",
            language="python",
            content="def hello():\n    print('Hello, world!')\n",
            annotated_content="def hello():\n    print('Hello, world!')\n",
            summary="A simple Python file with a hello function.",
            declarations=[sample_declaration],
            imports=["os", "sys", "logging"],
            token_stats=sample_token_stats,
            security_issues=[sample_security_issue],
            tags=["example", "test"],
        )

    @pytest.fixture
    def sample_doc_data(self) -> ParsedDocData:
        """Fixture providing sample documentation data."""
        return ParsedDocData(
            file_path="docs/README.md",
            content="# Test Documentation\n\nThis is test documentation content.",
            doc_type="markdown",
            summary="Documentation about the project.",
            tags=["docs", "readme"],
        )

    def test_markdown_render_declarations(self, sample_declaration, config):
        """Test rendering declarations to Markdown."""
        result = MarkdownRenderAdapter.render_declarations([sample_declaration], "test.py", config)

        # Check expected output
        assert "### Declarations" in result
        assert "**Class**: `TestClass`" in result
        assert "(lines 5-30)" in result
        assert "[public]" in result

        # Check that child declarations are included
        assert "**Method**: `test_method`" in result
        assert "(lines 10-20)" in result
        # Check both modifiers are present, without assuming order
        assert "public" in result
        assert "static" in result

        # Check that nested class is included
        assert "**Class**: `NestedClass`" in result
        assert "(lines 21-29)" in result
        assert "[private]" in result

    def test_markdown_render_imports(self, config):
        """Test rendering imports to Markdown."""
        imports = ["os", "sys", "logging"]
        result = MarkdownRenderAdapter.render_imports(imports)

        # Check expected output
        assert "### Imports" in result
        assert "- `os`" in result
        assert "- `sys`" in result
        assert "- `logging`" in result

    def test_markdown_render_security_issues(self, sample_security_issue):
        """Test rendering security issues to Markdown."""
        result = MarkdownRenderAdapter.render_security_issues([sample_security_issue])

        # Check expected output
        assert "### Security Issues" in result
        assert "| Severity | Rule | Line | Description |" in result
        assert "| 🟠 HIGH | SEC001 | 42 | Hardcoded credentials |" in result

    def test_markdown_render_token_stats(self, sample_token_stats):
        """Test rendering token statistics to Markdown."""
        result = MarkdownRenderAdapter.render_token_stats(sample_token_stats)

        # Check expected output
        assert "### Token Statistics" in result
        assert "| Model | Token Count |" in result
        assert "| GPT-4 | 1,200 |" in result
        assert "| Claude | 1,100 |" in result

    def test_markdown_render_file_content(self, config):
        """Test rendering file content to Markdown."""
        content = "def test():\n    return True"
        result = MarkdownRenderAdapter.render_file_content(content, "python", config)

        # Check expected output
        assert "```python" in result
        assert "def test():" in result
        assert "    return True" in result
        assert "```" in result

        # Test with line numbers
        config.show_line_numbers = True
        result = MarkdownRenderAdapter.render_file_content(content, "python", config)
        assert "   1 |" in result  # 4 digit padding format
        assert "def test():" in result
        assert "   2 |" in result  # 4 digit padding format
        assert "    return True" in result

    def test_markdown_render_annotated_file(self, sample_file_data, config):
        """Test rendering a complete annotated file to Markdown."""
        result = MarkdownRenderAdapter.render_annotated_file(sample_file_data, config)

        # Check expected sections
        assert "## File: test/path/to/file.py" in result[0]
        assert "### Summary" in result[1]
        assert "**Tags**: `example`, `test`" in result[2]

        # Concatenate for easier assertions
        content = "\n".join(result)
        assert "### Declarations" in content
        assert "### Imports" in content
        assert "### Security Issues" in content
        assert "### Token Statistics" in content
        assert "```python" in content

    def test_markdown_render_doc_file(self, sample_doc_data, config):
        """Test rendering a documentation file to Markdown."""
        result = MarkdownRenderAdapter.render_doc_file(sample_doc_data, config)

        # Check expected sections
        assert "## Documentation: docs/README.md" in result[0]
        assert "### Summary" in result[1]
        assert "**Tags**: `docs`, `readme`" in result[2]

        # Check content
        assert "# Test Documentation" in result[3]
        assert "This is test documentation content." in result[3]

    def test_json_render_declaration_to_dict(self, sample_declaration):
        """Test converting a Declaration to a dictionary."""
        result = JsonRenderAdapter.declaration_to_dict(sample_declaration)

        # Check expected structure
        assert result["kind"] == "class"
        assert result["name"] == "TestClass"
        assert result["start_line"] == 5
        assert result["end_line"] == 30
        assert "public" in result["modifiers"]
        assert result["docstring"] == "This is a test class docstring."

        # Check children
        assert len(result["children"]) == 2

        # Check first child (method)
        method = result["children"][0]
        assert method["kind"] == "method"
        assert method["name"] == "test_method"
        assert "static" in method["modifiers"]

        # Check second child (nested class)
        nested = result["children"][1]
        assert nested["kind"] == "class"
        assert nested["name"] == "NestedClass"
        assert "private" in nested["modifiers"]

    def test_json_render_security_issue_to_dict(self, sample_security_issue):
        """Test converting a SecurityIssue to a dictionary."""
        result = JsonRenderAdapter.security_issue_to_dict(sample_security_issue)

        # Check expected structure
        assert result["rule_id"] == "SEC001"
        assert result["description"] == "Hardcoded credentials"
        assert result["line_number"] == 42
        assert result["severity"] == "HIGH"
        assert result["context"] == "password = 'hardcoded_password'"

    def test_json_render_token_stats_to_dict(self, sample_token_stats):
        """Test converting TokenStats to a dictionary."""
        result = JsonRenderAdapter.token_stats_to_dict(sample_token_stats)

        # Check expected structure
        assert result["gpt4_tokens"] == 1200
        assert result["claude_tokens"] == 1100

    def test_json_render_annotated_file_to_dict(self, sample_file_data, config):
        """Test converting an AnnotatedFileData to a JSON dictionary."""
        result = JsonRenderAdapter.annotated_file_to_dict(sample_file_data, config)

        # Check expected structure
        assert result["file_path"] == "test/path/to/file.py"
        assert result["language"] == "python"
        assert "def hello():" in result["content"]
        assert result["summary"] == "A simple Python file with a hello function."
        assert "example" in result["tags"]
        assert "test" in result["tags"]

        # Check structured data
        assert len(result["declarations"]) == 1
        assert len(result["imports"]) == 3
        assert "os" in result["imports"]

        # Check token stats
        assert result["token_stats"]["gpt4_tokens"] == 1200

        # Check security issues
        assert len(result["security_issues"]) == 1
        assert result["security_issues"][0]["rule_id"] == "SEC001"

    def test_json_render_doc_file_to_dict(self, sample_doc_data, config):
        """Test converting a ParsedDocData to a JSON dictionary."""
        result = JsonRenderAdapter.doc_file_to_dict(sample_doc_data, config)

        # Check expected structure
        assert result["file_path"] == "docs/README.md"
        assert "# Test Documentation" in result["content"]
        assert result["doc_type"] == "markdown"
        assert result["summary"] == "Documentation about the project."
        assert "docs" in result["tags"]
        assert "readme" in result["tags"]

    def test_xml_render_add_declaration_to_element(self, sample_declaration):
        """Test adding a Declaration to an XML element."""
        parent_elem = ET.Element("parent")
        XmlRenderAdapter.add_declaration_to_element(parent_elem, sample_declaration)

        # Check the structure
        decl_elem = parent_elem.find("declaration")
        assert decl_elem is not None
        assert decl_elem.get("kind") == "class"
        assert decl_elem.get("name") == "TestClass"
        assert decl_elem.get("start_line") == "5"
        assert decl_elem.get("end_line") == "30"

        # Check modifiers
        mods_elem = decl_elem.find("modifiers")
        assert mods_elem is not None
        mod_elem = mods_elem.find("modifier")
        assert mod_elem is not None
        assert mod_elem.text == "public"

        # Check docstring
        doc_elem = decl_elem.find("docstring")
        assert doc_elem is not None
        assert doc_elem.text == "This is a test class docstring."

        # Check children
        children_elem = decl_elem.find("children")
        assert children_elem is not None

        # Check method child
        method_elem = children_elem.findall("declaration")[0]
        assert method_elem.get("kind") == "method"
        assert method_elem.get("name") == "test_method"

        # Check nested class child
        nested_elem = children_elem.findall("declaration")[1]
        assert nested_elem.get("kind") == "class"
        assert nested_elem.get("name") == "NestedClass"

    def test_xml_render_add_security_issue_to_element(self, sample_security_issue):
        """Test adding a SecurityIssue to an XML element."""
        parent_elem = ET.Element("parent")
        XmlRenderAdapter.add_security_issue_to_element(parent_elem, sample_security_issue)

        # Check the structure
        issue_elem = parent_elem.find("security_issue")
        assert issue_elem is not None
        assert issue_elem.get("rule_id") == "SEC001"
        assert issue_elem.get("line_number") == "42"
        assert issue_elem.get("severity") == "HIGH"

        # Check description
        desc_elem = issue_elem.find("description")
        assert desc_elem is not None
        assert desc_elem.text == "Hardcoded credentials"

        # Check context
        ctx_elem = issue_elem.find("context")
        assert ctx_elem is not None
        assert ctx_elem.text == "password = 'hardcoded_password'"

    def test_xml_render_add_token_stats_to_element(self, sample_token_stats):
        """Test adding TokenStats to an XML element."""
        parent_elem = ET.Element("parent")
        XmlRenderAdapter.add_token_stats_to_element(parent_elem, sample_token_stats)

        # Check the structure
        stats_elem = parent_elem.find("token_stats")
        assert stats_elem is not None

        # Check model elements
        model_elems = stats_elem.findall("model")
        assert len(model_elems) == 2

        # Check individual models
        model_map = {elem.get("name"): int(elem.get("tokens")) for elem in model_elems}
        assert model_map["gpt4"] == 1200
        assert model_map["claude"] == 1100

    def test_xml_render_create_annotated_file_element(self, sample_file_data, config):
        """Test creating an XML element for an AnnotatedFileData."""
        result = XmlRenderAdapter.create_annotated_file_element(sample_file_data, config)

        # Check basic structure
        assert result.tag == "file"
        assert result.get("path") == "test/path/to/file.py"
        assert result.get("language") == "python"

        # Check summary
        summary_elem = result.find("summary")
        assert summary_elem is not None
        assert summary_elem.text == "A simple Python file with a hello function."

        # Check tags
        tags_elem = result.find("tags")
        assert tags_elem is not None
        tag_texts = [tag.text for tag in tags_elem.findall("tag")]
        assert "example" in tag_texts
        assert "test" in tag_texts

        # Check declarations
        decls_elem = result.find("declarations")
        assert decls_elem is not None
        decl_elem = decls_elem.find("declaration")
        assert decl_elem is not None
        assert decl_elem.get("kind") == "class"
        assert decl_elem.get("name") == "TestClass"

        # Check imports
        imports_elem = result.find("imports")
        assert imports_elem is not None
        import_texts = [imp.text for imp in imports_elem.findall("import")]
        assert "os" in import_texts
        assert "sys" in import_texts
        assert "logging" in import_texts

        # Check token stats
        stats_elem = result.find("token_stats")
        assert stats_elem is not None

        # Check security issues
        issues_elem = result.find("security_issues")
        assert issues_elem is not None
        issue_elem = issues_elem.find("security_issue")
        assert issue_elem is not None
        assert issue_elem.get("rule_id") == "SEC001"

        # Check content
        content_elem = result.find("content")
        assert content_elem is not None
        assert "def hello():" in content_elem.text

    def test_xml_render_create_doc_file_element(self, sample_doc_data, config):
        """Test creating an XML element for a ParsedDocData."""
        result = XmlRenderAdapter.create_doc_file_element(sample_doc_data, config)

        # Check basic structure
        assert result.tag == "doc"
        assert result.get("path") == "docs/README.md"
        assert result.get("type") == "markdown"

        # Check summary
        summary_elem = result.find("summary")
        assert summary_elem is not None
        assert summary_elem.text == "Documentation about the project."

        # Check tags
        tags_elem = result.find("tags")
        assert tags_elem is not None
        tag_texts = [tag.text for tag in tags_elem.findall("tag")]
        assert "docs" in tag_texts
        assert "readme" in tag_texts

        # Check content
        content_elem = result.find("content")
        assert content_elem is not None
        assert "# Test Documentation" in content_elem.text

    def test_text_render_declarations(self, sample_declaration):
        """Test rendering declarations as plain text."""
        result = TextRenderAdapter.render_declarations([sample_declaration])

        # Check expected output
        assert "=== DECLARATIONS ===" in result
        assert "Class: TestClass (lines 5-30) [public]" in result

        # For method, check basic structure and each modifier individually
        method_line = result[2]  # The method should be the third line in the result list
        assert "Method: test_method (lines 10-20)" in method_line
        assert "public" in method_line
        assert "static" in method_line
        assert "  Class: NestedClass (lines 21-29) [private]" in result

    def test_text_render_imports(self):
        """Test rendering imports as plain text."""
        imports = ["os", "sys", "logging"]
        result = TextRenderAdapter.render_imports(imports)

        # Check expected output
        assert "=== IMPORTS ===" in result
        assert "- os" in result
        assert "- sys" in result
        assert "- logging" in result

    def test_text_render_security_issues(self, sample_security_issue):
        """Test rendering security issues as plain text."""
        result = TextRenderAdapter.render_security_issues([sample_security_issue])

        # Check expected output
        assert "=== SECURITY ISSUES ===" in result
        assert "[HIGH] SEC001 - Line 42: Hardcoded credentials" in result

    def test_text_render_token_stats(self, sample_token_stats):
        """Test rendering token statistics as plain text."""
        result = TextRenderAdapter.render_token_stats(sample_token_stats)

        # Check expected output
        assert "=== TOKEN STATISTICS ===" in result
        assert "GPT-4: 1,200" in result
        assert "Claude: 1,100" in result

    def test_text_render_file_content(self, config):
        """Test rendering file content as plain text."""
        content = "def test():\n    return True"
        result = TextRenderAdapter.render_file_content(content, config)

        # Check that content is split into lines
        assert result[0] == "def test():"
        assert result[1] == "    return True"

        # Test with line numbers
        config.show_line_numbers = True
        result = TextRenderAdapter.render_file_content(content, config)
        assert result[0] == "   1 | def test():"
        assert result[1] == "   2 |     return True"

    def test_text_render_annotated_file(self, sample_file_data, config):
        """Test rendering a complete annotated file as plain text."""
        result = TextRenderAdapter.render_annotated_file(sample_file_data, config)

        # Concatenate for easier assertions
        content = "\n".join(result)
        assert "FILE: test/path/to/file.py" in content
        assert "=== SUMMARY ===" in content
        assert "=== TAGS ===" in content
        assert "example, test" in content
        assert "=== DECLARATIONS ===" in content
        assert "=== IMPORTS ===" in content
        assert "=== SECURITY ISSUES ===" in content
        assert "=== TOKEN STATISTICS ===" in content
        assert "=== CONTENT ===" in content
        assert "def hello():" in content

    def test_text_render_doc_file(self, sample_doc_data, config):
        """Test rendering a documentation file as plain text."""
        result = TextRenderAdapter.render_doc_file(sample_doc_data, config)

        # Concatenate for easier assertions
        content = "\n".join(result)
        assert "DOCUMENTATION: docs/README.md" in content
        assert "=== SUMMARY ===" in content
        assert "Documentation about the project." in content
        assert "=== TAGS ===" in content
        assert "docs, readme" in content
        assert "=== CONTENT ===" in content
        assert "# Test Documentation" in content
        assert "This is test documentation content." in content


if __name__ == "__main__":
    pytest.main(["-v", __file__])
