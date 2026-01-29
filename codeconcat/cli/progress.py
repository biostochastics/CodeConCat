"""Progress dashboard for CodeConCat CLI.

Provides a unified progress display using Rich Live panel that shows
all stages of processing with their current status.
"""

import sys
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Literal, Protocol

from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.text import Text


class StageStatus(Enum):
    """Status of a processing stage."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Stage:
    """A processing stage in the dashboard."""

    name: str
    status: StageStatus = StageStatus.PENDING
    total: int = 0
    current: int = 0
    message: str = ""
    start_time: float | None = None
    end_time: float | None = None

    @property
    def elapsed(self) -> float:
        """Get elapsed time for this stage."""
        if self.start_time is None:
            return 0.0
        end = self.end_time or time.monotonic()
        return end - self.start_time

    @property
    def progress_pct(self) -> float:
        """Get progress percentage (0-100)."""
        if self.total == 0:
            return 0.0
        return min(100.0, (self.current / self.total) * 100)


class ProgressCallback(Protocol):
    """Protocol for progress callbacks."""

    def __call__(self, current: int, total: int, message: str = "") -> None:
        """Update progress."""
        ...


@dataclass
class ProgressDashboard:
    """Rich Live dashboard showing all processing stages.

    Usage:
        with ProgressDashboard() as dashboard:
            dashboard.start_stage("Collecting", total=100)
            for i in range(100):
                dashboard.update_progress(i + 1, 100)
            dashboard.complete_stage()

            dashboard.start_stage("Parsing", total=50)
            # ...
    """

    title: str = "CodeConCat"
    console: Console = field(default_factory=Console)
    refresh_rate: float = 10.0  # Hz
    min_width: int = 40
    _stages: list[Stage] = field(default_factory=list)
    _current_stage_idx: int = -1
    _live: Live | None = None
    _start_time: float | None = None
    _enabled: bool = True
    _is_tty: bool = True

    def __post_init__(self) -> None:
        """Initialize dashboard state."""
        # Default stages for CodeConCat
        self._stages = [
            Stage("Collecting"),
            Stage("Parsing"),
            Stage("Annotating"),
            Stage("Writing"),
        ]
        self._is_tty = sys.stdout.isatty()

    @property
    def current_stage(self) -> Stage | None:
        """Get the current stage, if any."""
        if 0 <= self._current_stage_idx < len(self._stages):
            return self._stages[self._current_stage_idx]
        return None

    @property
    def total_elapsed(self) -> float:
        """Get total elapsed time since dashboard started."""
        if self._start_time is None:
            return 0.0
        return time.monotonic() - self._start_time

    def disable(self) -> None:
        """Disable the dashboard (for quiet mode or no TTY)."""
        self._enabled = False

    def enable(self) -> None:
        """Enable the dashboard."""
        self._enabled = True

    def _get_stage_icon(self, stage: Stage) -> Text:
        """Get the status icon for a stage."""
        match stage.status:
            case StageStatus.PENDING:
                return Text("○", style="dim")
            case StageStatus.IN_PROGRESS:
                return Text("●", style="cyan bold")
            case StageStatus.COMPLETED:
                return Text("✓", style="green bold")
            case StageStatus.FAILED:
                return Text("✗", style="red bold")
            case StageStatus.SKIPPED:
                return Text("○", style="dim strikethrough")
            case _:
                return Text("?", style="yellow")

    def _render_stage(self, stage: Stage, width: int) -> Text:
        """Render a single stage line."""
        icon = self._get_stage_icon(stage)
        name = Text(
            f" {stage.name:<12}", style="bold" if stage.status == StageStatus.IN_PROGRESS else ""
        )

        if stage.status == StageStatus.PENDING:
            status_text = Text("waiting", style="dim")
        elif stage.status == StageStatus.COMPLETED:
            if stage.message:
                status_text = Text(stage.message, style="green")
            elif stage.total > 0:
                status_text = Text(f"{stage.total} files", style="green")
            else:
                status_text = Text("done", style="green")
        elif stage.status == StageStatus.FAILED:
            status_text = Text(stage.message or "failed", style="red")
        elif stage.status == StageStatus.SKIPPED:
            status_text = Text("skipped", style="dim")
        elif stage.status == StageStatus.IN_PROGRESS:
            if stage.total > 0:
                # Show progress bar
                pct = stage.progress_pct
                bar_width = max(2, min(30, width - 35))  # Clamp to avoid negative/zero
                filled = int(bar_width * pct / 100)
                bar = "━" * filled + "╺" + "─" * max(0, bar_width - filled - 1)

                count_text = f"{stage.current}/{stage.total}"
                pct_text = f"{pct:>3.0f}%"

                status_text = Text()
                status_text.append(f"{count_text:<12}", style="cyan")
                status_text.append(bar, style="cyan")
                status_text.append(f" {pct_text}", style="cyan bold")
            else:
                # Show spinner-style message
                status_text = Text(stage.message or "processing...", style="cyan")
        else:
            status_text = Text("")

        line = Text()
        line.append_text(icon)
        line.append_text(name)
        line.append_text(status_text)
        return line

    def _render(self) -> Panel:
        """Render the full dashboard panel."""
        width = self.console.width or 80
        width = max(self.min_width, min(width, 100))

        lines = [self._render_stage(stage, width) for stage in self._stages]

        # Footer with elapsed time
        elapsed = self.total_elapsed
        mins, secs = divmod(int(elapsed), 60)
        elapsed_text = Text(f"elapsed {mins}:{secs:02d}", style="dim")

        content = Group(*lines)

        return Panel(
            content,
            title=f"[bold cyan]{self.title}[/]",
            subtitle=elapsed_text,
            subtitle_align="right",
            border_style="cyan",
            width=width,
            padding=(0, 1),
        )

    def start_stage(self, name: str, total: int = 0, message: str = "") -> ProgressCallback:
        """Start a processing stage.

        Args:
            name: Stage name (must match predefined stage names)
            total: Total items to process (0 for indeterminate)
            message: Optional status message

        Returns:
            A callback function for updating progress
        """
        # Find the stage by name
        for idx, stage in enumerate(self._stages):
            if stage.name.lower() == name.lower():
                self._current_stage_idx = idx
                stage.status = StageStatus.IN_PROGRESS
                stage.total = total
                stage.current = 0
                stage.message = message
                stage.start_time = time.monotonic()
                stage.end_time = None
                break

        self._refresh(force=True)  # Force refresh on stage start

        # Return a callback for updating progress
        def callback(current: int, total: int, message: str = "") -> None:
            self.update_progress(current, total, message)

        return callback

    def update_progress(self, current: int, total: int, message: str = "") -> None:
        """Update progress for the current stage."""
        stage = self.current_stage
        if stage is None:
            return

        stage.current = current
        if total > 0:
            stage.total = total
        if message:
            stage.message = message

        self._refresh()

    def complete_stage(self, message: str = "") -> None:
        """Mark the current stage as completed."""
        stage = self.current_stage
        if stage is None:
            return

        stage.status = StageStatus.COMPLETED
        stage.end_time = time.monotonic()
        if message:
            stage.message = message
        elif stage.total > 0:
            stage.current = stage.total

        self._refresh(force=True)  # Force refresh on stage completion

    def fail_stage(self, message: str = "failed") -> None:
        """Mark the current stage as failed."""
        stage = self.current_stage
        if stage is None:
            return

        stage.status = StageStatus.FAILED
        stage.end_time = time.monotonic()
        stage.message = message

        self._refresh(force=True)  # Force refresh on stage failure

    def skip_stage(self, name: str, message: str = "skipped") -> None:
        """Mark a stage as skipped."""
        for stage in self._stages:
            if stage.name.lower() == name.lower():
                stage.status = StageStatus.SKIPPED
                stage.message = message
                break

        self._refresh(force=True)  # Force refresh on skip

    def skip_remaining(self, message: str = "cancelled") -> None:
        """Mark all pending stages as skipped (for cancellation)."""
        for stage in self._stages:
            if stage.status == StageStatus.PENDING:
                stage.status = StageStatus.SKIPPED
                stage.message = message
            elif stage.status == StageStatus.IN_PROGRESS:
                stage.status = StageStatus.SKIPPED
                stage.message = message
                stage.end_time = time.monotonic()

        self._refresh(force=True)  # Force refresh on cancellation

    def _refresh(self, force: bool = False) -> None:
        """Refresh the display.

        Args:
            force: If True, refresh immediately. Otherwise, defer to refresh_per_second.
        """
        if not self._enabled or self._live is None:
            return
        # Use refresh=False to honor refresh_per_second and reduce flicker
        # Only force refresh on stage transitions (start/complete/fail)
        self._live.update(self._render(), refresh=force)

    def __enter__(self) -> "ProgressDashboard":
        """Start the live display."""
        self._start_time = time.monotonic()

        if not self._enabled or not self._is_tty:
            return self

        self._live = Live(
            self._render(),
            console=self.console,
            refresh_per_second=self.refresh_rate,
            transient=False,
        )
        self._live.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> Literal[False]:
        """Stop the live display."""
        if self._live is not None:
            self._live.__exit__(exc_type, exc_val, exc_tb)
            self._live = None
        return False


class SimpleProgress:
    """Simple line-by-line progress for non-TTY environments.

    Provides the same interface as ProgressDashboard but outputs
    simple text lines instead of a live dashboard.
    """

    def __init__(self, console: Console | None = None, quiet: bool = False) -> None:
        self.console = console or Console()
        self.quiet = quiet
        self._current_stage: str = ""
        self._last_pct: int = -1

    def disable(self) -> None:
        """Disable output."""
        self.quiet = True

    def enable(self) -> None:
        """Enable output."""
        self.quiet = False

    def start_stage(self, name: str, total: int = 0, message: str = "") -> ProgressCallback:
        """Start a stage."""
        self._current_stage = name
        self._last_pct = -1
        if not self.quiet:
            if message:
                self.console.print(f"[cyan][{name}][/cyan] {message}")
            elif total > 0:
                self.console.print(f"[cyan][{name}][/cyan] 0/{total}")
            else:
                self.console.print(f"[cyan][{name}][/cyan] starting...")

        def callback(current: int, total: int, message: str = "") -> None:
            self.update_progress(current, total, message)

        return callback

    def update_progress(self, current: int, total: int, _message: str = "") -> None:
        """Update progress (only prints on 10% increments to reduce noise)."""
        if self.quiet or total == 0:
            return

        pct = int((current / total) * 100)
        # Only print on 10% increments
        if pct // 10 > self._last_pct // 10:
            self._last_pct = pct
            self.console.print(f"[cyan][{self._current_stage}][/cyan] {current}/{total} ({pct}%)")

    def complete_stage(self, message: str = "") -> None:
        """Complete current stage."""
        if not self.quiet:
            msg = message or "done"
            self.console.print(f"[green][{self._current_stage}][/green] {msg}")

    def fail_stage(self, message: str = "failed") -> None:
        """Mark stage as failed."""
        if not self.quiet:
            self.console.print(f"[red][{self._current_stage}][/red] {message}")

    def skip_stage(self, name: str, message: str = "skipped") -> None:
        """Skip a stage."""
        if not self.quiet:
            self.console.print(f"[dim][{name}][/dim] {message}")

    def skip_remaining(self, message: str = "cancelled") -> None:
        """Mark remaining as skipped."""
        if not self.quiet:
            self.console.print(f"[yellow]Remaining stages {message}[/yellow]")

    def __enter__(self) -> "SimpleProgress":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> Literal[False]:
        return False


def create_progress(
    console: Console | None = None,
    quiet: bool = False,
    force_simple: bool = False,
) -> ProgressDashboard | SimpleProgress:
    """Create appropriate progress display based on environment.

    Args:
        console: Rich console to use
        quiet: If True, create disabled progress
        force_simple: If True, use SimpleProgress even on TTY

    Returns:
        ProgressDashboard for TTY, SimpleProgress for non-TTY or if forced
    """
    console = console or Console()

    if quiet:
        progress = SimpleProgress(console, quiet=True)
        return progress

    if force_simple or not sys.stdout.isatty():
        return SimpleProgress(console, quiet=False)

    return ProgressDashboard(console=console)
