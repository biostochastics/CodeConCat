from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from codeconcat.config.config_builder import ConfigBuilder
from codeconcat.main import run_codeconcat_in_memory
from codeconcat.version import __version__

app = FastAPI(
    title="CodeConCat API",
    description="API for CodeConCat - An LLM-friendly code parser, aggregator and doc extractor",
    version=__version__,
)


class CodeConcatRequest(BaseModel):
    """
    Represents a request to concatenate code from various sources with specific formatting and filtering options.

    Attributes:
        target_path: The target path where the output should be saved.
        format: The format for the output; defaults to "markdown".
        github_url: URL of the GitHub repository to pull code from, if necessary.
        github_token: Token for authenticating with GitHub, if required.
        github_ref: Specific reference for checking out a GitHub branch or tag.
        extract_docs: Flag to determine if documentation should be extracted from source files.
        merge_docs: Flag for determining if extracted documentation should be merged.
        include_paths: List of paths to include in the code concatenation.
        exclude_paths: List of paths to exclude from the code concatenation.
        include_languages: Languages to include in the code concatenation.
        exclude_languages: Languages to exclude from the code concatenation.
        disable_tree: Flag to prevent tree representation in the output.
        disable_annotations: Flag to disable annotations in the output.
        disable_copy: Flag to disable copy functionality; default is True for API usage.
        disable_symbols: Flag to disable symbols in the output.
        disable_ai_context: Flag to disable AI context in processing.
        max_workers: Maximum number of workers for processing; defaults to 4.
        output_preset: Preset for the output format; defaults to "medium".
    """

    target_path: str
    format: str = "markdown"
    github_url: str | None = None
    github_token: str | None = None
    github_ref: str | None = None
    extract_docs: bool = False
    merge_docs: bool = False
    include_paths: list[str] = []
    exclude_paths: list[str] = []
    include_languages: list[str] = []
    exclude_languages: list[str] = []
    disable_tree: bool = False
    disable_annotations: bool = False
    disable_copy: bool = True  # Default to True for API usage
    disable_symbols: bool = False
    disable_ai_context: bool = False
    max_workers: int = 4
    output_preset: str = "medium"


@app.post("/concat")
async def concat_code(request: CodeConcatRequest):
    """
    Process code files and return concatenated output
    """
    try:
        cli_args = request.model_dump()
        config_builder = ConfigBuilder()
        config = (
            config_builder.with_defaults()
            .with_preset(request.output_preset)
            .with_cli_args(cli_args)
            .build()
        )
        output = run_codeconcat_in_memory(config)
        return {"output": output}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/")
async def root():
    """
    Root endpoint returning basic API info
    """
    return {
        "name": "CodeConCat API",
        "version": __version__,
        "description": "API for code concatenation and documentation extraction",
    }
