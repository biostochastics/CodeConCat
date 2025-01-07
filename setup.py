import os
import re
from setuptools import setup, find_packages


def get_version():
    """
    Extracts the CodeConCat version from codeconcat/version.py
    """
    version_file = os.path.join(os.path.dirname(__file__), "codeconcat", "version.py")
    with open(version_file, "r", encoding="utf-8") as f:
        content = f.read()
        match = re.search(r'__version__\s*=\s*"([^"]+)"', content)
        if match:
            return match.group(1)
    return "0.0.0"


def get_long_description():
    try:
        with open("README.md", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


setup(
    name="codeconcat",
    version=get_version(),
    author="Sergey Kornilov",
    author_email="sergey.kornilov@biostochastics.com",
    description="An LLM-friendly code parser, aggregator and doc extractor",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        "pyyaml>=5.0",
        "pyperclip>=1.8.0",
    ],
    python_requires=">=3.8",
    entry_points={"console_scripts": ["codeconcat=codeconcat.main:cli_entry_point"]},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    keywords="llm code parser documentation",
    project_urls={
        "Source": "https://github.com/biostochastics/codeconcat",
    },
)
