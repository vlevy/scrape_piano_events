from __future__ import annotations

import io
import os
import tarfile
from pathlib import Path
from typing import Dict, Tuple

import torch
from sentence_transformers import SentenceTransformer

_MODEL: torch.nn.Module | None = None
_ENCODER: SentenceTransformer | None = None
_TAG_TO_IDX: Dict[str, int] | None = None


def _load_bundle(path: Path) -> Dict:
    """Return the deserialized state bundle from either *.pt or *.tar.gz."""
    if path.suffixes[-2:] == [".tar", ".gz"]:
        # model.tar.gz → extract model.pt in memory
        with tarfile.open(path, mode="r:gz") as tar:
            with tar.extractfile("model.pt") as fp:  # type: ignore[arg-type]
                assert fp is not None, "model.pt not found in archive"
                buffer = io.BytesIO(fp.read())
        return torch.load(buffer, map_location="cpu")

    # Fallback: expect a raw model.pt
    return torch.load(path, map_location="cpu")


def load_model(
    path: str | Path = "suggesting/model.tar.gz",
) -> Tuple[
    torch.nn.Module,
    SentenceTransformer,
    Dict[str, int],
]:
    """Load the MLP and sentence encoder, caching them for reuse."""
    global _MODEL, _ENCODER, _TAG_TO_IDX

    if _MODEL is None:
        print("CWD:", os.getcwd())
        bundle = _load_bundle(Path(path))

        _TAG_TO_IDX = bundle["tag_to_idx"]

        _MODEL = torch.nn.Sequential(
            torch.nn.Linear(384, 256),
            torch.nn.ReLU(),
            torch.nn.Dropout(0.2),
            torch.nn.Linear(256, len(_TAG_TO_IDX)),
        )
        _MODEL.load_state_dict(bundle["state_dict"])
        _MODEL.eval()

        _ENCODER = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")

    # mypy-friendly: _MODEL etc. are non-None here
    return _MODEL, _ENCODER, _TAG_TO_IDX  # type: ignore[return-value]
