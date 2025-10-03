#!/usr/bin/env python3
"""
Performance benchmark for TreeSitterSolidityParser.
Tests parsing speed on various file sizes with a focus on 10KB files.
"""

import json
import statistics
import sys
import time
from pathlib import Path
from typing import Dict

sys.path.insert(0, str(Path(__file__).parent.parent))

from codeconcat.parser.language_parsers.tree_sitter_solidity_parser import TreeSitterSolidityParser


def measure_parse_time(
    parser: TreeSitterSolidityParser, content: str, iterations: int = 10
) -> Dict:
    """Measure parsing time over multiple iterations."""
    times = []

    for _ in range(iterations):
        start = time.perf_counter()
        parser.parse(content)
        end = time.perf_counter()
        times.append((end - start) * 1000)  # Convert to milliseconds

    return {
        "mean": statistics.mean(times),
        "median": statistics.median(times),
        "stdev": statistics.stdev(times) if len(times) > 1 else 0,
        "min": min(times),
        "max": max(times),
        "iterations": iterations,
    }


def get_file_size_category(size_bytes: int) -> str:
    """Categorize file size."""
    size_kb = size_bytes / 1024
    if size_kb < 5:
        return "small (<5KB)"
    elif size_kb < 10:
        return "medium (5-10KB)"
    elif size_kb < 15:
        return "target (~10KB)"
    elif size_kb < 50:
        return "large (15-50KB)"
    else:
        return "extra-large (>50KB)"


def benchmark_openzeppelin_files(num_files: int = 20) -> Dict:  # noqa: ARG001
    """Benchmark parsing performance on real OpenZeppelin contracts."""
    contracts_dir = Path("/tmp/openzeppelin-contracts/contracts")

    if not contracts_dir.exists():
        print(f"Error: {contracts_dir} not found")
        return {}

    # Find all .sol files and sort by size
    sol_files = list(contracts_dir.glob("**/*.sol"))
    files_with_sizes = []

    for file_path in sol_files:
        try:
            size = file_path.stat().st_size
            files_with_sizes.append((file_path, size))
        except OSError:
            continue

    # Sort by size to get a good distribution
    files_with_sizes.sort(key=lambda x: x[1])

    # Select files around 10KB and a distribution of sizes
    target_10kb = []
    size_categories = {
        "small (<5KB)": [],
        "medium (5-10KB)": [],
        "target (~10KB)": [],
        "large (15-50KB)": [],
        "extra-large (>50KB)": [],
    }

    for file_path, size in files_with_sizes:
        category = get_file_size_category(size)
        size_categories[category].append((file_path, size))

        # Special focus on files around 10KB (8-12KB)
        if 8192 <= size <= 12288:
            target_10kb.append((file_path, size))

    # Benchmark results
    results = {"by_category": {}, "target_10kb_files": [], "all_benchmarks": []}

    parser = TreeSitterSolidityParser()

    # Benchmark files around 10KB
    print("\n📊 BENCHMARKING ~10KB FILES")
    print("=" * 60)

    for file_path, size in target_10kb[:5]:  # Test up to 5 files around 10KB
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        benchmark = measure_parse_time(parser, content, iterations=20)
        file_info = {
            "file": file_path.name,
            "size_bytes": size,
            "size_kb": round(size / 1024, 2),
            "parse_time_ms": round(benchmark["mean"], 2),
            "median_ms": round(benchmark["median"], 2),
            "min_ms": round(benchmark["min"], 2),
            "max_ms": round(benchmark["max"], 2),
        }

        results["target_10kb_files"].append(file_info)
        print(
            f"  • {file_info['file']} ({file_info['size_kb']}KB): {file_info['parse_time_ms']}ms avg"
        )

    # Benchmark a sample from each category
    print("\n📈 BENCHMARKING BY SIZE CATEGORY")
    print("=" * 60)

    for category, files in size_categories.items():
        if not files:
            continue

        # Sample up to 3 files from each category
        sample_files = files[:3]
        category_benchmarks = []

        for file_path, size in sample_files:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            benchmark = measure_parse_time(parser, content, iterations=10)
            category_benchmarks.append({"size_kb": size / 1024, "parse_time_ms": benchmark["mean"]})

        if category_benchmarks:
            avg_time = statistics.mean([b["parse_time_ms"] for b in category_benchmarks])
            avg_size = statistics.mean([b["size_kb"] for b in category_benchmarks])

            results["by_category"][category] = {
                "avg_size_kb": round(avg_size, 2),
                "avg_parse_time_ms": round(avg_time, 2),
                "num_files_tested": len(category_benchmarks),
            }

            print(f"  • {category}: {round(avg_time, 2)}ms avg ({len(category_benchmarks)} files)")

    return results


def create_synthetic_10kb_contract() -> str:
    """Create a synthetic 10KB Solidity contract for controlled testing."""
    contract = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract SyntheticBenchmark {
    // State variables
    mapping(address => uint256) private balances;
    mapping(address => mapping(address => uint256)) private allowances;
    uint256 public totalSupply;
    address public owner;
    bool public paused;

    // Events
    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);
    event Paused(address account);
    event Unpaused(address account);

    // Modifiers
    modifier onlyOwner() {
        require(msg.sender == owner, "Not the owner");
        _;
    }

    modifier whenNotPaused() {
        require(!paused, "Contract is paused");
        _;
    }

