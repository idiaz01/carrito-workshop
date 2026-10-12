"""Execute the five workshop notebooks with a fake API client (no key, no cost)."""

import ast
import os
import sys
import tempfile
from pathlib import Path

import nbformat
from jupyter_client import KernelManager
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]


def check_no_live_switch(notebook, path):
    """Students always run live: a RUN_LIVE switch must not come back."""
    for cell in notebook.cells:
        if cell.cell_type == "code":
            tree = ast.parse(cell.source, filename=str(path))
            if any(isinstance(node, ast.Name) and node.id == "RUN_LIVE" for node in ast.walk(tree)):
                raise ValueError(f"RUN_LIVE switch found: {path}")


def main():
    starters = sorted(ROOT.glob("sessions/*/starter.ipynb"))
    paths = starters
    if len(starters) != 5:
        raise ValueError("Expected five workshop notebooks")
    environment = dict(os.environ)
    environment.pop("OPENAI_API_KEY", None)
    environment.pop("OPENAI_ADMIN_KEY", None)
    environment["CARRITO_OFFLINE_CHECK"] = "1"
    environment["PATH"] = str(Path(sys.executable).parent) + os.pathsep + environment["PATH"]
    failures = []
    with tempfile.TemporaryDirectory(prefix="carrito-notebook-check-") as directory:
        for index, path in enumerate(paths, 1):
            relative = path.relative_to(ROOT)
            try:
                notebook = nbformat.read(path, as_version=4)
                nbformat.validate(notebook)
                check_no_live_switch(notebook, path)
                # Assertions added only to temporary executions, never student sources.
                notebook.cells.append(
                    nbformat.v4.new_code_cell(
                        "assert COMPLETION, 'No behavior checks executed'\n"
                        "assert all(COMPLETION.values()), COMPLETION\n"
                    )
                )
                manager = KernelManager(kernel_name="python3")
                manager.kernel_spec.argv = [
                    sys.executable,
                    "-m",
                    "ipykernel_launcher",
                    "-f",
                    "{connection_file}",
                ]
                client = NotebookClient(
                    notebook,
                    timeout=180,
                    km=manager,
                    resources={"metadata": {"path": str(path.parent)}},
                    allow_errors=False,
                )
                try:
                    client.execute(env=environment)
                finally:
                    if manager.has_kernel:
                        manager.shutdown_kernel(now=True)
                nbformat.write(notebook, Path(directory) / f"{index:02d}-{path.stem}.ipynb")
                print(f"PASS {relative}", flush=True)
            except Exception as exc:
                failures.append(str(relative))
                print(f"FAIL {relative}\n{exc}", file=sys.stderr, flush=True)
    print(f"{len(paths) - len(failures)}/{len(paths)} notebooks executed with the offline client.")
    print("Checks cover code mechanics, not real LLM answers.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
