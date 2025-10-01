"""Integration tests for Dart parser against real-world Flutter framework code.

This test suite validates the Dart parser against the Flutter framework repository,
ensuring high accuracy (>98% success rate) on production Dart code.

Tests are marked as slow and only run when RUN_CORPUS_TESTS=1 is set.
"""

import os
import random
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List

import pytest

from codeconcat.parser.language_parsers.tree_sitter_dart_parser import (
    TreeSitterDartParser,
)


class TestDartCorpus:
    """Test suite for validating Dart parser against real-world codebases."""

    def _find_dart_files(self, directory: Path) -> List[Path]:
        """Recursively find all .dart files in a directory.

        Args:
            directory: Root directory to search

        Returns:
            List of Path objects for .dart files
        """
        dart_files = []
        for root, dirs, files in os.walk(directory):
            # Skip common non-source directories
            dirs[:] = [
                d
                for d in dirs
                if d not in {".git", ".dart_tool", "build", "node_modules", ".idea", ".vscode"}
            ]

            for file in files:
                if file.endswith(".dart"):
                    dart_files.append(Path(root) / file)
        return dart_files

    def _batch_parse_files(
        self, files: List[Path], parser: TreeSitterDartParser
    ) -> Dict[str, any]:
        """Parse multiple files and collect statistics.

        Args:
            files: List of .dart files to parse
            parser: TreeSitterDartParser instance

        Returns:
            Dictionary with parsing statistics:
            - total: Total files attempted
            - success: Successfully parsed files
            - failed: Failed to parse files
            - errors: List of (filename, error) tuples
            - declarations_found: Total declarations extracted
            - files_with_declarations: Files containing at least one declaration
        """
        results = {
            "total": len(files),
            "success": 0,
            "failed": 0,
            "errors": [],
            "declarations_found": 0,
            "files_with_declarations": 0,
        }

        for file_path in files:
            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()

                result = parser.parse(content, str(file_path))

                if result and not result.error:
                    results["success"] += 1
                    decl_count = len(result.declarations)
                    results["declarations_found"] += decl_count
                    if decl_count > 0:
                        results["files_with_declarations"] += 1
                else:
                    results["failed"] += 1
                    error_msg = result.error if result else "No result returned"
                    results["errors"].append((str(file_path), error_msg))

            except Exception as e:
                results["failed"] += 1
                results["errors"].append((str(file_path), str(e)))

        return results

    def _clone_repo(self, repo_url: str, target_dir: Path) -> bool:
        """Clone a git repository to target directory.

        Args:
            repo_url: Git repository URL
            target_dir: Destination directory

        Returns:
            True if successful, False otherwise
        """
        try:
            subprocess.run(
                ["git", "clone", "--depth=1", repo_url, str(target_dir)],
                check=True,
                capture_output=True,
                timeout=600,  # 10 minute timeout for large repos
            )
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            print(f"Failed to clone {repo_url}: {e}")
            return False

    def test_small_dart_sample(self, tmp_path):
        """Test parser against a small manually-created Dart corpus."""
        parser = TreeSitterDartParser()

        # Create test corpus directory
        corpus_dir = tmp_path / "dart_corpus"
        corpus_dir.mkdir()

        # Sample 1: Flutter StatelessWidget
        (corpus_dir / "simple_widget.dart").write_text(
            """
import 'package:flutter/material.dart';

class SimpleWidget extends StatelessWidget {
  final String title;

  const SimpleWidget({Key? key, required this.title}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Text(title);
  }
}
"""
        )

        # Sample 2: StatefulWidget with lifecycle
        (corpus_dir / "counter_widget.dart").write_text(
            """
import 'package:flutter/material.dart';

class CounterWidget extends StatefulWidget {
  @override
  State<CounterWidget> createState() => _CounterWidgetState();
}

class _CounterWidgetState extends State<CounterWidget> {
  int _counter = 0;

  @override
  void initState() {
    super.initState();
  }

  @override
  void dispose() {
    super.dispose();
  }

  void _increment() {
    setState(() => _counter++);
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text('Count: $_counter'),
        ElevatedButton(onPressed: _increment, child: Text('+')),
      ],
    );
  }
}
"""
        )

        # Sample 3: Async patterns
        (corpus_dir / "data_service.dart").write_text(
            """
import 'dart:async';

abstract class DataService {
  Future<List<String>> fetchItems();
  Stream<int> watchCount();
}

class ApiService implements DataService {
  @override
  Future<List<String>> fetchItems() async {
    await Future.delayed(Duration(seconds: 1));
    return ['item1', 'item2', 'item3'];
  }

  @override
  Stream<int> watchCount() async* {
    for (int i = 0; i < 10; i++) {
      await Future.delayed(Duration(milliseconds: 100));
      yield i;
    }
  }
}
"""
        )

        # Find and parse all files
        files = self._find_dart_files(corpus_dir)
        assert len(files) == 3

        results = self._batch_parse_files(files, parser)

        # Assertions
        assert results["total"] == 3
        assert results["success"] == 3
        assert results["failed"] == 0
        assert (
            results["declarations_found"] >= 8
        )  # At least: SimpleWidget, build, CounterWidget, _CounterWidgetState, initState, dispose, build, DataService, ApiService, fetchItems, watchCount

        # Calculate success rate
        success_rate = (results["success"] / results["total"]) * 100
        assert success_rate == 100.0

    @pytest.mark.slow
    @pytest.mark.skipif(
        not os.environ.get("RUN_CORPUS_TESTS"),
        reason="Corpus tests disabled (set RUN_CORPUS_TESTS=1 to enable)",
    )
    def test_flutter_framework_repository(self, tmp_path):
        """Test parser against the Flutter framework repository.

        This test is marked as slow and only runs when RUN_CORPUS_TESTS=1 is set.
        It validates parser accuracy against production Flutter code.

        Target: >98% success rate on Flutter framework source files.
        """
        parser = TreeSitterDartParser()

        # Clone Flutter repository
        flutter_dir = tmp_path / "flutter"
        repo_url = "https://github.com/flutter/flutter.git"

        if not self._clone_repo(repo_url, flutter_dir):
            pytest.skip("Failed to clone Flutter repository")

        # Focus on Flutter framework source directories
        target_dirs = [
            flutter_dir / "packages" / "flutter" / "lib" / "src" / "widgets",
            flutter_dir / "packages" / "flutter" / "lib" / "src" / "material",
            flutter_dir / "packages" / "flutter" / "lib" / "src" / "cupertino",
        ]

        # Find all Dart files in target directories
        files = []
        for target_dir in target_dirs:
            if target_dir.exists():
                files.extend(self._find_dart_files(target_dir))

        # Flutter is large, sample if needed
        if len(files) > 1000:
            random.seed(42)  # Reproducible sampling
            files = random.sample(files, 1000)

        assert len(files) > 0, "No Dart files found in Flutter repository"

        # Parse all files
        results = self._batch_parse_files(files, parser)

        # Calculate success rate
        success_rate = (results["success"] / results["total"]) * 100

        # Report results
        print(f"\n=== Flutter Framework Corpus Test Results ===")
        print(f"Total files: {results['total']}")
        print(f"Successfully parsed: {results['success']}")
        print(f"Failed to parse: {results['failed']}")
        print(f"Success rate: {success_rate:.2f}%")
        print(f"Declarations found: {results['declarations_found']}")
        print(f"Files with declarations: {results['files_with_declarations']}")

        if results["errors"]:
            print(f"\n=== First 10 Errors ===")
            for file_path, error in results["errors"][:10]:
                # Print relative path for readability
                try:
                    rel_path = Path(file_path).relative_to(flutter_dir)
                    print(f"  {rel_path}: {error[:100]}")
                except ValueError:
                    print(f"  {Path(file_path).name}: {error[:100]}")

        # Assert >98% success rate (allowing for some edge cases)
        assert (
            success_rate >= 98.0
        ), f"Success rate {success_rate:.2f}% is below 98% threshold"

    @pytest.mark.slow
    @pytest.mark.skipif(
        not os.environ.get("RUN_CORPUS_TESTS"),
        reason="Corpus tests disabled (set RUN_CORPUS_TESTS=1 to enable)",
    )
    def test_flutter_dart_ui_package(self, tmp_path):
        """Test parser against dart:ui bindings in Flutter.

        This tests lower-level Dart code that interacts with the Flutter engine.
        """
        parser = TreeSitterDartParser()

        # Clone Flutter repository
        flutter_dir = tmp_path / "flutter"
        repo_url = "https://github.com/flutter/flutter.git"

        if not self._clone_repo(repo_url, flutter_dir):
            pytest.skip("Failed to clone Flutter repository")

        # Target dart:ui bindings
        ui_dir = flutter_dir / "packages" / "flutter" / "lib" / "src" / "painting"

        if not ui_dir.exists():
            pytest.skip("Flutter painting directory not found")

        files = self._find_dart_files(ui_dir)

        # Sample if too many files
        if len(files) > 500:
            random.seed(42)
            files = random.sample(files, 500)

        assert len(files) > 0, "No Dart files found in painting directory"

        # Parse all files
        results = self._batch_parse_files(files, parser)

        # Calculate success rate
        success_rate = (results["success"] / results["total"]) * 100

        # Report results
        print(f"\n=== Flutter Painting Package Test Results ===")
        print(f"Total files: {results['total']}")
        print(f"Successfully parsed: {results['success']}")
        print(f"Failed to parse: {results['failed']}")
        print(f"Success rate: {success_rate:.2f}%")
        print(f"Declarations found: {results['declarations_found']}")

        if results["errors"]:
            print(f"\n=== First 5 Errors ===")
            for file_path, error in results["errors"][:5]:
                try:
                    rel_path = Path(file_path).relative_to(flutter_dir)
                    print(f"  {rel_path}: {error[:100]}")
                except ValueError:
                    print(f"  {Path(file_path).name}: {error[:100]}")

        # Assert >98% success rate
        assert (
            success_rate >= 98.0
        ), f"Success rate {success_rate:.2f}% is below 98% threshold"

    def test_parse_dart_packages(self, tmp_path):
        """Test parsing files with package imports."""
        parser = TreeSitterDartParser()

        # Create test with various package imports
        test_file = tmp_path / "package_imports.dart"
        test_file.write_text(
            """
import 'package:flutter/material.dart';
import 'package:flutter/cupertino.dart';
import 'package:http/http.dart' as http;
import 'package:provider/provider.dart';

import 'dart:async';
import 'dart:convert';

import 'models/user.dart';
import '../utils/helpers.dart';

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: Scaffold(
        body: Center(child: Text('Hello')),
      ),
    );
  }
}
"""
        )

        files = [test_file]
        results = self._batch_parse_files(files, parser)

        assert results["success"] == 1
        assert results["failed"] == 0
        assert results["declarations_found"] >= 1
