"""CLI commands for managing API keys."""

import asyncio

import typer
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table

from codeconcat.ai.key_manager import APIKeyManager, KeyStorage, setup_api_keys

app = typer.Typer(help="Manage API keys for AI providers")
console = Console()


def _get_storage_method() -> KeyStorage:
    """Get the preferred storage method based on environment."""
    # Prefer encrypted file for security
    return KeyStorage.ENCRYPTED_FILE


@app.command("setup")
def setup_keys(
    interactive: bool = typer.Option(
        True, "--interactive/--no-interactive", "-i/-n", help="Interactive setup mode"
    ),
    storage: str = typer.Option(
        "encrypted", "--storage", "-s", help="Storage method: encrypted, keyring, or env"
    ),
):
    """Set up API keys for AI providers."""
    console.print("\n[bold cyan]🔑 API Key Setup[/bold cyan]")
    console.print("=" * 50)

    # Map storage string to enum
    storage_map = {
        "encrypted": KeyStorage.ENCRYPTED_FILE,
        "keyring": KeyStorage.KEYRING,
        "env": KeyStorage.ENVIRONMENT,
    }

    if storage not in storage_map:
        console.print(f"[red]❌ Invalid storage method: {storage}[/red]")
        raise typer.Exit(1)

    if storage == "env":
        console.print("[yellow]⚠️  Environment storage is read-only.[/yellow]")
        console.print("Set API keys as environment variables:")
        console.print("  export OPENAI_API_KEY=sk-...")
        console.print("  export ANTHROPIC_API_KEY=sk-ant-...")
        console.print("  export OPENROUTER_API_KEY=sk-or-...")
        raise typer.Exit(0)

    # Run the async setup
    try:
        configured = asyncio.run(setup_api_keys(interactive=interactive))

        if configured:
            console.print(f"\n[green]✅ Configured {len(configured)} API key(s)[/green]")
        else:
            console.print("[yellow]⚠️  No API keys configured[/yellow]")
    except KeyboardInterrupt:
        console.print("\n[yellow]Setup cancelled[/yellow]")
        raise typer.Exit(0) from None
    except Exception as e:
        console.print(f"[red]❌ Setup failed: {e}[/red]")
        raise typer.Exit(1) from e


@app.command("list")
def list_keys(
    show_values: bool = typer.Option(
        False, "--show-values", "-v", help="Show actual API key values (be careful!)"
    ),
):
    """List configured API keys."""
    manager = APIKeyManager(storage_method=_get_storage_method())

    # Create a table
    table = Table(title="Configured API Keys")
    table.add_column("Provider", style="cyan")
    table.add_column("Status", style="green")
    if show_values:
        # Prevent truncation when showing full values
        table.add_column("API Key", style="yellow", no_wrap=True, overflow="fold")
    else:
        table.add_column("Key Preview", style="yellow")

    providers = [
        ("openai", "OpenAI"),
        ("anthropic", "Anthropic"),
        ("openrouter", "OpenRouter"),
        ("google", "Google Gemini"),
        ("deepseek", "DeepSeek"),
        ("minimax", "MiniMax"),
        ("qwen", "Qwen/DashScope"),
        ("zhipu", "Zhipu GLM"),
        ("ollama", "Ollama"),
        ("vllm", "vLLM"),
        ("lmstudio", "LM Studio"),
        ("llamacpp_server", "llama.cpp Server"),
        ("local_server", "Local OpenAI-Compatible"),
    ]

    found_any = False
    for provider_id, provider_name in providers:
        key = manager.get_key(provider_id)
        if key:
            found_any = True
            if show_values:
                table.add_row(provider_name, "✅ Configured", key)
            else:
                # Show first 10 and last 4 characters
                if len(key) > 20:
                    preview = f"{key[:10]}...{key[-4:]}"
                else:
                    preview = f"{key[:4]}..." if len(key) > 4 else "***"
                table.add_row(provider_name, "✅ Configured", preview)
        else:
            table.add_row(provider_name, "❌ Not configured", "-")

    console.print(table)

    if not found_any:
        console.print(
            "\n[yellow]💡 Tip: Run 'codeconcat keys setup' to configure API keys[/yellow]"
        )


