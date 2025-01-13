import os
import re
import setuptools


def get_version():
    version_file = os.path.join(os.path.dirname(__file__), "codeconcat", "version.py")
    with open(version_file, "r", encoding="utf-8") as f:
        content = f.read()
        match = re.search(r'__version__\s*=\s*"([^"]+)"', content)
        if match:
            return match.group(1)
    return "0.0.0"


setuptools.setup(
    name="codeconcat",
    version=get_version(),
    author="Sergey Kornilov",
    author_email="sergey.kornilov@biostochastics.com",
    description="An LLM-friendly code parser, aggregator and doc extractor",
    packages=setuptools.find_packages(),
    install_requires=[
        "pyyaml>=5.0",
        "pyperclip>=1.8.0",
        "tiktoken>=0.5.1",
        "halo>=0.0.31",
    ],
    python_requires=">=3.8",
    entry_points={"console_scripts": ["codeconcat=codeconcat.main:cli_entry_point"]},
)
