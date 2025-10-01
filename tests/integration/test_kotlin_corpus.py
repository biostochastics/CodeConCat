"""Integration tests for Kotlin parser against real-world code repositories."""

import os
import tempfile
from pathlib import Path
from typing import List, Dict, Tuple
import subprocess

import pytest

from codeconcat.parser.language_parsers.tree_sitter_kotlin_parser import (
    TreeSitterKotlinParser,
)


class TestKotlinCorpus:
    """Test suite for validating Kotlin parser against real-world codebases."""

    def _find_kotlin_files(self, directory: Path) -> List[Path]:
        """Recursively find all .kt and .kts files in a directory."""
        kotlin_files = []
        for root, dirs, files in os.walk(directory):
            # Skip common non-source directories
            dirs[:] = [d for d in dirs if d not in {'.git', '.gradle', 'build', 'node_modules', '.idea'}]

            for file in files:
                if file.endswith(('.kt', '.kts')):
                    kotlin_files.append(Path(root) / file)
        return kotlin_files

    def _batch_parse_files(
        self, files: List[Path], parser: TreeSitterKotlinParser
    ) -> Dict[str, any]:
        """Parse multiple files and collect statistics.

        Returns:
            Dictionary with:
            - total: Total files attempted
            - success: Successfully parsed files
            - failed: Failed to parse files
            - errors: List of (filename, error) tuples
            - declarations_found: Total declarations extracted
        """
        results = {
            'total': len(files),
            'success': 0,
            'failed': 0,
            'errors': [],
            'declarations_found': 0,
            'files_with_declarations': 0,
        }

        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()

                result = parser.parse(content, str(file_path))

                if result and not result.error:
                    results['success'] += 1
                    decl_count = len(result.declarations)
                    results['declarations_found'] += decl_count
                    if decl_count > 0:
                        results['files_with_declarations'] += 1
                else:
                    results['failed'] += 1
                    error_msg = result.error if result else "No result returned"
                    results['errors'].append((str(file_path), error_msg))

            except Exception as e:
                results['failed'] += 1
                results['errors'].append((str(file_path), str(e)))

        return results

    def _clone_repo(self, repo_url: str, target_dir: Path) -> bool:
        """Clone a git repository to target directory.

        Returns:
            True if successful, False otherwise
        """
        try:
            subprocess.run(
                ['git', 'clone', '--depth=1', repo_url, str(target_dir)],
                check=True,
                capture_output=True,
                timeout=300  # 5 minute timeout
            )
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            print(f"Failed to clone {repo_url}: {e}")
            return False

    def test_small_kotlin_sample(self, tmp_path):
        """Test parser against a small manually-created Kotlin corpus."""
        parser = TreeSitterKotlinParser()

        # Create test corpus directory
        corpus_dir = tmp_path / "kotlin_corpus"
        corpus_dir.mkdir()

        # Sample 1: Basic application
        (corpus_dir / "App.kt").write_text("""
package com.example

fun main() {
    println("Hello, Kotlin!")
}

class Application {
    fun run() {
        println("Running...")
    }
}
""")

        # Sample 2: Data classes and extensions
        (corpus_dir / "Models.kt").write_text("""
data class User(val id: Int, val name: String)

fun User.greet(): String = "Hello, $name!"

sealed class Result<out T> {
    data class Success<T>(val data: T) : Result<T>()
    data class Error(val message: String) : Result<Nothing>()
}
""")

        # Sample 3: Suspend functions
        (corpus_dir / "Repository.kt").write_text("""
interface Repository {
    suspend fun fetchData(): String
}

class NetworkRepository : Repository {
    override suspend fun fetchData(): String {
        // Simulate network call
        return "data"
    }
}
""")

        # Find and parse all files
        files = self._find_kotlin_files(corpus_dir)
        assert len(files) == 3

        results = self._batch_parse_files(files, parser)

        # Assertions
        assert results['total'] == 3
        assert results['success'] == 3
        assert results['failed'] == 0
        assert results['declarations_found'] >= 6  # At least: main, Application, User, greet, Result, Repository, NetworkRepository

        # Calculate success rate
        success_rate = (results['success'] / results['total']) * 100
        assert success_rate == 100.0

    @pytest.mark.slow
    @pytest.mark.skipif(
        not os.environ.get('RUN_CORPUS_TESTS'),
        reason="Corpus tests disabled (set RUN_CORPUS_TESTS=1 to enable)"
    )
    def test_ktor_repository(self, tmp_path):
        """Test parser against the Ktor framework repository.

        This test is marked as slow and only runs when RUN_CORPUS_TESTS=1 is set.
        """
        parser = TreeSitterKotlinParser()

        # Clone Ktor repository
        ktor_dir = tmp_path / "ktor"
        repo_url = "https://github.com/ktorio/ktor.git"

        if not self._clone_repo(repo_url, ktor_dir):
            pytest.skip("Failed to clone Ktor repository")

        # Find all Kotlin files
        files = self._find_kotlin_files(ktor_dir)

        # Ktor is a large project, should have hundreds of Kotlin files
        assert len(files) > 100, f"Expected >100 Kotlin files in Ktor, found {len(files)}"

        # Parse all files
        results = self._batch_parse_files(files, parser)

        # Calculate success rate
        success_rate = (results['success'] / results['total']) * 100

        # Report results
        print(f"\n=== Ktor Corpus Test Results ===")
        print(f"Total files: {results['total']}")
        print(f"Successfully parsed: {results['success']}")
        print(f"Failed to parse: {results['failed']}")
        print(f"Success rate: {success_rate:.2f}%")
        print(f"Declarations found: {results['declarations_found']}")
        print(f"Files with declarations: {results['files_with_declarations']}")

        if results['errors']:
            print(f"\n=== First 10 Errors ===")
            for file_path, error in results['errors'][:10]:
                print(f"  {file_path}: {error}")

        # Assert >98% success rate (allowing for some edge cases)
        assert success_rate >= 98.0, f"Success rate {success_rate:.2f}% is below 98% threshold"

    @pytest.mark.slow
    @pytest.mark.skipif(
        not os.environ.get('RUN_CORPUS_TESTS'),
        reason="Corpus tests disabled (set RUN_CORPUS_TESTS=1 to enable)"
    )
    def test_aosp_kotlin_sample(self, tmp_path):
        """Test parser against a sample of AOSP Kotlin files.

        AOSP is massive, so this tests a specific Kotlin-heavy component.
        This test is marked as slow and only runs when RUN_CORPUS_TESTS=1 is set.
        """
        parser = TreeSitterKotlinParser()

        # Clone a Kotlin-heavy AOSP component (e.g., Android Studio tools)
        # Using the androidx repository which has significant Kotlin code
        androidx_dir = tmp_path / "androidx"
        repo_url = "https://github.com/androidx/androidx.git"

        if not self._clone_repo(repo_url, androidx_dir):
            pytest.skip("Failed to clone androidx repository")

        # Find all Kotlin files
        files = self._find_kotlin_files(androidx_dir)

        # Sample the files if there are too many (>1000 files)
        if len(files) > 1000:
            import random
            random.seed(42)  # Reproducible sampling
            files = random.sample(files, 1000)

        assert len(files) > 0, "No Kotlin files found in androidx repository"

        # Parse all files
        results = self._batch_parse_files(files, parser)

        # Calculate success rate
        success_rate = (results['success'] / results['total']) * 100

        # Report results
        print(f"\n=== AndroidX Corpus Test Results ===")
        print(f"Total files: {results['total']}")
        print(f"Successfully parsed: {results['success']}")
        print(f"Failed to parse: {results['failed']}")
        print(f"Success rate: {success_rate:.2f}%")
        print(f"Declarations found: {results['declarations_found']}")
        print(f"Files with declarations: {results['files_with_declarations']}")

        if results['errors']:
            print(f"\n=== First 10 Errors ===")
            for file_path, error in results['errors'][:10]:
                print(f"  {file_path}: {error}")

        # Assert >98% success rate
        assert success_rate >= 98.0, f"Success rate {success_rate:.2f}% is below 98% threshold"

    def test_parse_kotlin_script_files(self, tmp_path):
        """Test parsing .kts (Kotlin script) files."""
        parser = TreeSitterKotlinParser()

        # Create test .kts file
        script_file = tmp_path / "build.gradle.kts"
        script_file.write_text("""
plugins {
    kotlin("jvm") version "1.9.0"
}

repositories {
    mavenCentral()
}

dependencies {
    implementation("org.jetbrains.kotlin:kotlin-stdlib")
}

tasks.withType<org.jetbrains.kotlin.gradle.tasks.KotlinCompile> {
    kotlinOptions {
        jvmTarget = "11"
    }
}
""")

        files = self._find_kotlin_files(tmp_path)
        assert len(files) == 1
        assert files[0].suffix == '.kts'

        results = self._batch_parse_files(files, parser)

        # Script files might not have traditional declarations, but should parse
        assert results['success'] == 1
        assert results['failed'] == 0
