import hashlib
from pathlib import Path
from typing import Union

PathLike = Union[str, Path]


class LocalStorage:
    """Local filesystem storage rooted at LOCAL_STORAGE_ROOT (default ./data)."""

    def __init__(self, storage_root: PathLike):
        self.storage_root = Path(storage_root).resolve()

    def normalize_path(self, *parts: str) -> str:
        """Return a repo-relative POSIX path such as data/raw/mrms/reflectivity/file.stub."""
        cleaned = [part.strip("/") for part in parts if part]
        inner = "/".join(cleaned)
        if inner.startswith("data/"):
            return inner
        return f"data/{inner}"

    def absolute_path(self, repo_relative_path: str) -> Path:
        relative = repo_relative_path.removeprefix("data/").lstrip("/")
        return self.storage_root / relative

    def ensure_directories(self, *repo_relative_dirs: str) -> None:
        for repo_relative in repo_relative_dirs:
            self.absolute_path(repo_relative).mkdir(parents=True, exist_ok=True)

    def ensure_storage_layout(self) -> None:
        self.ensure_directories("data/raw", "data/processed", "data/tiles")

    def path_exists(self, repo_relative_path: str) -> bool:
        return self.absolute_path(repo_relative_path).exists()

    def write_bytes(self, repo_relative_path: str, data: bytes, *, overwrite: bool = False) -> str:
        normalized = self.normalize_path(repo_relative_path)
        target = self.absolute_path(normalized)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and not overwrite:
            return normalized
        target.write_bytes(data)
        return normalized

    def write_text(self, repo_relative_path: str, text: str, *, overwrite: bool = False) -> str:
        return self.write_bytes(repo_relative_path, text.encode("utf-8"), overwrite=overwrite)

    def sha256(self, repo_relative_path: str) -> str:
        target = self.absolute_path(self.normalize_path(repo_relative_path))
        digest = hashlib.sha256()
        digest.update(target.read_bytes())
        return digest.hexdigest()

    def mrms_reflectivity_paths(self, timestamp: str) -> tuple[str, str]:
        token = timestamp.replace(":", "").replace("-", "")
        raw_path = self.normalize_path("raw", "mrms", "reflectivity", f"{token}.grib2.stub")
        processed_path = self.normalize_path("processed", "mrms", "reflectivity", f"{token}.png.stub")
        return raw_path, processed_path
