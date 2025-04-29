import logging
import os
import pytest
from codeconcat.parser.language_parsers.enhanced_rust_parser import EnhancedRustParser

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

@pytest.fixture
def parser():
    """Fixture providing an EnhancedRustParser instance."""
    return EnhancedRustParser()

@pytest.fixture
def file_path(test_corpus_dir):
    """Fixture providing a path to a sample Rust file for testing."""
    sample_path = os.path.join(test_corpus_dir, "rust", "basic.rs")
    if not os.path.exists(sample_path):
        # Fallback to creating a simple test file
        import tempfile
        fd, temp_path = tempfile.mkstemp(suffix=".rs")
        with os.fdopen(fd, 'w') as f:
            f.write('fn main() { println!("Hello, world!"); }')
        return temp_path
    return sample_path

def test_parser_on_file(parser, file_path):
    """Runs the parser on a given file and prints the results."""
    logger.info(f"--- Testing parser on: {file_path} ---")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        parse_result = parser.parse(content, file_path)
        
        print(f"File: {file_path}")
        print(f"  Declarations found: {len(parse_result.declarations)}")
        # Optionally print declaration details if needed for debugging
        # for decl in parse_result.declarations:
        #     print(f"    - {decl.kind}: {decl.name} (Lines {decl.start_line}-{decl.end_line})")
        print(f"  Imports found: {len(parse_result.imports)}")
        # Check for a single error string
        if parse_result.error:
            print(f"  Error encountered: {parse_result.error}")
        else:
            print("  Errors encountered: 0")
        print("-" * (len(file_path) + 23)) # Match the length of the header line

    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
    except Exception as e:
        logger.error(f"An error occurred while parsing {file_path}: {e}", exc_info=True)

if __name__ == "__main__":
    rust_parser = EnhancedRustParser()
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(base_dir, "..", "..", "..")) # Go up 3 levels to project root
    test_files_dir = os.path.join(project_root, "tests", "parser_test_corpus", "rust") # Path from project root
    
    basic_file = os.path.join(test_files_dir, "basic.rs")
    nested_file = os.path.join(test_files_dir, "nested_structures.rs")
    
    test_parser_on_file(rust_parser, basic_file)
    print("\n") # Add a newline for better separation
    test_parser_on_file(rust_parser, nested_file)
