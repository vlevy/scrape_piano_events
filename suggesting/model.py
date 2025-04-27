from pathlib import Path

import torch
from sentence_transformers import SentenceTransformer

_MODEL = None
_ENCODER = None
_TAG_TO_IDX = None

def load_model(path: Path | str = "model/model.pt"):
    global _MODEL, _ENCODER, _TAG_TO_IDX
    if _MODEL is None:
        bundle = torch.load(path, map_location="cpu")
        _TAG_TO_IDX = bundle["tag_to_idx"]

        _MODEL = torch.nn.Sequential(
            torch.nn.Linear(768, 256),
            torch.nn.ReLU(),
            torch.nn.Dropout(0.2),
            torch.nn.Linear(256, len(_TAG_TO_IDX)),
        )
        _MODEL.load_state_dict(bundle["state_dict"])
        _MODEL.eval()

        _ENCODER = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
    return _MODEL, _ENCODER, _TAG_TO_IDX