@app.command("set")
def set_key(
    provider: str = typer.Argument(..., help="Provider name (see --help for all providers)"),
    api_key: str | None = typer.Argument(None, help="API key value (will prompt if not provided)"),
    validate: bool = typer.Option(True, "--validate/--no-validate", help="Validate API key format"),
):
    """Set or update an API key for a specific provider."""
    manager = APIKeyManager(storage_method=_get_storage_method())

    # Normalize provider name
    provider = provider.lower()
    valid_providers = [
        "openai",
        "anthropic",
        "openrouter",
        "google",
        "deepseek",
        "minimax",
        "qwen",
        "zhipu",
        "ollama",
        "vllm",
        "lmstudio",
        "llamacpp_server",
        "local_server",
        "llamacpp",
    ]

    if provider not in valid_providers:
        console.print(f"[red]❌ Invalid provider: {provider}[/red]")
        console.print(f"Valid providers: {', '.join(valid_providers)}")
        raise typer.Exit(1)

    # Check if key already exists
    existing_key = manager.get_key(provider)
    if existing_key:
        console.print(f"[yellow]⚠️  API key for {provider} already exists[/yellow]")
        if not Confirm.ask("Do you want to replace it?"):
            raise typer.Exit(0)

    # Get API key if not provided
    if not api_key:
        api_key = Prompt.ask(f"Enter API key for {provider}", password=True)

    if not api_key:
        console.print("[red]❌ No API key provided[/red]")
        raise typer.Exit(1)

    # Validate if requested
    if validate and not manager._validate_api_key(provider, api_key):
        console.print(f"[red]❌ Invalid API key format for {provider}[/red]")
        if not Confirm.ask("Continue anyway?"):
            raise typer.Exit(1)
        validate = False

    # Store the key
    try:
        success = manager.set_key(provider, api_key, validate=validate)
        if success:
            console.print(f"[green]✅ API key for {provider} stored successfully[/green]")
        else:
            console.print("[red]❌ Failed to store API key[/red]")
            raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Error storing API key: {e}[/red]")
        raise typer.Exit(1) from e


