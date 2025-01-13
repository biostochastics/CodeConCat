from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from codeconcat import run_codeconcat_in_memory, CodeConCatConfig

app = FastAPI(
    title="CodeConCat API",
    description="API for CodeConCat - An LLM-friendly code parser, aggregator and doc extractor",
    version="1.0.0"
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

@app.post("/concat")
async def concat_code(request: CodeConcatRequest):
    """
    Process code files and return concatenated output
    """
    try:
        config = CodeConCatConfig(
            target_path=request.target_path,
            format=request.format,
            github_url=request.github_url,
            github_token=request.github_token,
            github_ref=request.github_ref,
            extract_docs=request.extract_docs,
            merge_docs=request.merge_docs,
            include_paths=request.include_paths,
            exclude_paths=request.exclude_paths,
            include_languages=request.include_languages,
            exclude_languages=request.exclude_languages,
            disable_tree=request.disable_tree,
            disable_annotations=request.disable_annotations,
            disable_copy=request.disable_copy,
            disable_symbols=request.disable_symbols,
            disable_ai_context=request.disable_ai_context,
            max_workers=request.max_workers
        )
        output = run_codeconcat_in_memory(config)
        return {"output": output}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """
    Root endpoint returning basic API info
    """
    return {
        "name": "CodeConCat API",
        "version": "1.0.0",
        "description": "API for code concatenation and documentation extraction"
    }
