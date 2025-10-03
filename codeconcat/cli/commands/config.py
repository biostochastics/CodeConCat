"""Configuration management commands for the CodeConCat CLI."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any, NamedTuple
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import urlopen

import typer
import yaml  # type: ignore[import-untyped]
from rich.console import Console
from rich.table import Table

from codeconcat.ai.base import AIProviderConfig, AIProviderType
from codeconcat.ai.providers.local_server_provider import LocalServerProvider
from codeconcat.cli.config import get_state

app = typer.Typer(help="Interactive helpers for configuring CodeConCat")
console = Console()


class LocalProviderPreset(NamedTuple):
    """Represents a selectable local server preset."""

    label: str
    key: str
    description: str
    provider_type: AIProviderType
    candidates: list[str]


SERVER_CHOICES: list[LocalProviderPreset] = [
    LocalProviderPreset(
        "vLLM (http://localhost:8000)",
        "vllm",
        "Fast OpenAI-compatible server for large models",
        AIProviderType.VLLM,
        [
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ],
    ),
    LocalProviderPreset(
        "LM Studio (http://localhost:1234)",
        "lmstudio",
        "Desktop UI with local REST server",
        AIProviderType.LMSTUDIO,
        [
            "http://localhost:1234",
            "http://127.0.0.1:1234",
        ],
    ),
    LocalProviderPreset(
        "llama.cpp server (http://localhost:8080)",
        "llamacpp_server",
        "llama.cpp built-in HTTP server",
        AIProviderType.LLAMACPP_SERVER,
        [
            "http://localhost:8080",
            "http://127.0.0.1:8080",
        ],
    ),
    LocalProviderPreset(
        "Generic OpenAI-compatible server",
        "local_server",
        "Other runtimes (TGI, LocalAI, FastChat, etc.)",
        AIProviderType.LOCAL_SERVER,
        [
            "http://localhost:8000",
            "http://127.0.0.1:8000",
            "http://localhost:3000",
        ],
    ),
]

ENV_VAR_BY_PROVIDER = {
    "local_server": "LOCAL_LLM_API_KEY",
    "vllm": "VLLM_API_KEY",
    "lmstudio": "LMSTUDIO_API_KEY",
    "llamacpp_server": "LLAMACPP_SERVER_API_KEY",
}


def _load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}

    try:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
            return data if isinstance(data, dict) else {}
    except Exception as exc:  # pragma: no cover - I/O errors reported to user
        console.print(f"[red]Failed to read {path}: {exc}[/red]")
        return {}


def _save_config(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(data, handle, sort_keys=False)


def _choose_provider(existing_provider: str | None) -> LocalProviderPreset:
    console.print("\n[bold]Local LLM Presets[/bold]")
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("#", style="bold")
    table.add_column("Provider")
    table.add_column("Notes")

    default_index = 1
    for idx, choice in enumerate(SERVER_CHOICES, start=1):
        label, key, description, _ptype, _candidates = choice
        if existing_provider and existing_provider == key:
            default_index = idx
        table.add_row(str(idx), label, description)

    console.print(table)

    prompt = typer.prompt(
        "Select your local server",
        default=str(default_index),
    )

    try:
        selection = int(prompt)
        if 1 <= selection <= len(SERVER_CHOICES):
            return SERVER_CHOICES[selection - 1]
    except ValueError:
        pass

    # Fallback to first option if parsing failed
    return SERVER_CHOICES[default_index - 1]


def _probe_plain_http(url: str, timeout: float = 1.5) -> bool:
    # Validate URL is localhost to prevent SSRF attacks
    parsed = urlparse(url)
    if parsed.hostname not in ["localhost", "127.0.0.1", "::1", "0.0.0.0"]:
        # Refuse to probe non-localhost URLs for security
        return False

    try:
        with urlopen(url, timeout=timeout) as response:  # nosec B310 - validated localhost only
            return 200 <= response.status < 500  # type: ignore[no-any-return]
    except HTTPError as exc:
        return exc.code in {401, 403, 404}
    except URLError:
        return False


async def _validate_local_server(
    provider_type: AIProviderType,
    api_base: str,
    api_key: str | None,
) -> tuple[bool, dict[str, Any], str | None]:
    config = AIProviderConfig(
        provider_type=provider_type,
        api_base=api_base,
        api_key=api_key or "",
        model="",
        cache_enabled=False,
        max_tokens=32,
    )
    provider = LocalServerProvider(config)
    try:
        success = await provider.validate_connection()
        info = await provider.get_model_info() if success else {}
        return success, info, provider.last_error
    finally:
        await provider.close()


def _auto_detect_base(
    provider: LocalProviderPreset,
    existing_base: str | None,
    api_key: str | None,
) -> tuple[str | None, dict[str, Any], str | None]:
    label, key, _desc, provider_type, candidates = provider
    candidate_urls = []
    for candidate in [existing_base, *candidates]:
        if not candidate:
            continue
        normalized = candidate.rstrip("/")
        if normalized not in candidate_urls:
            candidate_urls.append(normalized)

    for base in candidate_urls:
        console.print(f"[cyan]• Checking {base}[/cyan]")
        # Quick TCP check before spinning up aiohttp
        if not _probe_plain_http(f"{base}/health") and not _probe_plain_http(f"{base}/v1/models"):
            continue
        success, info, error = asyncio.run(_validate_local_server(provider_type, base, api_key))
        if success:
            console.print(f"  [green]✓ Connected to {base}[/green]")
            return base, info, None
        if error:
            console.print(f"  [yellow]{error}[/yellow]")
    return None, {}, None


def _prompt_for_api_key(provider_key: str, existing_key: str | None) -> str:
    env_var = ENV_VAR_BY_PROVIDER.get(provider_key)
    env_value = os.getenv(env_var) if env_var else None
    default_value = existing_key or env_value or ""
    prompt_text = "API key (leave blank if not required)"
    return typer.prompt(prompt_text, default=default_value, hide_input=True)  # type: ignore[no-any-return]


def _prompt_for_base_url(
    provider: LocalProviderPreset,
    auto_detected: str | None,
    existing_base: str | None,
    api_key: str | None,
) -> tuple[str, dict[str, Any]]:
    label, key, _description, provider_type, candidates = provider
    default_base = auto_detected or existing_base or candidates[0]

    while True:
        base = typer.prompt("Server URL", default=default_base).rstrip("/")
        success, info, error = asyncio.run(_validate_local_server(provider_type, base, api_key))
        if success:
            console.print(f"[green]Validated {label} at {base}[/green]")
            return base, info

        console.print(
            f"[yellow]Could not validate {label} at {base}: {error or 'unknown error'}[/yellow]"
        )
        if not typer.confirm("Keep this URL anyway?", default=False):
            # Reset to first candidate instead of reusing failed value
            default_base = candidates[0]
            continue
        return base, {}


def _prompt_for_model(
    available_models: list[str],
    existing_model: str | None,
) -> str:
    if not available_models:
        default_model = existing_model or "local-model"
        return typer.prompt("Model name", default=default_model).strip()  # type: ignore[no-any-return]

    limited_models = available_models[:10]
    if len(available_models) > len(limited_models):
        console.print(
            f"Showing first {len(limited_models)} models out of {len(available_models)} detected."
        )

    for idx, model_name in enumerate(limited_models, start=1):
        console.print(f"  {idx}. {model_name}")

    default_model = existing_model or limited_models[0]
    default_prompt = (
        str(limited_models.index(existing_model) + 1)
        if existing_model and existing_model in limited_models
        else default_model
    )

    user_input = typer.prompt(
        "Select model (number or name)",
        default=default_prompt,
    ).strip()

    if user_input.isdigit():
        selection = int(user_input)
        if 1 <= selection <= len(limited_models):
            return limited_models[selection - 1]

    return user_input or default_model


@app.command("local-llm")
def configure_local_llm() -> None:
    """Interactive wizard to configure a local LLM provider."""

    state = get_state()
    config_path = (state.config_path or Path.cwd() / ".codeconcat.yml").resolve()
    config_data = _load_config(config_path)

    existing_provider = str(config_data.get("ai_provider", "")) or None
    existing_model = str(config_data.get("ai_model", "")) or None
    existing_base = str(config_data.get("ai_api_base", "")) or None
    existing_key = str(config_data.get("ai_api_key", "")) or None

    console.print("[bold cyan]\nCodeConCat Local LLM Configuration Wizard[/bold cyan]")
    console.print("This will update:")
    console.print(f"  • [green]{config_path}[/green]\n")

    choice = _choose_provider(existing_provider)
    label, provider_key, description, provider_type, _candidates = choice

    console.print(f"\nConfiguring [bold]{label}[/bold] — {description}")

    api_key = _prompt_for_api_key(provider_key, existing_key)
    auto_base, info, _ = _auto_detect_base(choice, existing_base, api_key)
    api_base, info = _prompt_for_base_url(choice, auto_base, existing_base, api_key)

    models = info.get("available_models", []) if isinstance(info, dict) else []
    model = _prompt_for_model(models, existing_model)

    config_data["enable_ai_summary"] = True
    config_data["ai_provider"] = provider_key
    config_data["ai_model"] = model
    config_data["ai_api_base"] = api_base
    config_data["ai_api_key"] = api_key

    _save_config(config_path, config_data)

    console.print("\n[green]Configuration saved.[/green]")
    console.print("Run [bold]codeconcat run --ai-summary[/bold] to use your local model.")
