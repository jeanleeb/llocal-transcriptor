"""Configuration management for LLocal Transcriptor."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CONFIG_DIR = Path.home() / ".config" / "llocal-transcriptor"
CONFIG_FILE = CONFIG_DIR / "config.toml"

WHISPER_MODELS = ("tiny", "base", "small", "medium", "large-v3")
SUMMARY_STYLES = ("bullets", "paragraph", "action-items")
SUPPORTED_LANGUAGES = ("en", "pt")

DEFAULT_CONFIG: dict[str, Any] = {
    "whisper_model": "base",
    "language": "auto",
    "ollama_model": "llama3.1",
    "ollama_url": "http://localhost:11434",
    "summary_style": "bullets",
    "output_format": "txt",
}


@dataclass
class Config:
    whisper_model: str = "base"
    language: str = "auto"
    ollama_model: str = "llama3.1"
    ollama_url: str = "http://localhost:11434"
    summary_style: str = "bullets"
    output_format: str = "txt"

    @classmethod
    def load(cls) -> Config:
        """Load config from TOML file, falling back to defaults."""
        if not CONFIG_FILE.exists():
            return cls()

        with open(CONFIG_FILE, "rb") as f:
            data = tomllib.load(f)

        merged = {**DEFAULT_CONFIG, **data}
        return cls(
            whisper_model=merged["whisper_model"],
            language=merged["language"],
            ollama_model=merged["ollama_model"],
            ollama_url=merged["ollama_url"],
            summary_style=merged["summary_style"],
            output_format=merged["output_format"],
        )

    def save(self) -> None:
        """Save current config to TOML file."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        lines = [
            f'whisper_model = "{self.whisper_model}"',
            f'language = "{self.language}"',
            f'ollama_model = "{self.ollama_model}"',
            f'ollama_url = "{self.ollama_url}"',
            f'summary_style = "{self.summary_style}"',
            f'output_format = "{self.output_format}"',
        ]
        CONFIG_FILE.write_text("\n".join(lines) + "\n")
