import os
import subprocess
import sys


def cli(*args, input=None):
    return subprocess.run(
        [sys.executable, "-m", "carrito.cli", *args],
        input=input,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    )


def test_doctor_and_demo(tmp_path):
    assert cli("doctor").returncode == 0
    path = tmp_path / "trace.jsonl"
    demo = cli("demo", "--mode", "fixture", "--trace", str(path))
    assert demo.returncode == 0 and "P001" in demo.stdout
    assert path.is_file()
    assert "tool_result" in cli("trace", str(path)).stdout


def test_cli_return_requires_explicit_host_flag():
    assert '"return_count": 0' in cli("demo", "--scenario", "return").stdout
    assert '"return_count": 1' in cli("demo", "--scenario", "return", "--confirm").stdout


def test_chat_host_confirmation_and_history():
    result = cli("chat", "--mode", "fixture", input="devolver\n/confirm\n/quit\n")
    assert result.returncode == 0
    assert "confirmation_required" in result.stdout and '"status": "requested"' in result.stdout


def test_eval_cli_reports_real_checks():
    result = cli("eval", "--split", "dev", "--mode", "fixture")
    assert result.returncode == 0
    assert '"total": 16' in result.stdout and '"passed": 16' in result.stdout


def test_eval_cli_rejects_unavailable_dataset():
    result = cli("eval", "--split", "missing", "--mode", "fixture")
    assert result.returncode == 2
    assert "invalid choice" in result.stderr
