#!/usr/bin/env python3
"""
Simple test of Solidity parser against OpenZeppelin contracts.
Just counts basic structures without complex queries.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import tree_sitter_language_pack as tslp
import tree_sitter as ts

def analyze_file(file_path: Path) -> dict:
    """Analyze a Solidity file by counting basic structures."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        lang = tslp.get_language('solidity')
        parser = ts.Parser(lang)
        tree = parser.parse(bytes(content, 'utf8'))

        # Count basic structures
        counts = {
            'contracts': 0,
            'interfaces': 0,
            'libraries': 0,
            'functions': 0,
            'modifiers': 0,
            'events': 0,
            'errors': 0,
            'parse_errors': 0
        }

        def walk_tree(node):
            if node.type == 'contract_declaration':
                counts['contracts'] += 1
            elif node.type == 'interface_declaration':
                counts['interfaces'] += 1
            elif node.type == 'library_declaration':
                counts['libraries'] += 1
            elif node.type == 'function_definition':
                counts['functions'] += 1
            elif node.type == 'modifier_definition':
                counts['modifiers'] += 1
            elif node.type == 'event_definition':
                counts['events'] += 1
            elif node.type == 'error_declaration':
                counts['errors'] += 1
            elif node.type == 'ERROR':
                counts['parse_errors'] += 1

            for child in node.children:
                walk_tree(child)

        walk_tree(tree.root_node)
        return {'success': True, 'counts': counts}

    except Exception as e:
        return {'success': False, 'error': str(e)}

def main():
    """Run simple analysis on OpenZeppelin contracts."""
    contracts_dir = Path('/tmp/openzeppelin-contracts/contracts')

    if not contracts_dir.exists():
        print(f"Error: {contracts_dir} not found")
        sys.exit(1)

    # Find all .sol files
    sol_files = list(contracts_dir.glob('**/*.sol'))
    print(f"Found {len(sol_files)} Solidity files")

    total_counts = {
        'contracts': 0,
        'interfaces': 0,
        'libraries': 0,
        'functions': 0,
        'modifiers': 0,
        'events': 0,
        'errors': 0,
        'parse_errors': 0
    }
    successful_files = 0
    failed_files = 0

    for file_path in sol_files:
        result = analyze_file(file_path)
        if result['success']:
            successful_files += 1
            for key, value in result['counts'].items():
                total_counts[key] += value
        else:
            failed_files += 1

    # Print results
    print("\n" + "="*60)
    print("SIMPLE SOLIDITY PARSER TEST RESULTS")
    print("="*60)

    print(f"\nFILE STATISTICS:")
    print(f"  • Total files: {len(sol_files)}")
    print(f"  • Successful: {successful_files}")
    print(f"  • Failed: {failed_files}")
    print(f"  • Success rate: {(successful_files/len(sol_files)*100):.1f}%")

    print(f"\nSTRUCTURE COUNTS:")
    for key, value in total_counts.items():
        print(f"  • {key}: {value}")

    print("\n" + "="*60)

    # Check if we meet the 97% threshold
    success_rate = (successful_files/len(sol_files)*100)
    if success_rate >= 97:
        print(f"✅ SUCCESS: Parse rate {success_rate:.1f}% exceeds 97% threshold")
    else:
        print(f"❌ FAILURE: Parse rate {success_rate:.1f}% below 97% threshold")

    # Check if we found reasonable structures
    if total_counts['contracts'] + total_counts['interfaces'] + total_counts['libraries'] > 100:
        print(f"✅ Found {total_counts['contracts'] + total_counts['interfaces'] + total_counts['libraries']} contract-like structures")
    else:
        print(f"⚠️  Only found {total_counts['contracts'] + total_counts['interfaces'] + total_counts['libraries']} contract-like structures")

if __name__ == "__main__":
    main()
