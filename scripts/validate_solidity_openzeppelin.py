#!/usr/bin/env python3
"""
Validate TreeSitterSolidityParser against OpenZeppelin contracts library.

This script parses all Solidity files in the OpenZeppelin contracts library
and collects metrics on parse accuracy and security pattern detection.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from codeconcat.parser.language_parsers.base_tree_sitter_parser import (
    TREE_SITTER_AVAILABLE,
)

if not TREE_SITTER_AVAILABLE:
    print("Error: tree-sitter not available")
    sys.exit(1)

from codeconcat.parser.language_parsers.tree_sitter_solidity_parser import (
    TreeSitterSolidityParser,
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def find_solidity_files(contracts_dir: Path) -> List[Path]:
    """Find all Solidity files in the contracts directory."""
    return list(contracts_dir.glob("**/*.sol"))


def analyze_contract(parser: TreeSitterSolidityParser, file_path: Path) -> Dict:
    """Analyze a single Solidity contract file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        result = parser.parse(content)

        analysis = {
            "file": str(file_path.relative_to(file_path.parent.parent.parent)),
            "success": not bool(result.error),
            "errors": [result.error] if result.error else None,
            "declarations": len(result.declarations) if result.declarations else 0,
            "declaration_types": {},
            "security_patterns": {},
            "metadata": {},
        }

        # Count declaration types
        if result.declarations:
            for decl in result.declarations:
                decl_type = decl.type
                analysis["declaration_types"][decl_type] = (
                    analysis["declaration_types"].get(decl_type, 0) + 1
                )

        # Extract security patterns from metadata
        if result.metadata:
            if "security_patterns" in result.metadata:
                analysis["security_patterns"] = result.metadata["security_patterns"]
            if "pattern_counts" in result.metadata:
                analysis["metadata"]["pattern_counts"] = result.metadata["pattern_counts"]
            if "external_calls" in result.metadata:
                analysis["metadata"]["external_calls_count"] = len(
                    result.metadata["external_calls"]
                )

        return analysis

    except Exception as e:
        return {
            "file": str(file_path.relative_to(file_path.parent.parent.parent)),
            "success": False,
            "errors": [str(e)],
            "declarations": 0,
            "declaration_types": {},
            "security_patterns": {},
            "metadata": {},
        }


def generate_report(results: List[Dict]) -> Dict:
    """Generate a summary report from analysis results."""
    total_files = len(results)
    successful_parses = sum(1 for r in results if r["success"])
    failed_parses = total_files - successful_parses

    # Aggregate declaration types
    all_declaration_types = {}
    for result in results:
        for decl_type, count in result["declaration_types"].items():
            all_declaration_types[decl_type] = all_declaration_types.get(decl_type, 0) + count

    # Aggregate security patterns
    security_pattern_files = {}
    pattern_counts = {}
    total_external_calls = 0

    for result in results:
        if result["security_patterns"]:
            for pattern in result["security_patterns"]:
                if pattern not in security_pattern_files:
                    security_pattern_files[pattern] = []
                security_pattern_files[pattern].append(result["file"])

        if "pattern_counts" in result.get("metadata", {}):
            for pattern, count in result["metadata"]["pattern_counts"].items():
                pattern_counts[pattern] = pattern_counts.get(pattern, 0) + count

        if "external_calls_count" in result.get("metadata", {}):
            total_external_calls += result["metadata"]["external_calls_count"]

    # Identify files that failed to parse
    failed_files = [r["file"] for r in results if not r["success"]]

    # Calculate accuracy
    parse_accuracy = (successful_parses / total_files) * 100 if total_files > 0 else 0

    report = {
        "summary": {
            "total_files": total_files,
            "successful_parses": successful_parses,
            "failed_parses": failed_parses,
            "parse_accuracy_percent": round(parse_accuracy, 2),
        },
        "declaration_statistics": {
            "total_declarations": sum(all_declaration_types.values()),
            "by_type": all_declaration_types,
        },
        "security_analysis": {
            "patterns_detected": len(security_pattern_files),
            "pattern_files": {
                pattern: len(files) for pattern, files in security_pattern_files.items()
            },
            "pattern_counts": pattern_counts,
            "total_external_calls": total_external_calls,
        },
        "failed_files": failed_files[:10] if failed_files else [],  # Show first 10 failures
    }

    return report