@app.command("delete")
def delete_key(
    provider: str = typer.Argument(..., help="Provider name (see --help for all providers)"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt"),
):
    """Delete an API key for a specific provider."""
    manager = APIKeyManager(storage_method=_get_storage_method())

    # Normalize provider name
    provider = provider.lower()
    valid_providers = [
        "openai",
        "anthropic",
        "openrouter",
        "google",
        "deepseek",
        "minimax",
        "qwen",
        "zhipu",
        "ollama",
        "vllm",
        "lmstudio",
        "llamacpp_server",
        "local_server",
        "llamacpp",
    ]

    if provider not in valid_providers:
        console.print(f"[red]❌ Invalid provider: {provider}[/red]")
        console.print(f"Valid providers: {', '.join(valid_providers)}")
        raise typer.Exit(1)

    # Check if key exists
    existing_key = manager.get_key(provider)
    if not existing_key:
        console.print(f"[yellow]⚠️  No API key found for {provider}[/yellow]")
        raise typer.Exit(0)

    # Confirm deletion
    if not force and not Confirm.ask(
        f"Are you sure you want to delete the API key for {provider}?"
    ):
        raise typer.Exit(0)

    # Delete the key
    try:
        success = manager.delete_key(provider)
        if success:
            console.print(f"[green]✅ API key for {provider} deleted successfully[/green]")
        else:
            console.print("[red]❌ Failed to delete API key[/red]")
            raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Error deleting API key: {e}[/red]")
        raise typer.Exit(1) from e


@app.command("reset")
def reset_keys(force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt")):
    """Reset all API keys (delete all stored keys)."""
    manager = APIKeyManager(storage_method=_get_storage_method())

    # List current keys
    providers = [
        "openai",
        "anthropic",
        "openrouter",
        "google",
        "deepseek",
        "minimax",
        "qwen",
        "zhipu",
        "ollama",
        "vllm",
        "lmstudio",
        "llamacpp_server",
        "local_server",
        "llamacpp",
    ]
    stored_keys = []

    for provider in providers:
        if manager.get_key(provider):
            stored_keys.append(provider)

    if not stored_keys:
        console.print("[yellow]⚠️  No API keys to reset[/yellow]")
        raise typer.Exit(0)

    console.print("[yellow]⚠️  This will delete the following API keys:[/yellow]")
    for provider in stored_keys:
        console.print(f"  - {provider}")

    # Confirm deletion
    if not force and not Confirm.ask("Are you sure you want to delete ALL API keys?"):
        raise typer.Exit(0)

    # Delete all keys
    deleted = 0
    failed = 0

    for provider in stored_keys:
        try:
            if manager.delete_key(provider):
                deleted += 1
            else:
                failed += 1
        except Exception:
            failed += 1

    if deleted > 0:
        console.print(f"[green]✅ Deleted {deleted} API key(s)[/green]")
    if failed > 0:
        console.print(f"[red]❌ Failed to delete {failed} API key(s)[/red]")


@app.command("test")
def test_key(
    provider: str = typer.Argument(..., help="Provider name (cloud providers with API keys)"),
):
    """Test if an API key is valid by making a minimal request."""
    manager = APIKeyManager(storage_method=_get_storage_method())

    # Normalize provider name
    provider = provider.lower()
    valid_providers = [
        "openai",
        "anthropic",
        "openrouter",
        "google",
        "deepseek",
        "minimax",
        "qwen",
        "zhipu",
    ]

    if provider not in valid_providers:
        console.print(f"[red]❌ Invalid provider: {provider}[/red]")
        console.print(f"Valid providers: {', '.join(valid_providers)}")
        raise typer.Exit(1)

    # Get the key
    api_key = manager.get_key(provider)
    if not api_key:
        console.print(f"[red]❌ No API key found for {provider}[/red]")
        console.print(f"[yellow]💡 Run 'codeconcat keys set {provider}' to configure[/yellow]")
        raise typer.Exit(1)

    # Test the key
    console.print(f"[cyan]🔍 Testing {provider} API key...[/cyan]")

    async def test():
        return await manager.test_api_key(provider, api_key)

    try:
        is_valid = asyncio.run(test())

        if is_valid:
            console.print(f"[green]✅ API key for {provider} is valid and working![/green]")
        else:
            console.print(f"[red]❌ API key for {provider} failed validation[/red]")
            console.print(
                "[yellow]The key might be invalid, expired, or the service might be down[/yellow]"
            )
            raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Error testing API key: {e}[/red]")
        raise typer.Exit(1) from e


@app.command("change-password")
def change_password():
    """Change the master password for encrypted key storage."""
    from getpass import getpass

    console.print("[bold cyan]🔐 Change Master Password[/bold cyan]")
    console.print("=" * 50)

    # Check if using encrypted storage
    manager = APIKeyManager(storage_method=KeyStorage.ENCRYPTED_FILE)

    # Check if any keys exist
    providers = [
        "openai",
        "anthropic",
        "openrouter",
        "google",
        "deepseek",
        "minimax",
        "qwen",
        "zhipu",
        "ollama",
        "vllm",
        "lmstudio",
        "llamacpp_server",
        "local_server",
        "llamacpp",
    ]
    stored_keys: dict[str, str] = {}

    # Get current password and load keys
    console.print("[cyan]Enter current master password to load existing keys[/cyan]")
    current_password = getpass("Current password: ")

    # Try to load keys with current password
    manager._fernet = None  # Reset to force password prompt

    try:
        # Temporarily set password
        import unittest.mock as mock

        with mock.patch("getpass.getpass", return_value=current_password):
            for provider in providers:
                key = manager.get_key(provider)
                if key:
                    stored_keys[provider] = key
    except Exception as e:
        console.print(f"[red]❌ Failed to decrypt with current password: {e}[/red]")
        raise typer.Exit(1) from e

    if not stored_keys:
        console.print("[yellow]⚠️  No encrypted keys found[/yellow]")
        raise typer.Exit(0)

    # Get new password
    console.print("\n[cyan]Enter new master password[/cyan]")
    new_password = getpass("New password: ")
    confirm_password = getpass("Confirm new password: ")

    if new_password != confirm_password:
        console.print("[red]❌ Passwords do not match[/red]")
        raise typer.Exit(1)

    if len(new_password) < 8:
        console.print("[red]❌ Password must be at least 8 characters[/red]")
        raise typer.Exit(1)

    # Create new manager with new password
    new_manager = APIKeyManager(storage_method=KeyStorage.ENCRYPTED_FILE)

    # Store all keys with new password
    import unittest.mock as mock

    with mock.patch("getpass.getpass", return_value=new_password):
        for provider, key in stored_keys.items():
            success = new_manager.set_key(provider, key, validate=False)
            if not success:
                console.print(f"[red]❌ Failed to re-encrypt key for {provider}[/red]")
                raise typer.Exit(1)

    console.print("[green]✅ Master password changed successfully![/green]")
    console.print(f"[green]✅ Re-encrypted {len(stored_keys)} API key(s)[/green]")


@app.command("export")
def export_keys(
    output_file: str = typer.Option(
        None, "--output", "-o", help="Output file for exported keys (JSON format)"
    ),
    include_values: bool = typer.Option(
        False, "--include-values", help="Include actual API key values (DANGEROUS!)"
    ),
):
    """Export API keys configuration (for backup or migration)."""
    import json
    from typing import Any

    manager = APIKeyManager(storage_method=_get_storage_method())

    providers = [
        "openai",
        "anthropic",
        "openrouter",
        "google",
        "deepseek",
        "minimax",
        "qwen",
        "zhipu",
        "ollama",
        "vllm",
        "lmstudio",
        "llamacpp_server",
        "local_server",
        "llamacpp",
    ]
    export_data: dict[str, Any] = {"version": "1.0", "keys": {}}

    for provider in providers:
        key = manager.get_key(provider)
        if key:
            if include_values:
                export_data["keys"][provider] = key
            else:
                # Just mark as configured
                export_data["keys"][provider] = "***CONFIGURED***"

    if not export_data["keys"]:
        console.print("[yellow]⚠️  No API keys to export[/yellow]")
        raise typer.Exit(0)

    if output_file:
        try:
            with open(output_file, "w") as f:
                json.dump(export_data, f, indent=2)
            console.print(f"[green]✅ Exported to {output_file}[/green]")
        except Exception as e:
            console.print(f"[red]❌ Failed to write file: {e}[/red]")
            raise typer.Exit(1) from e
    else:
        # Print to console
        console.print(json.dumps(export_data, indent=2))

    if include_values:
        console.print("[bold red]⚠️  WARNING: Exported file contains sensitive API keys![/bold red]")
        console.print("[red]Keep this file secure and delete it after use.[/red]")


if __name__ == "__main__":
    app()
