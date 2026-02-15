"""CLI interface for LLocal Transcriptor."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from transcriptor.config import Config
from transcriptor.transcriber import Segment, Transcriber, TranscriptionResult

app = typer.Typer(
    name="transcriptor",
    help="LLocal Transcriptor — transcrição local de áudio e reuniões em tempo real.",
)
console = Console()


def _format_time_short(seconds: float) -> str:
    """Format seconds as MM:SS for live display."""
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02d}:{s:02d}"


@app.command()
def transcribe(
    audio_path: Path = typer.Argument(..., help="Caminho para o arquivo de áudio/vídeo."),
    model: str = typer.Option(None, "--model", "-m", help="Modelo Whisper a utilizar."),
    language: str = typer.Option(None, "--language", "-l", help="Idioma do áudio (en, pt, auto)."),
    output_format: str = typer.Option(
        None, "--format", "-f", help="Formato de saída: txt, srt, json."
    ),
) -> None:
    """Transcreve um arquivo de áudio ou vídeo."""
    cfg = Config.load()
    model_name = model or cfg.whisper_model
    lang = language or cfg.language
    fmt = output_format or cfg.output_format

    with console.status(f"Carregando modelo [bold]{model_name}[/bold]..."):
        t = Transcriber(model_name=model_name)

    with console.status("Transcrevendo..."):
        result = t.transcribe(audio_path, language=lang)

    if fmt == "srt":
        console.print(result.to_srt())
    elif fmt == "json":
        console.print(result.to_json())
    else:
        console.print(result.to_txt())


@app.command()
def live(
    model: str = typer.Option(None, "--model", "-m", help="Modelo Whisper a utilizar."),
    language: str = typer.Option(None, "--language", "-l", help="Idioma do áudio (en, pt, auto)."),
    audio_device: int = typer.Option(
        None, "--device", "-d", help="ID do dispositivo de entrada de áudio."
    ),
    list_devices: bool = typer.Option(
        False, "--list-devices", help="Listar dispositivos de áudio disponíveis e sair."
    ),
    interval: float = typer.Option(
        3.0, "--interval", "-i", help="Intervalo entre transcrições em segundos."
    ),
    output: Path = typer.Option(
        None, "--output", "-o", help="Salvar transcrição em arquivo ao finalizar."
    ),
    output_format: str = typer.Option(
        None, "--format", "-f", help="Formato de saída: txt, srt, json."
    ),
) -> None:
    """Transcrição em tempo real a partir do microfone.

    Captura áudio do microfone (ou dispositivo escolhido) e transcreve
    em tempo real usando o modelo Whisper local. Pressione Ctrl+C para
    parar a gravação.

    Para capturar áudio do sistema (ex.: reuniões), configure um
    dispositivo de áudio virtual e passe seu ID via --device.
    Use --list-devices para ver os dispositivos disponíveis.
    """
    from transcriptor.audio_capture import list_audio_devices
    from transcriptor.live_transcriber import LiveTranscriber

    if list_devices:
        devices = list_audio_devices()
        if not devices:
            console.print("[red]Nenhum dispositivo de entrada encontrado.[/red]")
            raise typer.Exit(1)
        table = Table(title="Dispositivos de Áudio")
        table.add_column("ID", style="cyan", justify="right")
        table.add_column("Nome", style="green")
        table.add_column("Canais", style="yellow", justify="right")
        for dev in devices:
            table.add_row(str(dev.index), dev.name, str(dev.max_input_channels))
        console.print(table)
        raise typer.Exit()

    cfg = Config.load()
    model_name = model or cfg.whisper_model
    lang = language or cfg.language
    fmt = output_format or cfg.output_format

    console.print(
        Panel(
            f"[bold]Modelo:[/bold] {model_name}  "
            f"[bold]Idioma:[/bold] {lang}  "
            f"[bold]Intervalo:[/bold] {interval}s\n"
            "[dim]Pressione Ctrl+C para parar a gravação.[/dim]",
            title="[bold green]Transcrição em Tempo Real[/bold green]",
            border_style="green",
        )
    )

    with console.status(f"Carregando modelo [bold]{model_name}[/bold]..."):
        lt = LiveTranscriber(
            model_name=model_name,
            language=lang,
            audio_device=audio_device,
            chunk_interval=interval,
        )

    console.print("[green]Gravando... (Ctrl+C para parar)[/green]\n")

    def on_update(segments: list[Segment], full_text: str) -> None:  # noqa: ARG001
        for seg in segments:
            text = seg.text.strip()
            if text:
                ts = _format_time_short(seg.start)
                console.print(f"[dim]{ts}[/dim]  {text}")

    session = lt.run(on_update=on_update)

    console.print("\n[yellow]Transcrição finalizada.[/yellow]")

    if session.segments:
        console.print(f"[dim]Segmentos: {len(session.segments)}  Idioma: {session.language}[/dim]")

    if output and session.segments:
        result = TranscriptionResult(
            segments=session.segments,
            language=session.language or lang or "auto",
            language_probability=session.language_probability,
            text=session.text,
        )
        if fmt == "srt":
            content = result.to_srt()
        elif fmt == "json":
            content = result.to_json()
        else:
            content = result.to_txt()
        output.write_text(content)
        console.print(f"[green]Salvo em:[/green] {output}")


if __name__ == "__main__":
    app()
