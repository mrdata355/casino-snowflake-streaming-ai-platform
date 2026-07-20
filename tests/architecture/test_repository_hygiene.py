from pathlib import Path

FORBIDDEN_NAMES = {
    ".env",
    "terraform.tfstate",
    "terraform.tfstate.backup",
    "rsa_key.p8",
    "id_rsa",
}


def test_no_forbidden_secret_or_state_files_are_present() -> None:
    violations = [
        str(path) for path in Path(".").rglob("*") if path.is_file() and path.name in FORBIDDEN_NAMES
    ]
    assert not violations, f"Forbidden files found: {violations}"


def test_repository_documents_synthetic_data_boundary() -> None:
    readme = Path("README.md").read_text(encoding="utf-8").lower()
    assert "synthetic" in readme
    assert "not a production system" in readme
