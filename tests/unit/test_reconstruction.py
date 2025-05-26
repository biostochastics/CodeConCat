"""Tests for the reconstruction module.

This module tests the ability to reconstruct files from various output formats.
"""

import tempfile
import unittest
from pathlib import Path

from codeconcat.reconstruction import CodeConcatReconstructor, reconstruct_from_file


class TestReconstruction(unittest.TestCase):
    """Test the reconstruction functionality."""

    def setUp(self):
        """Set up test cases."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up after tests."""
        self.temp_dir.cleanup()

    def test_markdown_format(self):
        """Test reconstructing from markdown format."""
        # Create sample markdown content
        markdown_content = """# Project Files

## `file1.py`

```python
def hello():
    print("Hello World!")
    
# This is a comment
```

## `path/to/file2.js`

```javascript
function greet() {
    console.log("Hello from JavaScript!");
    // JS comment
}
```
"""
        # Create temp markdown file
        md_file = self.output_dir / "test.md"
        with open(md_file, "w") as f:
            f.write(markdown_content)

        # Run reconstruction
        reconstructor = CodeConcatReconstructor(self.output_dir / "reconstructed")
        reconstructor.reconstruct(str(md_file), "markdown")

        # Verify files were created
        file1_path = self.output_dir / "reconstructed" / "file1.py"
        file2_path = self.output_dir / "reconstructed" / "path" / "to" / "file2.js"

        self.assertTrue(file1_path.exists(), "file1.py should exist")
        self.assertTrue(file2_path.exists(), "file2.js should exist")

        # Verify content is correct (no markdown artifacts)
        with open(file1_path, "r") as f:
            file1_content = f.read()
        with open(file2_path, "r") as f:
            file2_content = f.read()

        self.assertEqual(
            file1_content, 'def hello():\n    print("Hello World!")\n    \n# This is a comment'
        )
        self.assertEqual(
            file2_content,
            'function greet() {\n    console.log("Hello from JavaScript!");\n    // JS comment\n}',
        )

    def test_json_format(self):
        """Test reconstructing from JSON format."""
        # Create sample JSON content
        json_content = """{
  "files": [
    {
      "path": "file1.py",
      "content": "def hello():\\n    print(\\"Hello World!\\")\\n    \\n# This is a comment"
    },
    {
      "path": "path/to/file2.js",
      "content": "function greet() {\\n    console.log(\\"Hello from JavaScript!\\");\\n    // JS comment\\n}"
    }
  ]
}"""
        # Create temp JSON file
        json_file = self.output_dir / "test.json"
        with open(json_file, "w") as f:
            f.write(json_content)

        # Run reconstruction
        reconstructor = CodeConcatReconstructor(self.output_dir / "reconstructed")
        reconstructor.reconstruct(str(json_file), "json")

        # Verify files were created
        file1_path = self.output_dir / "reconstructed" / "file1.py"
        file2_path = self.output_dir / "reconstructed" / "path" / "to" / "file2.js"

        self.assertTrue(file1_path.exists(), "file1.py should exist")
        self.assertTrue(file2_path.exists(), "file2.js should exist")

        # Verify content is correct
        with open(file1_path, "r") as f:
            file1_content = f.read()
        with open(file2_path, "r") as f:
            file2_content = f.read()

        self.assertEqual(
            file1_content, 'def hello():\n    print("Hello World!")\n    \n# This is a comment'
        )
        self.assertEqual(
            file2_content,
            'function greet() {\n    console.log("Hello from JavaScript!");\n    // JS comment\n}',
        )

    def test_xml_format(self):
        """Test reconstructing from XML format."""
        # Create sample XML content
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<codeconcat>
  <files>
    <file path="file1.py">
      <content>def hello():
    print("Hello World!")
    
# This is a comment</content>
    </file>
    <file path="path/to/file2.js">
      <content>function greet() {
    console.log("Hello from JavaScript!");
    // JS comment
}</content>
    </file>
  </files>
</codeconcat>
"""
        # Create temp XML file
        xml_file = self.output_dir / "test.xml"
        with open(xml_file, "w") as f:
            f.write(xml_content)

        # Run reconstruction
        reconstructor = CodeConcatReconstructor(self.output_dir / "reconstructed")
        reconstructor.reconstruct(str(xml_file), "xml")

        # Verify files were created
        file1_path = self.output_dir / "reconstructed" / "file1.py"
        file2_path = self.output_dir / "reconstructed" / "path" / "to" / "file2.js"

        self.assertTrue(file1_path.exists(), "file1.py should exist")
        self.assertTrue(file2_path.exists(), "file2.js should exist")

        # Verify content is correct
        with open(file1_path, "r") as f:
            file1_content = f.read()
        with open(file2_path, "r") as f:
            file2_content = f.read()

        self.assertEqual(
            file1_content, 'def hello():\n    print("Hello World!")\n    \n# This is a comment'
        )
        self.assertEqual(
            file2_content,
            'function greet() {\n    console.log("Hello from JavaScript!");\n    // JS comment\n}',
        )

    def test_compressed_content(self):
        """Test handling of compressed content in reconstructed files."""
        # Create sample markdown with compression placeholders
        markdown_content = """# Project Files

## `compressed_file.py`

```python
def start_function():
    print("Important part at the beginning")
    
    [...code omitted: 15 lines, 0 issues]
    
    print("Important part at the end")
```
"""
        # Create temp markdown file
        md_file = self.output_dir / "test_compressed.md"
        with open(md_file, "w") as f:
            f.write(markdown_content)

        # Run reconstruction
        reconstructor = CodeConcatReconstructor(self.output_dir / "reconstructed")
        reconstructor.reconstruct(str(md_file), "markdown")

        # Verify files were created
        file_path = self.output_dir / "reconstructed" / "compressed_file.py"
        self.assertTrue(file_path.exists(), "compressed_file.py should exist")

        # Verify compressed content is preserved
        with open(file_path, "r") as f:
            content = f.read()

        self.assertIn("def start_function():", content)
        self.assertIn("[...code omitted: 15 lines, 0 issues]", content)
        self.assertIn('print("Important part at the end")', content)

        # Ensure no artifacts like triple backticks are present
        self.assertNotIn("```", content)

    def test_multiple_formats(self):
        """Test the ability to auto-detect formats."""
        # Create files in different formats
        markdown_file = self.output_dir / "test.md"
        json_file = self.output_dir / "test.json"
        xml_file = self.output_dir / "test.xml"

        # Create minimal content in each format
        with open(markdown_file, "w") as f:
            f.write("## `test.txt`\n\n```\nTest content\n```\n")

        with open(json_file, "w") as f:
            f.write('{"files":[{"path":"test.txt","content":"Test content"}]}')

        with open(xml_file, "w") as f:
            f.write(
                '<codeconcat><file path="test.txt"><content>Test content</content></file></codeconcat>'
            )

        # Test auto-detection for each format
        for i, file_path in enumerate([markdown_file, json_file, xml_file]):
            output_dir = self.output_dir / f"reconstructed_{i}"
            reconstruct_from_file(str(file_path), str(output_dir))

            # Check result
            result_file = output_dir / "test.txt"
            self.assertTrue(result_file.exists(), f"File should exist for {file_path}")

            with open(result_file, "r") as f:
                content = f.read()
                self.assertEqual(content, "Test content")
