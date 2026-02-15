"""CLI interface for LLocal Transcriptor."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel

from transcriptor.config import WHISPER_MODELS, Config

app = typer.Typer(
    name="llocal-transcriptor",
    help="Local audio transcription tool — 100% offline, powered by faster-whisper.",
)
console = Console()


@app.command()
def transcribe(
    audio_path: Annotated[Path, typer.Argument(help="Path to audio/video file to transcribe.")],
    model: Annotated[
        str, typer.Option("--model", "-m", help="Whisper model to use.")
    ] = "",
    language: Annotated[
        str, typer.Option("--language", "-l", help="Language code (e.g. 'en', 'pt') or 'auto'.")
    ] = "",
    output_format: Annotated[
        str,
        typer.Option("--format", "-f", help="Output format: txt, srt, json."),
    ] = "",
) -> None:
    """Transcribe an audio or video file."""
    cfg = Config.load()
    model_name = model or cfg.whisper_model
    lang = language or cfg.language
    fmt = output_format or cfg.output_format

    if model_name not in WHISPER_MODELS:
        console.print(
            f"[red]Unknown model '{model_name}'. "
            f"Available: {', '.join(WHISPER_MODELS)}[/red]"
        )
        raise typer.Exit(1)

    if not audio_path.exists():
        console.print(f"[red]File not found: {audio_path}[/red]")
        raise typer.Exit(1)

    console.print(f"[bold]Transcribing:[/bold] {audio_path}")
    console.print(f"[dim]Model: {model_name} | Language: {lang} | Format: {fmt}[/dim]")

    from transcriptor.transcriber import Transcriber

    with console.status("Loading model..."):
        transcriber = Transcriber(model_name=model_name)

    with console.status("Transcribing..."):
        result = transcriber.transcribe(audio_path, language=lang if lang != "auto" else None)

    if fmt == "srt":
        output = result.to_srt()
    elif fmt == "json":
        output = result.to_json()
    else:
        output = result.to_txt()

    console.print()
    console.print(Panel(output, title="Transcription", border_style="green"))
    console.print(
        f"\n[dim]Language: {result.language} "
        f"(confidence: {result.language_probability:.0%})[/dim]"
    )


@app.command()
def serve(
    host: Annotated[
        str, typer.Option("--host", "-h", help="Host to bind the WebSocket server.")
    ] = "localhost",
    port: Annotated[
        int, typer.Option("--port", "-p", help="Port for the WebSocket server.")
    ] = 9867,
) -> None:
    """Start the WebSocket server for real-time transcription."""
    console.print(
        Panel(
            f"[bold green]LLocal Transcriptor — WebSocket Server[/bold green]\n\n"
            f"Listening on [cyan]ws://{host}:{port}[/cyan]\n"
            f"Press [bold]Ctrl+C[/bold] to stop.",
            border_style="blue",
        )
    )

    from transcriptor.ws_server import run_server

    run_server(host=host, port=port)


@app.command()
def config(
    show: Annotated[
        bool, typer.Option("--show", help="Show current configuration.")
    ] = False,
) -> None:
    """Manage configuration."""
    cfg = Config.load()
    if show:
        console.print(Panel(
            f"whisper_model: {cfg.whisper_model}\n"
            f"language: {cfg.language}\n"
            f"ollama_model: {cfg.ollama_model}\n"
            f"ollama_url: {cfg.ollama_url}\n"
            f"summary_style: {cfg.summary_style}\n"
            f"output_format: {cfg.output_format}",
            title="Current Config",
            border_style="blue",
        ))
    else:
        console.print("[dim]Use --show to display current configuration.[/dim]")


if __name__ == "__main__":
    app()
