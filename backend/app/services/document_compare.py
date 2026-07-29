"""Safe textual comparison for already-extracted official document text."""
from difflib import unified_diff

def compare_text(base_text: str, compared_text: str) -> dict:
    if not base_text or not compared_text:
        return {"status": "insufficient_content", "diff": []}
    diff = list(unified_diff(
        base_text.splitlines(), compared_text.splitlines(),
        fromfile="documento_base", tofile="documento_comparado", lineterm=""
    ))
    return {"status": "compared", "diff": diff, "changed": bool(diff)}
