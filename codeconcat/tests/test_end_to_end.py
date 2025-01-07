import os

import pytest

from codeconcat.base_types import CodeConCatConfig
from codeconcat.main import run_codeconcat


@pytest.fixture
def sample_dir(tmp_path):
    py_file = tmp_path / "script.py"
    py_file.write_text("def foo(): pass\n")
    doc_file = tmp_path / "README.md"
    doc_file.write_text("# This is documentation.")
    return tmp_path


def test_run_codeconcat(sample_dir):
    config = CodeConCatConfig(
        target_path=str(sample_dir),
        docs=True,
        merge_docs=True,
        format="markdown",
        output=str(sample_dir / "output.md"),
    )
    run_codeconcat(config)

    output_path = sample_dir / "output.md"
    assert output_path.exists()
    content = output_path.read_text()
    assert "def foo" in content
    assert "# This is documentation." in content
