#!/usr/bin/env python3
"""
Tree-sitter dependency verification tool for CodeConCat.

This script checks if all the required Tree-sitter grammars are correctly
installed and available.
"""

import os
import sys
import logging

# Add the parent directory to path so we can import codeconcat modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from codeconcat.diagnostics import verify_tree_sitter_dependencies

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

def main():
    """Main entry point for the verification script."""
    print("CodeConCat Tree-sitter Grammar Verification Tool")
    print("================================================\n")
    
    # Run verification
    success, successful_langs, failed_langs = verify_tree_sitter_dependencies()
    
    # Print summary
    if success:
        print(f"\n✅ All {len(successful_langs)} Tree-sitter grammars are properly installed.")
        print(f"Supported languages: {', '.join(sorted(successful_langs))}")
        return 0
    else:
        print(f"\n❌ Tree-sitter dependency check failed.")
        print(f"✅ Successful: {len(successful_langs)} languages")
        print(f"❌ Failed: {len(failed_langs)} languages")
        
        # Print detailed errors
        if failed_langs:
            print("\nError details:")
            for i, error in enumerate(failed_langs, 1):
                print(f"  {i}. {error}")
                
        print("\nSuggestions for fixing:")
        print("  1. Run 'pip install -U tree-sitter' to ensure the core library is installed")
        print("  2. Check that your Python environment has the necessary compilers for native extensions")
        print("  3. Try reinstalling CodeConCat to rebuild all Tree-sitter grammars")
        return 1

if __name__ == "__main__":
    sys.exit(main())
