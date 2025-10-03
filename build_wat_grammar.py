#!/usr/bin/env python
"""Build tree-sitter-wasm WAT grammar for CodeConCat."""

from pathlib import Path

from tree_sitter import Language


def build_wat_grammar():
    """Build and install the tree-sitter-wasm WAT grammar."""

    # Paths
    repo_path = Path("/tmp/tree-sitter-wasm")
    wat_path = repo_path / "wat"

    # Clone if not exists
    if not repo_path.exists():
        print("Cloning tree-sitter-wasm repository...")
        import subprocess

        subprocess.run(
            ["git", "clone", "https://github.com/wasm-lsp/tree-sitter-wasm.git", str(repo_path)],
            check=True,
        )

    # Build the library
    output_path = Path.cwd() / "codeconcat" / "parser" / "grammars" / "tree-sitter-wat.so"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Building WAT grammar from {wat_path}...")
    Language.build_library(str(output_path), [str(wat_path)])

    print(f"WAT grammar built successfully at {output_path}")
    return output_path


if __name__ == "__main__":
    build_wat_grammar()
