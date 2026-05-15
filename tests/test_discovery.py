"""Tests for gemini_agent_sdk.discovery — binary location."""

import os
import sys
from unittest.mock import patch

import pytest

from gemini_agent_sdk.discovery import find_gemini_binary


def test_override_path_exists(tmp_path):
    binary = tmp_path / "gemini"
    binary.write_text("fake")
    result = find_gemini_binary(str(binary))
    assert result == str(binary)


def test_override_path_not_found():
    with pytest.raises(FileNotFoundError, match="not found at"):
        find_gemini_binary("/nonexistent/path/gemini")


def test_found_on_path():
    with patch("gemini_agent_sdk.discovery.shutil.which", return_value="/usr/bin/gemini"):
        result = find_gemini_binary()
        assert result == "/usr/bin/gemini"


def test_windows_fallback(tmp_path, monkeypatch):
    monkeypatch.setattr("gemini_agent_sdk.discovery.shutil.which", lambda _: None)
    monkeypatch.setattr("gemini_agent_sdk.discovery.sys.platform", "win32")

    # Create fake binary in APPDATA/npm/
    appdata = tmp_path / "AppData" / "Roaming"
    npm_dir = appdata / "npm"
    npm_dir.mkdir(parents=True)
    fake_bin = npm_dir / "gemini.cmd"
    fake_bin.write_text("fake")

    monkeypatch.setenv("APPDATA", str(appdata))
    result = find_gemini_binary()
    assert result == str(fake_bin)


def test_not_found_raises():
    with patch("gemini_agent_sdk.discovery.shutil.which", return_value=None):
        with patch("gemini_agent_sdk.discovery.os.path.isfile", return_value=False):
            with pytest.raises(FileNotFoundError, match="npm install"):
                find_gemini_binary()
