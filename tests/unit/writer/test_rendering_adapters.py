#!/usr/bin/env python3

"""
Comprehensive unit tests for the rendering adapters in CodeConCat.

Tests the decoupled rendering logic for different output formats:
- Markdown rendering
- JSON rendering
- XML rendering
- Text rendering

This test suite provides comprehensive coverage including:
- All adapter classes and their methods
- Data transformation correctness
- Edge cases (empty data, special characters, large inputs)
- Error handling for malformed data
- Configuration options and customization
- Compression functionality
- Performance considerations
"""

import logging
import xml.etree.ElementTree as ET
from typing import List

import pytest

from codeconcat.base_types import (
    AnnotatedFileData,
    CodeConCatConfig,
    ContentSegment,
    ContentSegmentType,
    Declaration,
    ParsedDocData,
    SecurityIssue,
    SecuritySeverity,
    TokenStats,
)
from codeconcat.writer.rendering_adapters import (
    JsonRenderAdapter,
    MarkdownRenderAdapter,
    TextRenderAdapter,
    XmlRenderAdapter,
)

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class TestRenderingAdapters:
    """Comprehensive test class for rendering adapters."""

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
    def minimal_config(self) -> CodeConCatConfig:
        """Fixture providing a minimal CodeConCatConfig instance."""
        return CodeConCatConfig(
            output_dir="out",
            include_file_summary=False,
            include_declarations_in_summary=False,
            include_imports_in_summary=False,
            include_security_in_summary=False,
            include_tokens_in_summary=False,
            enable_token_counting=False,
            disable_symbols=True,
            mask_output_content=True,
        )

    @pytest.fixture
    def compressed_config(self) -> CodeConCatConfig:
        """Fixture providing a compression-enabled config."""
        config = CodeConCatConfig(
            output_dir="out",
            enable_compression=True,
            include_file_summary=True,
        )
        # Mock compressed segments
        config._compressed_segments = {
            "test/path/to/file.py": [
                ContentSegment(
                    segment_type=ContentSegmentType.CODE,
                    content="def important_function():\n    return 42",
                    start_line=1,
                    end_line=2,
                    metadata={"importance": "high"},
                ),
                ContentSegment(
                    segment_type=ContentSegmentType.OMITTED,
                    content="... [15 lines omitted] ...",
                    start_line=3,
                    end_line=17,
                    metadata={"omitted_lines": 15},
                ),
                ContentSegment(
                    segment_type=ContentSegmentType.CODE,
                    content="if __name__ == '__main__':\n    main()",
                    start_line=18,
                    end_line=19,
                ),
            ]
        }
        return config

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
    def complex_declaration_tree(self) -> Declaration:
        """Fixture providing a more complex declaration tree."""
        # Root namespace
        namespace = Declaration(
            kind="namespace",
            name="MyProject",
            start_line=1,
            end_line=100,
            modifiers=set(),
            docstring="Project namespace",
        )

        # Add interface
        interface = Declaration(
            kind="interface",
            name="IDataProcessor",
            start_line=5,
            end_line=15,
            modifiers={"public"},
            docstring="Data processing interface",
        )
        namespace.children.append(interface)

        # Add abstract method to interface
        abstract_method = Declaration(
            kind="method",
            name="process",
            start_line=10,
            end_line=12,
            modifiers={"abstract", "public"},
            docstring="Process data method",
        )
        interface.children.append(abstract_method)

        # Add implementation class
        impl_class = Declaration(
            kind="class",
            name="DataProcessor",
            start_line=20,
            end_line=80,
            modifiers={"public"},
            docstring="Concrete data processor",
        )
        namespace.children.append(impl_class)

        # Add constructor
        constructor = Declaration(
            kind="constructor",
            name="DataProcessor",
            start_line=25,
            end_line=30,
            modifiers={"public"},
            docstring="Constructor",
        )
        impl_class.children.append(constructor)

        return namespace

    @pytest.fixture
    def sample_security_issues(self) -> List[SecurityIssue]:
        """Fixture providing multiple security issues with different severities."""
        return [
            SecurityIssue(
                rule_id="SEC001",
                description="Hardcoded credentials",
                file_path="test.py",
                line_number=42,
                severity=SecuritySeverity.CRITICAL,
                context="password = 'secret123'",
            ),
            SecurityIssue(
                rule_id="SEC002",
                description="SQL injection vulnerability",
                file_path="test.py",
                line_number=100,
                severity=SecuritySeverity.HIGH,
                context="query = 'SELECT * FROM users WHERE id=' + user_id",
            ),
            SecurityIssue(
                rule_id="SEC003",
                description="Use of MD5 hash",
                file_path="test.py",
                line_number=200,
                severity=SecuritySeverity.MEDIUM,
                context="hashlib.md5(data).hexdigest()",
            ),
            SecurityIssue(
                rule_id="SEC004",
                description="Debug mode enabled",
                file_path="test.py",
                line_number=300,
                severity=SecuritySeverity.LOW,
                context="DEBUG = True",
            ),
            SecurityIssue(
                rule_id="INFO001",
                description="TODO comment found",
                file_path="test.py",
                line_number=400,
                severity=SecuritySeverity.INFO,
                context="# TODO: implement this",
            ),
        ]

    @pytest.fixture
    def sample_token_stats(self) -> TokenStats:
        """Fixture providing sample token statistics."""
        return TokenStats(gpt4_tokens=1200, claude_tokens=1100)

    @pytest.fixture
    def large_token_stats(self) -> TokenStats:
        """Fixture providing large token statistics."""
        return TokenStats(gpt4_tokens=1_234_567, claude_tokens=2_345_678)

    @pytest.fixture
    def sample_file_data(
        self, sample_declaration, sample_security_issues, sample_token_stats
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
            security_issues=sample_security_issues,
            tags=["example", "test"],
        )

    @pytest.fixture
    def empty_file_data(self) -> AnnotatedFileData:
        """Fixture providing empty file data."""
        return AnnotatedFileData(
            file_path="empty/file.py",
            language="python",
            content="",
            annotated_content="",
            summary=None,
            declarations=[],
            imports=[],
            token_stats=None,
            security_issues=[],
            tags=[],
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

    @pytest.fixture
    def unicode_doc_data(self) -> ParsedDocData:
        """Fixture providing documentation with unicode characters."""
        return ParsedDocData(
            file_path="docs/unicode.md",
            content="# Unicode Test 🚀\n\n测试中文 العربية русский\n\n```python\nprint('Hello 🌍')\n```",
            doc_type="markdown",
            summary="Unicode documentation test with emojis and international text.",
            tags=["unicode", "test", "🏷️"],
        )

    @pytest.fixture
    def content_segments(self) -> List[ContentSegment]:
        """Fixture providing sample content segments for compression tests."""
        return [
            ContentSegment(
                segment_type=ContentSegmentType.CODE,
                content="def main():",
                start_line=1,
                end_line=1,
            ),
            ContentSegment(
                segment_type=ContentSegmentType.OMITTED,
                content="    # ... [50 lines omitted] ...",
                start_line=2,
                end_line=51,
                metadata={"omitted_lines": 50, "reason": "boilerplate"},
            ),
            ContentSegment(
                segment_type=ContentSegmentType.CODE,
                content="    return result",
                start_line=52,
                end_line=52,
            ),
        ]

    # =====================================
    # MarkdownRenderAdapter Tests
    # =====================================

    def test_markdown_render_declarations_empty(self, config):
        """Test rendering empty declarations list."""
        result = MarkdownRenderAdapter.render_declarations([], "test.py", config)
        assert result == ""

    def test_markdown_render_declarations_complex(self, complex_declaration_tree, config):
        """Test rendering complex declaration tree."""
        result = MarkdownRenderAdapter.render_declarations(
            [complex_declaration_tree], "test.py", config
        )

        assert "### Declarations" in result
        assert "**Namespace**: `MyProject`" in result
        assert "**Interface**: `IDataProcessor`" in result
        assert "**Method**: `process`" in result
        assert "**Class**: `DataProcessor`" in result
        assert "**Constructor**: `DataProcessor`" in result

        # Check indentation for nested elements
        lines = result.split("\n")
        interface_line = next(line for line in lines if "IDataProcessor" in line)
        method_line = next(line for line in lines if "process" in line)

        # Interface should be indented (child of namespace)
        assert interface_line.startswith("  ")
        # Method should be more indented (child of interface)
        assert method_line.startswith("    ")

    def test_markdown_render_declarations_no_modifiers(self, config):
        """Test rendering declarations without modifiers."""
        decl = Declaration(
            kind="function",
            name="simple_func",
            start_line=1,
            end_line=3,
            modifiers=set(),  # No modifiers
        )
        result = MarkdownRenderAdapter.render_declarations([decl], "test.py", config)

        assert "**Function**: `simple_func` (lines 1-3)" in result
        # Should not have empty modifiers bracket
        assert "[" not in result.split("(lines 1-3)")[-1]

    def test_markdown_render_imports_empty(self):
        """Test rendering empty imports list."""
        result = MarkdownRenderAdapter.render_imports([])
        assert result == ""

    def test_markdown_render_imports_special_characters(self):
        """Test rendering imports with special characters."""
        imports = ["sys", "os.path", "module.submodule", "special-chars_123"]
        result = MarkdownRenderAdapter.render_imports(imports)

        assert "### Imports" in result
        assert "- `special-chars_123`" in result
        assert "- `module.submodule`" in result

    def test_markdown_render_security_issues_empty(self):
        """Test rendering empty security issues."""
        result = MarkdownRenderAdapter.render_security_issues([])
        assert result == ""

    def test_markdown_render_security_issues_all_severities(self, sample_security_issues):
        """Test rendering security issues with all severity levels."""
        result = MarkdownRenderAdapter.render_security_issues(sample_security_issues)

        assert "### Security Issues" in result
        assert "| Severity | Rule | Line | Description |" in result

        # Check that issues are sorted by severity (most severe first)
        lines = result.split("\n")
        issue_lines = [
            line
            for line in lines
            if line.startswith("| 🔴")
            or line.startswith("| 🟠")
            or line.startswith("| 🟡")
            or line.startswith("| 🟢")
            or line.startswith("| ℹ️")
        ]

        # First should be CRITICAL
        assert "🔴 CRITICAL" in issue_lines[0]
        # Last should be INFO
        assert "ℹ️ INFO" in issue_lines[-1]

    def test_markdown_render_security_issues_special_characters(self):
        """Test rendering security issues with special characters in descriptions."""
        issue = SecurityIssue(
            rule_id="TEST",
            description="Special chars: <script>alert('xss')</script> & \"quotes\"",
            file_path="test.py",
            line_number=1,
            severity=SecuritySeverity.HIGH,
            context="var x = '<script>alert(1)</script>';",
        )
        result = MarkdownRenderAdapter.render_security_issues([issue])

        # Should preserve special characters (markdown will handle escaping)
        assert "<script>alert('xss')</script>" in result
        assert '& "quotes"' in result

    def test_markdown_render_token_stats_none(self):
        """Test rendering None token statistics."""
        result = MarkdownRenderAdapter.render_token_stats(None)
        assert result == ""

    def test_markdown_render_token_stats_large_numbers(self, large_token_stats):
        """Test rendering large token numbers with proper formatting."""
        result = MarkdownRenderAdapter.render_token_stats(large_token_stats)

        assert "| GPT-4 | 1,234,567 |" in result
        assert "| Claude | 2,345,678 |" in result

    def test_markdown_render_file_content_empty(self, config):
        """Test rendering empty file content."""
        result = MarkdownRenderAdapter.render_file_content("", "python", config)
        assert result == "```\n// No content\n```"

    def test_markdown_render_file_content_unknown_language(self, config):
        """Test rendering content with unknown language."""
        content = "some content"
        result = MarkdownRenderAdapter.render_file_content(content, "unknown", config)
        assert result == "```\nsome content\n```"

    def test_markdown_render_file_content_line_numbers(self, config):
        """Test rendering content with line numbers enabled."""
        config.show_line_numbers = True
        content = "line 1\nline 2\nline 3"
        result = MarkdownRenderAdapter.render_file_content(content, "text", config)

        assert "```text" in result
        assert "   1 | line 1" in result
        assert "   2 | line 2" in result
        assert "   3 | line 3" in result

    def test_markdown_render_file_content_large_line_numbers(self, config):
        """Test rendering content with large line numbers."""
        config.show_line_numbers = True
        lines = [f"line {i}" for i in range(1, 1001)]  # 1000 lines
        content = "\n".join(lines)
        result = MarkdownRenderAdapter.render_file_content(content, "text", config)

        # Check proper padding for large line numbers
        assert "1000 | line 1000" in result

    def test_markdown_render_file_content_compressed(self, compressed_config):
        """Test rendering compressed file content."""
        result = MarkdownRenderAdapter.render_file_content(
            "original content", "python", compressed_config, "test/path/to/file.py"
        )

        assert "```python" in result
        assert "def important_function():" in result
        assert "... [15 lines omitted] ..." in result
        assert "if __name__ == '__main__':" in result

    def test_markdown_render_compressed_content_standalone(self, content_segments):
        """Test rendering compressed content segments directly."""
        result = MarkdownRenderAdapter._render_compressed_content(content_segments, "python")

        assert result.startswith("```python")
        assert result.endswith("```")
        assert "def main():" in result
        assert "# ... [50 lines omitted] ..." in result
        assert "return result" in result

    def test_markdown_render_annotated_file_minimal_config(self, sample_file_data, minimal_config):
        """Test rendering annotated file with minimal configuration."""
        result = MarkdownRenderAdapter.render_annotated_file(sample_file_data, minimal_config)

        # Should only have basic file info and content
        content = "\n".join(result)
        assert "## File: test/path/to/file.py" in content
        assert "### Summary" not in content  # Disabled in minimal config
        assert "### Declarations" not in content  # Disabled
        assert "### Security Issues" not in content  # Masked

    def test_markdown_render_annotated_file_no_summary(self, config):
        """Test rendering annotated file with no summary."""
        file_data = AnnotatedFileData(
            file_path="test.py",
            language="python",
            content="print('test')",
            annotated_content="print('test')",
            summary=None,  # No summary
            declarations=[],
            imports=[],
            token_stats=None,
            security_issues=[],
            tags=[],
        )
        result = MarkdownRenderAdapter.render_annotated_file(file_data, config)

        content = "\n".join(result)
        assert "## File: test.py" in content
        assert "### Summary" not in content

    def test_markdown_render_doc_file_empty_tags(self, config):
        """Test rendering doc file with empty tags."""
        doc_data = ParsedDocData(
            file_path="docs/test.md",
            content="# Test",
            doc_type="markdown",
            summary="Test doc",
            tags=[],  # Empty tags
        )
        result = MarkdownRenderAdapter.render_doc_file(doc_data, config)

        content = "\n".join(result)
        assert "## Documentation: docs/test.md" in content
        assert "**Tags**:" not in content

    def test_markdown_render_doc_file_unicode(self, unicode_doc_data, config):
        """Test rendering doc file with unicode content."""
        result = MarkdownRenderAdapter.render_doc_file(unicode_doc_data, config)

        content = "\n".join(result)
        assert "🚀" in content
        assert "测试中文" in content
        assert "العربية" in content
        assert "русский" in content
        assert "🏷️" in content

    # =====================================
    # JsonRenderAdapter Tests
    # =====================================

    def test_json_declaration_to_dict_empty_modifiers(self):
        """Test converting declaration with empty modifiers."""
        decl = Declaration(
            kind="function",
            name="test",
            start_line=1,
            end_line=5,
            modifiers=set(),
        )
        result = JsonRenderAdapter.declaration_to_dict(decl)

        assert result["modifiers"] == []
        # Docstring might be empty string instead of None
        assert result["docstring"] in (None, "")

    def test_json_declaration_to_dict_nested_children(self, complex_declaration_tree):
        """Test converting complex nested declaration tree."""
        result = JsonRenderAdapter.declaration_to_dict(complex_declaration_tree)

        assert result["kind"] == "namespace"
        assert len(result["children"]) == 2  # Interface and class

        # Check nested structure
        interface = result["children"][0]
        assert interface["kind"] == "interface"
        assert len(interface["children"]) == 1

        method = interface["children"][0]
        assert method["kind"] == "method"
        assert "abstract" in method["modifiers"]

    def test_json_security_issue_to_dict_no_context(self):
        """Test converting security issue without context."""
        issue = SecurityIssue(
            rule_id="TEST",
            description="Test issue",
            file_path="test.py",
            line_number=1,
            severity=SecuritySeverity.LOW,
            context=None,
        )
        result = JsonRenderAdapter.security_issue_to_dict(issue)

        assert result["context"] is None
        assert result["severity"] == "LOW"

    def test_json_token_stats_to_dict_none(self):
        """Test converting None token statistics."""
        result = JsonRenderAdapter.token_stats_to_dict(None)
        assert result is None

    def test_json_segment_to_dict_with_metadata(self):
        """Test converting content segment with metadata."""
        segment = ContentSegment(
            segment_type=ContentSegmentType.OMITTED,
            content="... omitted ...",
            start_line=10,
            end_line=20,
            metadata={
                "omitted_lines": 10,
                "reason": "boilerplate",
                "original_content": "lots of code here",  # Should be filtered out
                "complexity": 5,
            },
        )
        result = JsonRenderAdapter.segment_to_dict(segment)

        assert result["type"] == "omitted"
        assert result["metadata"]["omitted_lines"] == 10
        assert result["metadata"]["reason"] == "boilerplate"
        assert result["metadata"]["complexity"] == 5
        # original_content should be filtered out
        assert "original_content" not in result["metadata"]

    def test_json_segment_to_dict_no_metadata(self):
        """Test converting content segment without metadata."""
        segment = ContentSegment(
            segment_type=ContentSegmentType.CODE,
            content="def test(): pass",
            start_line=1,
            end_line=1,
        )
        result = JsonRenderAdapter.segment_to_dict(segment)

        assert "metadata" not in result

    def test_json_annotated_file_to_dict_compression_applied(
        self, sample_file_data, compressed_config
    ):
        """Test converting annotated file with compression applied."""
        result = JsonRenderAdapter.annotated_file_to_dict(sample_file_data, compressed_config)

        assert result["compression_applied"] is True
        assert "segments" in result
        assert len(result["segments"]) == 3
        assert "segment_stats" in result

    def test_json_annotated_file_to_dict_no_compression(self, sample_file_data, config):
        """Test converting annotated file without compression."""
        result = JsonRenderAdapter.annotated_file_to_dict(sample_file_data, config)

        assert result["compression_applied"] is False
        assert "segments" not in result
        assert "def hello():" in result["content"]

    def test_json_annotated_file_to_dict_masked_content(self, sample_file_data, minimal_config):
        """Test converting annotated file with masked content."""
        result = JsonRenderAdapter.annotated_file_to_dict(sample_file_data, minimal_config)

        # Security issues should be omitted when masked
        assert "security_issues" not in result
        # Symbols should be omitted when disabled
        assert "declarations" not in result

    def test_json_annotated_file_to_dict_unknown_language(self, config):
        """Test converting file with unknown language."""
        file_data = AnnotatedFileData(
            file_path="test.unknown",
            language=None,  # Unknown language
            content="some content",
            annotated_content="some content",
        )
        result = JsonRenderAdapter.annotated_file_to_dict(file_data, config)

        assert result["language"] == "unknown"

    def test_json_doc_file_to_dict_complete(self, unicode_doc_data, config):
        """Test converting complete doc file with all fields."""
        result = JsonRenderAdapter.doc_file_to_dict(unicode_doc_data, config)

        assert result["file_path"] == "docs/unicode.md"
        assert "🚀" in result["content"]
        assert result["doc_type"] == "markdown"
        assert "Unicode" in result["summary"]
        assert "🏷️" in result["tags"]

    # =====================================
    # XmlRenderAdapter Tests
    # =====================================

    def test_xml_add_declaration_no_docstring(self):
        """Test adding declaration without docstring to XML."""
        decl = Declaration(
            kind="function",
            name="test",
            start_line=1,
            end_line=3,
            docstring=None,
        )
        parent = ET.Element("parent")
        XmlRenderAdapter.add_declaration_to_element(parent, decl)

        decl_elem = parent.find("declaration")
        assert decl_elem is not None
        # Should not have docstring element
        assert decl_elem.find("docstring") is None

    def test_xml_add_declaration_no_modifiers(self):
        """Test adding declaration without modifiers to XML."""
        decl = Declaration(
            kind="function",
            name="test",
            start_line=1,
            end_line=3,
            modifiers=set(),
        )
        parent = ET.Element("parent")
        XmlRenderAdapter.add_declaration_to_element(parent, decl)

        decl_elem = parent.find("declaration")
        assert decl_elem is not None
        # Should not have modifiers element
        assert decl_elem.find("modifiers") is None

    def test_xml_add_declaration_no_children(self):
        """Test adding declaration without children to XML."""
        decl = Declaration(
            kind="function",
            name="test",
            start_line=1,
            end_line=3,
        )
        parent = ET.Element("parent")
        XmlRenderAdapter.add_declaration_to_element(parent, decl)

        decl_elem = parent.find("declaration")
        assert decl_elem is not None
        # Should not have children element
        assert decl_elem.find("children") is None

    def test_xml_add_security_issue_no_context(self):
        """Test adding security issue without context to XML."""
        issue = SecurityIssue(
            rule_id="TEST",
            description="Test issue",
            file_path="test.py",
            line_number=1,
            severity=SecuritySeverity.MEDIUM,
            context=None,
        )
        parent = ET.Element("parent")
        XmlRenderAdapter.add_security_issue_to_element(parent, issue)

        issue_elem = parent.find("security_issue")
        assert issue_elem is not None
        # Should not have context element
        assert issue_elem.find("context") is None

    def test_xml_add_security_issue_special_characters(self):
        """Test adding security issue with special characters to XML."""
        issue = SecurityIssue(
            rule_id="XSS001",
            description="XSS vulnerability: <script>alert('test')</script>",
            file_path="test.js",
            line_number=42,
            severity=SecuritySeverity.HIGH,
            context="var x = '<script>alert(\"test\")</script>';",
        )
        parent = ET.Element("parent")
        XmlRenderAdapter.add_security_issue_to_element(parent, issue)

        issue_elem = parent.find("security_issue")
        desc_elem = issue_elem.find("description")
        ctx_elem = issue_elem.find("context")

        # XML should properly escape special characters
        assert "<script>" in desc_elem.text
        assert "alert('test')" in desc_elem.text
        assert '"test"' in ctx_elem.text

    def test_xml_create_annotated_file_element_compression(
        self, sample_file_data, compressed_config
    ):
        """Test creating XML element with compression applied."""
        result = XmlRenderAdapter.create_annotated_file_element(sample_file_data, compressed_config)

        assert result.get("compression_applied") == "true"

        # Check segments
        segments_elem = result.find("segments")
        assert segments_elem is not None

        segment_elems = segments_elem.findall("segment")
        assert len(segment_elems) == 3

        # Check first segment (CODE)
        first_segment = segment_elems[0]
        assert first_segment.get("type") == "code"
        assert first_segment.get("start_line") == "1"

        # Check metadata
        metadata_elem = first_segment.find("metadata")
        assert metadata_elem is not None

    def test_xml_create_annotated_file_element_no_compression(self, sample_file_data, config):
        """Test creating XML element without compression."""
        result = XmlRenderAdapter.create_annotated_file_element(sample_file_data, config)

        assert result.get("compression_applied") == "false"

        # Should not have segments
        assert result.find("segments") is None

        # Should have direct content
        content_elem = result.find("content")
        assert content_elem is not None
        assert "def hello():" in content_elem.text

    def test_xml_create_annotated_file_element_masked_security(
        self, sample_file_data, minimal_config
    ):
        """Test creating XML element with masked security issues."""
        result = XmlRenderAdapter.create_annotated_file_element(sample_file_data, minimal_config)

        # Security issues should not be present when masked
        assert result.find("security_issues") is None
        # Declarations should not be present when symbols disabled
        assert result.find("declarations") is None

    def test_xml_create_doc_file_element_no_summary(self, config):
        """Test creating XML doc element without summary."""
        doc_data = ParsedDocData(
            file_path="test.md",
            content="# Test",
            doc_type="markdown",
            summary=None,
            tags=["test"],
        )
        result = XmlRenderAdapter.create_doc_file_element(doc_data, config)

        assert result.find("summary") is None

    def test_xml_create_doc_file_element_no_tags(self, config):
        """Test creating XML doc element without tags."""
        doc_data = ParsedDocData(
            file_path="test.md",
            content="# Test",
            doc_type="markdown",
            summary="Test",
            tags=[],
        )
        result = XmlRenderAdapter.create_doc_file_element(doc_data, config)

        assert result.find("tags") is None

    def test_xml_create_doc_file_element_unicode(self, unicode_doc_data, config):
        """Test creating XML doc element with unicode content."""
        result = XmlRenderAdapter.create_doc_file_element(unicode_doc_data, config)

        content_elem = result.find("content")
        assert "🚀" in content_elem.text
        assert "测试中文" in content_elem.text

        # Check unicode in tags
        tags_elem = result.find("tags")
        tag_texts = [tag.text for tag in tags_elem.findall("tag")]
        assert "🏷️" in tag_texts

    # =====================================
    # TextRenderAdapter Tests
    # =====================================

    def test_text_render_declarations_empty(self):
        """Test rendering empty declarations as text."""
        result = TextRenderAdapter.render_declarations([])
        assert result == []

    def test_text_render_declarations_complex(self, complex_declaration_tree):
        """Test rendering complex declaration tree as text."""
        result = TextRenderAdapter.render_declarations([complex_declaration_tree])

        content = "\n".join(result)
        assert "=== DECLARATIONS ===" in content
        assert "Namespace: MyProject" in content
        assert "Interface: IDataProcessor" in content
        assert "Class: DataProcessor" in content

        # Check indentation
        assert "  Interface: IDataProcessor" in content
        assert "    Method: process" in content

    def test_text_render_imports_empty(self):
        """Test rendering empty imports as text."""
        result = TextRenderAdapter.render_imports([])
        assert result == []

    def test_text_render_imports_large_list(self):
        """Test rendering large imports list."""
        imports = [f"module_{i}" for i in range(100)]
        result = TextRenderAdapter.render_imports(imports)

        assert "=== IMPORTS ===" in result
        assert len(result) == 101  # Header + 100 imports
        assert "- module_99" in result

    def test_text_render_security_issues_empty(self):
        """Test rendering empty security issues as text."""
        result = TextRenderAdapter.render_security_issues([])
        assert result == []

    def test_text_render_security_issues_sorting(self, sample_security_issues):
        """Test that security issues are properly sorted by severity."""
        result = TextRenderAdapter.render_security_issues(sample_security_issues)

        # Find issue lines (skip header)
        issue_lines = [line for line in result if line.startswith("[")]

        # Should be sorted: CRITICAL, HIGH, MEDIUM, LOW, INFO
        assert issue_lines[0].startswith("[CRITICAL]")
        assert issue_lines[1].startswith("[HIGH]")
        assert issue_lines[2].startswith("[MEDIUM]")
        assert issue_lines[3].startswith("[LOW]")
        assert issue_lines[4].startswith("[INFO]")

    def test_text_render_token_stats_empty(self):
        """Test rendering empty token stats as text."""
        result = TextRenderAdapter.render_token_stats(None)
        assert result == []

    def test_text_render_token_stats_formatting(self, large_token_stats):
        """Test token stats number formatting."""
        result = TextRenderAdapter.render_token_stats(large_token_stats)

        content = "\n".join(result)
        assert "GPT-4: 1,234,567" in content
        assert "Claude: 2,345,678" in content

    def test_text_render_file_content_empty(self, config):
        """Test rendering empty file content as text."""
        result = TextRenderAdapter.render_file_content("", config)
        assert result == [""]

    def test_text_render_file_content_single_line(self, config):
        """Test rendering single line content."""
        result = TextRenderAdapter.render_file_content("single line", config)
        assert result == ["single line"]

    def test_text_render_file_content_line_numbers(self, config):
        """Test rendering content with line numbers."""
        config.show_line_numbers = True
        content = "line 1\nline 2\nline 3"
        result = TextRenderAdapter.render_file_content(content, config)

        assert result[0] == "   1 | line 1"
        assert result[1] == "   2 | line 2"
        assert result[2] == "   3 | line 3"

    def test_text_render_file_content_large_line_numbers(self, config):
        """Test rendering content with large line numbers."""
        config.show_line_numbers = True
        lines = [f"line {i}" for i in range(1, 1001)]
        content = "\n".join(lines)
        result = TextRenderAdapter.render_file_content(content, config)

        # Check proper padding
        assert "1000 | line 1000" in result

    def test_text_render_annotated_file_minimal_config(self, sample_file_data, minimal_config):
        """Test rendering annotated file with minimal configuration."""
        result = TextRenderAdapter.render_annotated_file(sample_file_data, minimal_config)

        content = "\n".join(result)
        assert "FILE: test/path/to/file.py" in content
        assert "=== CONTENT ===" in content
        # Should not have summary section
        assert "=== SUMMARY ===" not in content
        # Should not have declarations section
        assert "=== DECLARATIONS ===" not in content

    def test_text_render_annotated_file_empty_data(self, empty_file_data, config):
        """Test rendering empty annotated file."""
        result = TextRenderAdapter.render_annotated_file(empty_file_data, config)

        content = "\n".join(result)
        assert "FILE: empty/file.py" in content
        assert "=== CONTENT ===" in content
        # Should not have optional sections for empty data
        assert "=== SUMMARY ===" not in content
        assert "=== TAGS ===" not in content

    def test_text_render_doc_file_minimal(self, config):
        """Test rendering minimal doc file."""
        doc_data = ParsedDocData(
            file_path="minimal.md",
            content="Just content",
            doc_type="text",
            summary=None,
            tags=[],
        )
        result = TextRenderAdapter.render_doc_file(doc_data, config)

        content = "\n".join(result)
        assert "DOCUMENTATION: minimal.md" in content
        assert "=== CONTENT ===" in content
        assert "Just content" in content
        # Should not have summary or tags sections
        assert "=== SUMMARY ===" not in content
        assert "=== TAGS ===" not in content

    # =====================================
    # Edge Cases and Error Handling Tests
    # =====================================

    def test_markdown_render_with_none_values(self, config):
        """Test markdown rendering with None values in data structures."""
        # Declaration with None docstring
        decl = Declaration(
            kind="function",
            name="test",
            start_line=1,
            end_line=3,
            docstring=None,
        )
        result = MarkdownRenderAdapter.render_declarations([decl], "test.py", config)

        # Should handle None docstring gracefully
        assert "**Function**: `test`" in result

    def test_json_render_with_special_characters(self):
        """Test JSON rendering preserves special characters correctly."""
        decl = Declaration(
            kind="method",
            name="test_with_unicode_🚀",
            start_line=1,
            end_line=3,
            docstring="测试中文 documentation with emojis 🎉",
        )
        result = JsonRenderAdapter.declaration_to_dict(decl)

        assert result["name"] == "test_with_unicode_🚀"
        assert "测试中文" in result["docstring"]
        assert "🎉" in result["docstring"]

    def test_xml_render_with_empty_elements(self, config):
        """Test XML rendering with empty data structures."""
        file_data = AnnotatedFileData(
            file_path="empty.py",
            language="python",
            content="",
            annotated_content="",
            declarations=[],
            imports=[],
            security_issues=[],
            tags=[],
        )
        result = XmlRenderAdapter.create_annotated_file_element(file_data, config)

        # Should create valid XML even with empty data
        assert result.tag == "file"
        assert result.get("path") == "empty.py"
        # Empty lists should not create elements
        assert result.find("declarations") is None
        assert result.find("imports") is None
        assert result.find("security_issues") is None
        assert result.find("tags") is None

    def test_text_render_with_newlines_and_tabs(self, config):
        """Test text rendering handles newlines and tabs correctly."""
        content = "line 1\n\tindented line\n\n\tempty line above"
        result = TextRenderAdapter.render_file_content(content, config)

        assert result[0] == "line 1"
        assert result[1] == "\tindented line"
        assert result[2] == ""  # Empty line preserved
        assert result[3] == "\tempty line above"

    def test_all_adapters_with_large_data(self, config):
        """Test all adapters handle large data structures efficiently."""
        # Create large declaration tree
        large_decl = Declaration(
            kind="namespace",
            name="LargeNamespace",
            start_line=1,
            end_line=10000,
        )

        # Add many children
        for i in range(100):
            child = Declaration(
                kind="class",
                name=f"Class_{i}",
                start_line=i * 100 + 1,
                end_line=(i + 1) * 100,
                modifiers={"public"},
                docstring=f"Class {i} documentation with details " * 10,  # Long docstring
            )
            large_decl.children.append(child)

        # Test all adapters can handle large data
        md_result = MarkdownRenderAdapter.render_declarations([large_decl], "large.py", config)
        json_result = JsonRenderAdapter.declaration_to_dict(large_decl)

        # Should complete without errors and contain expected content
        assert "Class_99" in md_result
        assert len(json_result["children"]) == 100
        assert json_result["children"][99]["name"] == "Class_99"

    def test_compression_with_invalid_segments(self):
        """Test compression rendering with invalid segment data."""
        # Create segments with edge case data
        segments = [
            ContentSegment(
                segment_type=ContentSegmentType.CODE,
                content="",  # Empty content
                start_line=1,
                end_line=1,
            ),
            ContentSegment(
                segment_type=ContentSegmentType.OMITTED,
                content="... [0 lines omitted] ...",  # Zero lines omitted
                start_line=2,
                end_line=2,
                metadata={"omitted_lines": 0},
            ),
        ]

        result = MarkdownRenderAdapter._render_compressed_content(segments, "python")

        # Should handle edge cases gracefully
        assert "```python" in result
        assert result.endswith("```")

    def test_security_issue_sorting_stability(self):
        """Test that security issue sorting is stable for same severity."""
        issues = [
            SecurityIssue(
                rule_id="A",
                description="First HIGH",
                file_path="test.py",
                line_number=1,
                severity=SecuritySeverity.HIGH,
            ),
            SecurityIssue(
                rule_id="B",
                description="Second HIGH",
                file_path="test.py",
                line_number=2,
                severity=SecuritySeverity.HIGH,
            ),
        ]

        # Test multiple times to ensure stable sorting
        for _ in range(10):
            md_result = MarkdownRenderAdapter.render_security_issues(issues)
            text_result = TextRenderAdapter.render_security_issues(issues)

            # Order should be consistent
            assert "First HIGH" in md_result
            assert "Second HIGH" in md_result
            assert "[HIGH] A" in "\n".join(text_result)
            assert "[HIGH] B" in "\n".join(text_result)

    # =====================================
    # Performance and Memory Tests
    # =====================================

    def test_memory_efficiency_with_large_content(self, config):
        """Test memory efficiency with very large content."""
        # Create large content string (1MB)
        large_content = "x" * (1024 * 1024)

        # Test that adapters don't duplicate large strings unnecessarily
        md_result = MarkdownRenderAdapter.render_file_content(large_content, "text", config)

        # Should contain the content without excessive memory usage
        assert large_content in md_result
        assert len(md_result) > len(large_content)  # Includes markdown formatting

    def test_recursive_declaration_handling(self):
        """Test handling of deeply nested declarations."""
        # Create deeply nested structure
        root = Declaration(
            kind="namespace",
            name="Root",
            start_line=1,
            end_line=1000,
        )

        current = root
        for i in range(50):  # 50 levels deep
            child = Declaration(
                kind="class",
                name=f"Nested_{i}",
                start_line=i * 10 + 1,
                end_line=(i + 1) * 10,
            )
            current.children.append(child)
            current = child

        # Should handle deep nesting without stack overflow
        json_result = JsonRenderAdapter.declaration_to_dict(root)

        # Verify structure is preserved
        assert json_result["name"] == "Root"

        # Navigate to the deepest level
        current_json = json_result
        for i in range(50):
            assert len(current_json["children"]) == 1
            current_json = current_json["children"][0]
            assert current_json["name"] == f"Nested_{i}"


if __name__ == "__main__":
    pytest.main(["-v", __file__])
