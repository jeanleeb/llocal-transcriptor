"""Tests for transcriptor.config."""

from __future__ import annotations

from pathlib import Path

from transcriptor.config import CONFIG_DIR, DEFAULT_CONFIG, Config


class TestConfigDefaults:
    def test_default_values(self):
        cfg = Config()
        assert cfg.whisper_model == "base"
        assert cfg.language == "auto"
        assert cfg.ollama_model == "llama3.1"
        assert cfg.ollama_url == "http://localhost:11434"
        assert cfg.summary_style == "bullets"
        assert cfg.output_format == "txt"

    def test_default_config_dict_matches_dataclass(self):
        cfg = Config()
        for key, value in DEFAULT_CONFIG.items():
            assert getattr(cfg, key) == value

    def test_config_dir_path(self):
        assert Path.home() / ".config" / "llocal-transcriptor" == CONFIG_DIR


class TestConfigLoad:
    def test_load_returns_defaults_when_no_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr("transcriptor.config.CONFIG_FILE", tmp_path / "nonexistent.toml")
        cfg = Config.load()
        assert cfg.whisper_model == "base"
        assert cfg.language == "auto"

    def test_load_reads_toml_file(self, tmp_path, monkeypatch):
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            'whisper_model = "large-v3"\nlanguage = "pt"\nollama_model = "gemma2"\n'
        )
        monkeypatch.setattr("transcriptor.config.CONFIG_FILE", config_file)
        cfg = Config.load()
        assert cfg.whisper_model == "large-v3"
        assert cfg.language == "pt"
        assert cfg.ollama_model == "gemma2"
        # defaults preserved for unset keys
        assert cfg.ollama_url == "http://localhost:11434"
        assert cfg.summary_style == "bullets"
        assert cfg.output_format == "txt"

    def test_load_partial_override(self, tmp_path, monkeypatch):
        config_file = tmp_path / "config.toml"
        config_file.write_text('output_format = "srt"\n')
        monkeypatch.setattr("transcriptor.config.CONFIG_FILE", config_file)
        cfg = Config.load()
        assert cfg.output_format == "srt"
        assert cfg.whisper_model == "base"


class TestConfigSave:
    def test_save_creates_file(self, tmp_path, monkeypatch):
        config_dir = tmp_path / "config"
        config_file = config_dir / "config.toml"
        monkeypatch.setattr("transcriptor.config.CONFIG_DIR", config_dir)
        monkeypatch.setattr("transcriptor.config.CONFIG_FILE", config_file)

        cfg = Config(whisper_model="small", language="en")
        cfg.save()

        assert config_file.exists()
        content = config_file.read_text()
        assert 'whisper_model = "small"' in content
        assert 'language = "en"' in content

    def test_save_roundtrip(self, tmp_path, monkeypatch):
        config_dir = tmp_path / "config"
        config_file = config_dir / "config.toml"
        monkeypatch.setattr("transcriptor.config.CONFIG_DIR", config_dir)
        monkeypatch.setattr("transcriptor.config.CONFIG_FILE", config_file)

        original = Config(
            whisper_model="medium",
            language="pt",
            ollama_model="llama3.1",
            ollama_url="http://localhost:11434",
            summary_style="paragraph",
            output_format="json",
        )
        original.save()

        loaded = Config.load()
        assert loaded.whisper_model == original.whisper_model
        assert loaded.language == original.language
        assert loaded.summary_style == original.summary_style
        assert loaded.output_format == original.output_format
