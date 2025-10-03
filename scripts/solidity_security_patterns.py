#!/usr/bin/env python3
"""
Detect security patterns in OpenZeppelin contracts using direct AST traversal.
This approach works around query node type mismatches by directly walking the tree.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import tree_sitter as ts
import tree_sitter_language_pack as tslp


def detect_security_patterns(file_path: Path) -> dict:
    """Detect security patterns in a Solidity file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        lang = tslp.get_language("solidity")
        parser = ts.Parser(lang)
        tree = parser.parse(bytes(content, "utf8"))

        patterns = {
            "assembly_blocks": [],
            "delegatecalls": [],
            "selfdestruct": [],
            "external_calls": [],
            "payable_functions": [],
            "modifiers": [],
            "reentrancy_guards": [],
            "access_control": [],
            "upgradeable_patterns": [],
        }

        def walk_tree(node, depth=0):
            # Detect assembly blocks
            if node.type == "assembly_statement":
                patterns["assembly_blocks"].append(
                    {"line": node.start_point[0] + 1, "type": "assembly"}
                )

            # Detect function calls that might be security-relevant
            elif node.type == "call_expression":
                func_text = node.text.decode("utf-8")

                # Check for delegatecall
                if "delegatecall" in func_text:
                    patterns["delegatecalls"].append(
                        {"line": node.start_point[0] + 1, "text": func_text[:100]}
                    )

                # Check for selfdestruct/suicide
                if "selfdestruct" in func_text or "suicide" in func_text:
                    patterns["selfdestruct"].append(
                        {"line": node.start_point[0] + 1, "text": func_text[:100]}
                    )

                # Check for external calls (call, send, transfer)
                if any(x in func_text for x in [".call(", ".send(", ".transfer("]):
                    patterns["external_calls"].append(
                        {"line": node.start_point[0] + 1, "text": func_text[:100]}
                    )

            # Detect payable functions
            elif node.type == "function_definition":
                func_text = node.text.decode("utf-8")
                if "payable" in func_text:
                    # Extract function name
                    name_node = None
                    for child in node.children:
                        if child.type == "identifier":
                            name_node = child
                            break

                    patterns["payable_functions"].append(
                        {
                            "line": node.start_point[0] + 1,
                            "name": name_node.text.decode("utf-8") if name_node else "unnamed",
                        }
                    )

            # Detect modifiers
            elif node.type == "modifier_definition":
                name_node = None
                for child in node.children:
                    if child.type == "identifier":
                        name_node = child
                        break

                modifier_name = name_node.text.decode("utf-8") if name_node else "unnamed"
                patterns["modifiers"].append(
                    {"line": node.start_point[0] + 1, "name": modifier_name}
                )

                # Check for reentrancy guard patterns
                if "nonReentrant" in modifier_name or "noReentrant" in modifier_name:
                    patterns["reentrancy_guards"].append(
                        {"line": node.start_point[0] + 1, "name": modifier_name}
                    )

                # Check for access control patterns
                if any(
                    x in modifier_name.lower()
                    for x in ["onlyowner", "onlyadmin", "onlyrole", "authorized"]
                ):
                    patterns["access_control"].append(
                        {"line": node.start_point[0] + 1, "name": modifier_name}
                    )

            # Detect upgradeable patterns
            elif node.type == "import_directive":
                import_text = node.text.decode("utf-8")
                if "upgradeable" in import_text.lower():
                    patterns["upgradeable_patterns"].append(
                        {"line": node.start_point[0] + 1, "import": import_text[:100]}
                    )

            # Recursively walk children
            for child in node.children:
                walk_tree(child, depth + 1)

        walk_tree(tree.root_node)

        return {"success": True, "patterns": patterns}

    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    """Analyze security patterns in OpenZeppelin contracts."""
    contracts_dir = Path("/tmp/openzeppelin-contracts/contracts")

    if not contracts_dir.exists():
        print(f"Error: {contracts_dir} not found")
        sys.exit(1)

    # Find all .sol files
    sol_files = list(contracts_dir.glob("**/*.sol"))
    print(f"Found {len(sol_files)} Solidity files")
    print("=" * 60)

    # Aggregate all patterns
    total_patterns = {
        "assembly_blocks": 0,
        "delegatecalls": 0,
        "selfdestruct": 0,
        "external_calls": 0,
        "payable_functions": 0,
        "modifiers": 0,
        "reentrancy_guards": 0,
        "access_control": 0,
        "upgradeable_patterns": 0,
    }

    files_with_patterns = {
        "assembly_blocks": set(),
        "delegatecalls": set(),
        "selfdestruct": set(),
        "external_calls": set(),
        "payable_functions": set(),
        "modifiers": set(),
        "reentrancy_guards": set(),
        "access_control": set(),
        "upgradeable_patterns": set(),
    }

    successful_files = 0
    failed_files = 0

    # Analyze each file
    for file_path in sol_files:
        result = detect_security_patterns(file_path)
        if result["success"]:
            successful_files += 1
            relative_path = file_path.relative_to(contracts_dir)

            for pattern_type, patterns in result["patterns"].items():
                if patterns:
                    total_patterns[pattern_type] += len(patterns)
                    files_with_patterns[pattern_type].add(str(relative_path))
        else:
            failed_files += 1

    # Print results
    print("\nSECURITY PATTERN DETECTION RESULTS")
    print("=" * 60)

    print("\nFile Analysis:")
    print(f"  • Total files: {len(sol_files)}")
    print(f"  • Successfully analyzed: {successful_files}")
    print(f"  • Failed: {failed_files}")
    print(f"  • Success rate: {(successful_files / len(sol_files) * 100):.1f}%")

    print("\nSecurity Patterns Detected:")
    for pattern_type, count in total_patterns.items():
        if count > 0:
            file_count = len(files_with_patterns[pattern_type])
            pattern_name = pattern_type.replace("_", " ").title()
            print(f"  • {pattern_name}: {count} occurrences in {file_count} files")

    # Check for critical patterns
    print("\n" + "=" * 60)
    print("CRITICAL PATTERN ANALYSIS:")
    print("=" * 60)

    if total_patterns["selfdestruct"] > 0:
        print(f"⚠️  WARNING: Found {total_patterns['selfdestruct']} selfdestruct calls")
    else:
        print("✅ No selfdestruct calls detected")

    if total_patterns["delegatecalls"] > 0:
        print(f"⚠️  WARNING: Found {total_patterns['delegatecalls']} delegatecall usages")
    else:
        print("✅ No delegatecall usages detected")

    if total_patterns["assembly_blocks"] > 0:
        print(f"ℹ️  INFO: Found {total_patterns['assembly_blocks']} assembly blocks for review")

    if total_patterns["external_calls"] > 0:
        print(
            f"ℹ️  INFO: Found {total_patterns['external_calls']} external calls (potential reentrancy)"
        )

    # Check for security controls
    if total_patterns["reentrancy_guards"] > 0:
        print(f"✅ Found {total_patterns['reentrancy_guards']} reentrancy guard implementations")

    if total_patterns["access_control"] > 0:
        print(f"✅ Found {total_patterns['access_control']} access control modifiers")

    if total_patterns["upgradeable_patterns"] > 0:
        print(
            f"ℹ️  INFO: Found {total_patterns['upgradeable_patterns']} upgradeable contract patterns"
        )

    # Save detailed report
    report = {
        "summary": {
            "total_files": len(sol_files),
            "successful_analyses": successful_files,
            "failed_analyses": failed_files,
            "success_rate": round((successful_files / len(sol_files) * 100), 2),
        },
        "patterns": {
            pattern_type: {
                "total_occurrences": count,
                "files_affected": len(files_with_patterns[pattern_type]),
                "file_list": sorted(files_with_patterns[pattern_type])[:10],  # First 10
            }
            for pattern_type, count in total_patterns.items()
        },
    }

    report_path = Path("openzeppelin_security_patterns.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n📄 Detailed report saved to {report_path}")

    # Final validation
    print("\n" + "=" * 60)
    print("VALIDATION RESULTS:")
    print("=" * 60)

    # Check if we detected meaningful patterns
    total_detected = sum(total_patterns.values())
    if total_detected > 0:
        print(f"✅ Successfully detected {total_detected} security patterns")
        print("✅ Security pattern detection is functional")
    else:
        print("⚠️  No security patterns detected - may need investigation")

    return successful_files == len(sol_files) and total_detected > 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
