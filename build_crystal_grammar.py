#!/usr/bin/env python
"""Build tree-sitter-crystal grammar for CodeConCat."""

from pathlib import Path

from tree_sitter import Language


def build_crystal_grammar():
    """Build and install the tree-sitter-crystal grammar."""

    # Paths
    repo_path = Path("/tmp/tree-sitter-crystal")

    # Clone if not exists
    if not repo_path.exists():
        print("Cloning tree-sitter-crystal repository...")
        import subprocess

        subprocess.run(
            [
                "git",
                "clone",
                "https://github.com/crystal-lang-tools/tree-sitter-crystal.git",
                str(repo_path),
            ],
            check=True,
        )

    # Build the library
    output_path = Path.cwd() / "codeconcat" / "parser" / "grammars" / "tree-sitter-crystal.so"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Building Crystal grammar from {repo_path}...")
    Language.build_library(str(output_path), [str(repo_path)])

    print(f"Crystal grammar built successfully at {output_path}")
    return output_path


if __name__ == "__main__":
    build_crystal_grammar()
