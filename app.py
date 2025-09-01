from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from codeconcat.config.config_builder import ConfigBuilder
from codeconcat.main import run_codeconcat_in_memory

app = FastAPI(
    title="CodeConCat API",
    description="API for CodeConCat - An LLM-friendly code parser, aggregator and doc extractor",
    version="1.0.0",
)


class CodeConcatRequest(BaseModel):
    target_path: str
    format: str = "markdown"
    github_url: Optional[str] = None
    github_token: Optional[str] = None
    github_ref: Optional[str] = None
    extract_docs: bool = False
    merge_docs: bool = False
    include_paths: List[str] = []
    exclude_paths: List[str] = []
    include_languages: List[str] = []
    exclude_languages: List[str] = []
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
        cli_args = request.dict()
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
        "version": "1.0.0",
        "description": "API for code concatenation and documentation extraction",
    }
