"""Execute the five workshop notebooks in clean offline kernels."""

import ast
import os
import sys
import tempfile
from pathlib import Path

import nbformat
from jupyter_client import KernelManager
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]


def check_live_disabled(notebook, path):
    assignments = []
    for cell in notebook.cells:
        if cell.cell_type != "code":
            continue
        tree = ast.parse(cell.source, filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "RUN_LIVE":
                        assignments.append(node.value)
    if not assignments or any(
        not isinstance(value, ast.Constant) or value.value is not False for value in assignments
    ):
        raise ValueError(f"RUN_LIVE must remain explicitly False: {path}")


def main():
    starters = sorted(ROOT.glob("sessions/*/starter.ipynb"))
    paths = starters
    if len(starters) != 5:
        raise ValueError("Expected five workshop notebooks")
    environment = dict(os.environ)
    environment.pop("OPENAI_API_KEY", None)
    environment.pop("OPENAI_ADMIN_KEY", None)
    environment["CARRITO_NOTEBOOK_CHECK"] = "1"
    environment["PATH"] = str(Path(sys.executable).parent) + os.pathsep + environment["PATH"]
    failures = []
    with tempfile.TemporaryDirectory(prefix="carrito-notebook-check-") as directory:
        for index, path in enumerate(paths, 1):
            relative = path.relative_to(ROOT)
            try:
                notebook = nbformat.read(path, as_version=4)
                nbformat.validate(notebook)
                check_live_disabled(notebook, path)
                # Assertions added only to temporary executions, never student sources.
                condition = "not all(COMPLETION.values())"
                notebook.cells.append(
                    nbformat.v4.new_code_cell(
                        "assert COMPLETION, 'No behavior checks executed'\n"
                        f"assert {condition}, 'Exercise completion contract failed'\n"
                        "assert RUN_LIVE is False\n"
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
    print(f"{len(paths) - len(failures)}/{len(paths)} notebooks executed in clean offline kernels.")
    print("Checks cover exercise mechanics, not real LLM quality or written work.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
