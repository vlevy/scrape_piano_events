import numpy as np
import torch

from .model import load_model


def _text_from_fields(rec: dict) -> str:
    return (
        f"[TITLE] {rec['post_title']} "
        f"[VENUE] {rec['venue_name']} "
        f"[ORG] {rec['organizer_name']} "
        f"[CONTENT] {rec['post_content']}"
    )

def suggest_tags(event: dict, top_k=5, threshold=0.25):
    model, encoder, tag_to_idx = load_model()
    idx_to_tag = {i: t for t, i in tag_to_idx.items()}

    emb = encoder.encode(_text_from_fields(event), convert_to_tensor=True)
    with torch.no_grad():
        probs = torch.sigmoid(model(emb)).numpy()

    pairs = [(idx_to_tag[i], float(p)) for i, p in enumerate(probs) if p >= threshold]
    pairs.sort(key=lambda x: x[1], reverse=True)
    return pairs[:top_k]
