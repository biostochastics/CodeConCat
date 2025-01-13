"""
symbol_index.py
Builds a global index of all symbols (classes, functions, etc.)
and optionally cross-references usage sites.
"""

from typing import List, Dict
from codeconcat.base_types import ParsedFileData, Declaration

class SymbolIndex:
    def __init__(self):
        # symbol_table: dict of { symbol_name: [ (file_path, start_line, end_line), ... ] }
        self.symbol_table: Dict[str, List[dict]] = {}

        # references: dict of { symbol_name: [ (file_path, usage_line), ... ] }
        # This is more advanced usage for cross-referencing
        self.references: Dict[str, List[dict]] = {}

    def build_index(self, parsed_files: List[ParsedFileData]):
        """
        Collect all declarations from parsed_files and store them in symbol_table.
        """
        for pfile in parsed_files:
            for decl in pfile.declarations:
                symbol = decl.name
                entry = {
                    "file": pfile.file_path,
                    "start_line": decl.start_line,
                    "end_line": decl.end_line,
                    "kind": decl.kind,
                }
                self.symbol_table.setdefault(symbol, []).append(entry)

    def find_references(self, parsed_files: List[ParsedFileData]):
        """
        Very naive example: We'll look for any symbol name in the lines of code.
        In a real cross-referencing system, you'd do a deeper AST pass to find references.
        """
        for pfile in parsed_files:
            lines = pfile.content.split("\n")
            for i, line in enumerate(lines, start=1):
                for symbol, entries in self.symbol_table.items():
                    # Skip if this line is part of the symbol's definition
                    is_definition = any(
                        e["file"] == pfile.file_path and
                        e["start_line"] <= i <= e["end_line"]
                        for e in entries
                    )
                    if is_definition:
                        continue

                    # Look for symbol in various contexts:
                    # - Exact match: "symbol"
                    # - Assignment: "x = symbol"
                    # - Call: "symbol()"
                    # - Import: "import symbol" or "from x import symbol"
                    # - Class instantiation: "x = symbol()"
                    # - Method call: "x.symbol"
                    if any(pattern in line for pattern in [
                        f" {symbol}",  # space before to avoid partial matches
                        f"({symbol}",  # function call
                        f"import {symbol}",  # import statement
                        f"= {symbol}",  # assignment
                        f"={symbol}",  # assignment without space
                        f".{symbol}",  # method call
                        f", {symbol}",  # list context
                        f"[{symbol}",  # list/array context
                        f"({symbol}",  # tuple/call context
                        f"{symbol})",  # end of call
                        f"{symbol},",  # comma-separated list
                    ]):
                        ref_entry = {
                            "file": pfile.file_path,
                            "line": i,
                            "context": line.strip()[:200]  # snippet
                        }
                        self.references.setdefault(symbol, []).append(ref_entry)

    def print_index(self):
        """Simple debug function to print the symbol table."""
        for symbol, entries in self.symbol_table.items():
            print(f"Symbol: {symbol}")
            for e in entries: 
                print(f"  - {e}")

    def print_references(self, symbol_name: str):
        """Debug function to show references to a particular symbol."""
        refs = self.references.get(symbol_name, [])
        if not refs:
            print(f"No references found for symbol '{symbol_name}'.")
            return
        print(f"References to symbol '{symbol_name}':")
        for r in refs:
            print(f"  {r['file']} : line {r['line']}")
            print(f"    {r['context']}")