def main():
    """Main validation script."""
    # Path to OpenZeppelin contracts
    contracts_dir = Path("/tmp/openzeppelin-contracts/contracts")

    if not contracts_dir.exists():
        logger.error(f"OpenZeppelin contracts not found at {contracts_dir}")
        logger.info("Please clone OpenZeppelin contracts to /tmp/openzeppelin-contracts")
        sys.exit(1)

    # Initialize parser
    parser = TreeSitterSolidityParser()
    logger.info("Initialized TreeSitterSolidityParser")

    # Find all Solidity files
    sol_files = find_solidity_files(contracts_dir)
    logger.info(f"Found {len(sol_files)} Solidity files to analyze")

    if not sol_files:
        logger.error("No Solidity files found!")
        sys.exit(1)

    # Analyze each file
    results = []
    for i, file_path in enumerate(sol_files, 1):
        if i % 20 == 0:
            logger.info(f"Progress: {i}/{len(sol_files)} files analyzed")

        analysis = analyze_contract(parser, file_path)
        results.append(analysis)

    # Generate report
    logger.info("Generating report...")
    report = generate_report(results)

    # Display report
    print("\n" + "=" * 60)
    print("OPENZEPPELIN CONTRACTS VALIDATION REPORT")
    print("=" * 60)

    print("\n📊 PARSE STATISTICS:")
    print(f"  • Total files: {report['summary']['total_files']}")
    print(f"  • Successful: {report['summary']['successful_parses']}")
    print(f"  • Failed: {report['summary']['failed_parses']}")
    print(f"  • Accuracy: {report['summary']['parse_accuracy_percent']}%")

    print("\n📝 DECLARATION TYPES:")
    print(f"  • Total declarations: {report['declaration_statistics']['total_declarations']}")
    for decl_type, count in sorted(report["declaration_statistics"]["by_type"].items()):
        print(f"    - {decl_type}: {count}")

    print("\n🔒 SECURITY PATTERNS:")
    if report["security_analysis"]["patterns_detected"] > 0:
        print(f"  • Patterns detected: {report['security_analysis']['patterns_detected']}")
        for pattern, file_count in sorted(report["security_analysis"]["pattern_files"].items()):
            print(f"    - {pattern}: found in {file_count} files")

        if report["security_analysis"]["pattern_counts"]:
            print("\n  • Pattern occurrence counts:")
            for pattern, count in sorted(report["security_analysis"]["pattern_counts"].items()):
                print(f"    - {pattern}: {count} occurrences")

        if report["security_analysis"]["total_external_calls"] > 0:
            print(
                f"\n  • Total external calls detected: {report['security_analysis']['total_external_calls']}"
            )
    else:
        print("  • No security patterns detected")

    if report["failed_files"]:
        print("\n❌ FAILED FILES (first 10):")
        for file in report["failed_files"]:
            print(f"  • {file}")

    # Save detailed report to JSON
    report_path = Path("openzeppelin_validation_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    logger.info(f"Detailed report saved to {report_path}")

    # Check success criteria
    print("\n" + "=" * 60)
    print("VALIDATION CRITERIA CHECK:")
    print("=" * 60)

    accuracy_threshold = 97.0
    accuracy_pass = report["summary"]["parse_accuracy_percent"] >= accuracy_threshold

    print(f"\n✓ Parse Accuracy: {report['summary']['parse_accuracy_percent']}% ", end="")
    if accuracy_pass:
        print("✅ PASS (>= 97%)")
    else:
        print(f"❌ FAIL (< {accuracy_threshold}%)")

    # Security pattern detection check
    patterns_detected = report["security_analysis"]["patterns_detected"] > 0
    print("✓ Security Pattern Detection: ", end="")
    if patterns_detected:
        print(f"✅ PASS ({report['security_analysis']['patterns_detected']} patterns detected)")
    else:
        print("⚠️  WARNING (No patterns detected - may need investigation)")

    # Overall result
    print("\n" + "=" * 60)
    if accuracy_pass:
        print("🎉 VALIDATION SUCCESSFUL!")
        sys.exit(0)
    else:
        print("❌ VALIDATION FAILED - Parse accuracy below 97% threshold")
        sys.exit(1)


if __name__ == "__main__":
    main()
