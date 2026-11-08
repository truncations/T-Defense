"""Regression for native argument quoting in actual Windows PowerShell 5.1."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from vm_kit import readiness

ROOT = Path(__file__).resolve().parent.parent


def test_vm_readiness_emits_json_success_only_after_probe(monkeypatch, capsys):
    monkeypatch.setattr(readiness, "check_browser", lambda: None)
    assert readiness.main() == 0
    assert json.loads(capsys.readouterr().out) == {"ok": True}


def test_vm_readiness_failure_is_bounded_json_not_native_stderr(monkeypatch, capsys):
    def fail():
        raise RuntimeError("Synthetic readiness failure " + ("x" * 6000))

    monkeypatch.setattr(readiness, "check_browser", fail)
    assert readiness.main() == 1
    captured = capsys.readouterr()
    value = json.loads(captured.out)
    assert value["ok"] is False and "Synthetic readiness failure" in value["error"]
    assert len(value["error"]) <= 4000 and not captured.err


def test_vm_policy_helpers_reject_bad_route_and_private_address():
    from unittest.mock import patch

    from vm_kit import checks

    with (
        patch("sys.argv", ["checks", "route-overlaps", "not-a-route"]),
        pytest.raises(ValueError),
    ):
        checks.main()
    with (
        patch("sys.argv", ["checks", "public-ip"]),
        patch("sys.stdin") as stream,
        pytest.raises(ValueError),
    ):
        stream.read.return_value = "127.0.0.1"
        checks.main()


def test_vm_ps51_file_and_module_calls_preserve_quotes(tmp_path):
    if sys.platform != "win32":
        pytest.skip("Windows PowerShell 5.1 native argument handling")
    python = str(Path(sys.executable)).replace("'", "''")
    project = str(ROOT).replace("'", "''")
    probe = tmp_path / "probe with spaces.py"
    probe.write_text(
        'import json\nprint(json.dumps({"ok":True,"html":"<h1>Synthetic offline readiness check</h1>"}))\n',
        encoding="utf8",
    )
    script = tmp_path / "native probe.ps1"
    script.write_text(
        "Set-Location -LiteralPath '"
        + project
        + "'\n& '"
        + python
        + "' '"
        + str(probe).replace("'", "''")
        + "'\n'https://example.com/' | & '"
        + python
        + "' -m vm_kit.checks origin\n& '"
        + python
        + "' -m vm_kit.checks route-overlaps '192.168.253.0/24'\n& '"
        + python
        + "' -m vm_kit.checks route-overlaps '10.0.0.0/8'\n'93.184.216.34' | & '"
        + python
        + "' -m vm_kit.checks public-ip\nexit $LASTEXITCODE\n",
        encoding="utf8",
    )
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-File", str(script)],
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    lines = result.stdout.strip().splitlines()
    assert json.loads(lines[0]) == {
        "ok": True,
        "html": "<h1>Synthetic offline readiness check</h1>",
    }
    assert lines[1:] == ["https://example.com", "True", "False", "93.184.216.34"]


def test_vm_seal_uses_script_file_and_route_failures_block_provisioning():
    text = (ROOT / "vm_kit/TDefense-VM.ps1").read_text(encoding="utf8")
    assert " -c '" not in text
    assert "readiness-check.py" in text and "ConvertFrom-Json" in text
    assert "This VM uses Server Core" in text
    assert "Cannot validate local route overlap; no switch will be created." in text
