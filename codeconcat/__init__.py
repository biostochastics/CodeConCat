"""
CodeConCat - An LLM-friendly code parser, aggregator and doc extractor.
"""

from .main import run_codeconcat, run_codeconcat_in_memory
from .base_types import CodeConCatConfig, AnnotatedFileData, ParsedDocData
from .version import __version__

__all__ = [
    "run_codeconcat",
    "run_codeconcat_in_memory",
    "CodeConCatConfig",
    "AnnotatedFileData", 
    "ParsedDocData",
    "__version__",
]