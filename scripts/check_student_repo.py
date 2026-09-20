"""Check distributable files, notebook hygiene and local documentation links."""

import json
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
TOP_FILES = {
    "README.md", "LICENSE", "THIRD_PARTY_NOTICES.md", "pyproject.toml", "uv.lock",
    ".env.example", ".gitattributes", ".gitignore", ".python-version",
}
FOLDERS = {"src", "tests", "data", "examples", "sessions", "evals", "docs", "scripts", ".github"}
DOCS = {"setup.md", "architecture.md", "references.md"}
SCRIPTS = {"check_notebooks.py", "check_student_repo.py"}
EVALS = {"README.md", "rubrics.md", "dev.jsonl"}
INTERNAL = re.compile(
    r"docs/(?:guiones|revision|research|output)|instructor-guide|evals/instructor|"
    r"solutions/|slides/|guion docente|guión docente|\bRUN_RESERVED\b|"
    r"\b\d+\s*(?:minutos|min)\b|\b\d+–\d+\s*·",
    re.IGNORECASE,
)


def main():
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT, check=True, capture_output=True, text=True,
    )
    names = sorted(set(filter(None, result.stdout.split("\0"))))
    assert names, "No workshop files found"
    for name in names:
        path = Path(name)
        assert name in TOP_FILES or path.parts[0] in FOLDERS, name
        if path.parts[0] == "docs":
            assert len(path.parts) == 2 and path.name in DOCS, name
        if path.parts[0] == "scripts":
            assert len(path.parts) == 2 and path.name in SCRIPTS, name
        if path.parts[0] == "evals":
            assert len(path.parts) == 2 and path.name in EVALS, name
        assert path.suffix not in {".pptx", ".pdf", ".docx", ".zip", ".bundle"}, name
        file = ROOT / path
        if path.suffix == ".ipynb":
            nb = json.loads(file.read_text())
            for cell in nb["cells"]:
                assert not INTERNAL.search("".join(cell["source"])), name
                if cell["cell_type"] == "code":
                    assert cell["execution_count"] is None and not cell["outputs"], name
        elif path.suffix in {".md", ".py"} and path.name != "check_student_repo.py":
            text = file.read_text()
            assert not INTERNAL.search(text), name
        if path.suffix == ".md":
            for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", file.read_text()):
                if "://" in target or target.startswith(("#", "mailto:")):
                    continue
                relative = unquote(target.split("#")[0])
                assert (file.parent / relative).exists(), (name, target)
    notebooks = [n for n in names if n.endswith("starter.ipynb")]
    assert len(notebooks) == 5
    print(f"PASS: {len(names)} workshop files, five clean notebooks and valid local links")


if __name__ == "__main__":
    main()