"""

    # Add functions to reach approximately 10KB
    for i in range(30):
        contract += f"""
    function function{i}(uint256 amount, address recipient) public whenNotPaused returns (bool) {{
        require(recipient != address(0), "Invalid recipient");
        require(amount > 0, "Amount must be positive");
        require(balances[msg.sender] >= amount, "Insufficient balance");

        balances[msg.sender] -= amount;
        balances[recipient] += amount;

        emit Transfer(msg.sender, recipient, amount);

        // Additional logic to increase complexity
        if (amount > 1000) {{
            uint256 bonus = amount / 100;
            balances[recipient] += bonus;
            totalSupply += bonus;
        }}

        return true;
    }}
"""

    contract += "\n}"

    # Ensure it's approximately 10KB
    while len(contract.encode("utf-8")) < 10240:
        contract += "\n    // Padding comment to reach target size\n"

    return (
        contract[:10240].decode("utf-8", errors="ignore")
        if isinstance(contract[:10240], bytes)
        else contract[:10240]
    )


def main():
    """Run comprehensive performance benchmarks."""
    print("=" * 60)
    print("SOLIDITY PARSER PERFORMANCE BENCHMARK")
    print("=" * 60)

    # Test 1: Synthetic 10KB contract
    print("\n🧪 TEST 1: SYNTHETIC 10KB CONTRACT")
    print("-" * 40)

    parser = TreeSitterSolidityParser()
    synthetic_contract = create_synthetic_10kb_contract()
    synthetic_size = len(synthetic_contract.encode("utf-8"))

    print(f"Contract size: {synthetic_size} bytes ({round(synthetic_size / 1024, 2)}KB)")

    # Warm-up run
    parser.parse(synthetic_contract)

    # Actual benchmark
    benchmark = measure_parse_time(parser, synthetic_contract, iterations=50)

    print("\nParsing Performance:")
    print(f"  • Mean: {benchmark['mean']:.2f}ms")
    print(f"  • Median: {benchmark['median']:.2f}ms")
    print(f"  • Min: {benchmark['min']:.2f}ms")
    print(f"  • Max: {benchmark['max']:.2f}ms")
    print(f"  • StdDev: {benchmark['stdev']:.2f}ms")

    # Check against requirement
    meets_requirement = benchmark["mean"] < 70
    print(f"\n{'✅' if meets_requirement else '❌'} Requirement: <70ms for 10KB file")
    print(f"   Result: {benchmark['mean']:.2f}ms {'PASS' if meets_requirement else 'FAIL'}")

    # Test 2: Real OpenZeppelin contracts
    print("\n📁 TEST 2: REAL OPENZEPPELIN CONTRACTS")
    print("-" * 40)

    oz_results = benchmark_openzeppelin_files()

    if oz_results and "target_10kb_files" in oz_results:
        print("\n🎯 10KB FILE PERFORMANCE SUMMARY")
        print("=" * 60)

        if oz_results["target_10kb_files"]:
            parse_times = [f["parse_time_ms"] for f in oz_results["target_10kb_files"]]
            avg_time = statistics.mean(parse_times)

            print(f"Average parse time for ~10KB files: {avg_time:.2f}ms")
            print(f"All under 70ms: {'✅ YES' if all(t < 70 for t in parse_times) else '❌ NO'}")

            # Show individual results
            print("\nDetailed results:")
            for file_info in oz_results["target_10kb_files"]:
                status = "✅" if file_info["parse_time_ms"] < 70 else "❌"
                print(f"  {status} {file_info['file']}: {file_info['parse_time_ms']}ms")

    # Generate final report
    print("\n" + "=" * 60)
    print("FINAL BENCHMARK REPORT")
    print("=" * 60)

    report = {
        "synthetic_10kb": {
            "size_bytes": synthetic_size,
            "mean_parse_time_ms": round(benchmark["mean"], 2),
            "median_parse_time_ms": round(benchmark["median"], 2),
            "meets_requirement": meets_requirement,
        },
        "openzeppelin_results": oz_results,
        "conclusion": {
            "requirement": "<70ms for 10KB file",
            "synthetic_result": f"{benchmark['mean']:.2f}ms",
            "status": "PASS" if meets_requirement else "FAIL",
        },
    }

    # Save report
    report_path = Path("solidity_benchmark_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n📊 Detailed report saved to {report_path}")

    # Performance comparison
    if oz_results and "by_category" in oz_results:
        print("\n📈 PERFORMANCE BY FILE SIZE")
        print("-" * 40)
        for category, data in oz_results["by_category"].items():
            print(f"  • {category}: {data['avg_parse_time_ms']}ms")

    # Final verdict
    print("\n" + "=" * 60)
    if meets_requirement:
        print("✅ VALIDATION SUCCESSFUL!")
        print(f"   Solidity parser performance: {benchmark['mean']:.2f}ms < 70ms requirement")
    else:
        print("❌ VALIDATION FAILED")
        print(f"   Solidity parser performance: {benchmark['mean']:.2f}ms > 70ms requirement")

    return 0 if meets_requirement else 1


if __name__ == "__main__":
    sys.exit(main())
