import re
from typing import List

def detect_red_flags(user_text: str) -> List[str]:
    """Conservative red flag detector for raw user text (adapter-level).
    Not used by golden-case evaluation (which is structured state-first)."""
    text = (user_text or "").lower().strip()
    if not text:
        return []
    flags: List[str] = []
    if re.search(r"\b(suicide|kill myself|end my life|self harm|hurt myself)\b", text):
        flags.append("RED_FLAG_SELF_HARM")
    if re.search(r"\b(chest pain|pressure in chest|can't breathe|shortness of breath|fainting|passed out)\b", text):
        flags.append("RED_FLAG_ACUTE_CARDIORESP")
    if re.search(r"\b(face droop|slurred speech|one side weak|sudden weakness|stroke)\b", text):
        flags.append("RED_FLAG_NEURO")
    if re.search(r"\b(erection.*(4 hours|four hours)|priapism)\b", text):
        flags.append("RED_FLAG_PRIAPISM")
    if re.search(r"\b(severe pain|unbearable pain|bleeding a lot|heavy bleeding)\b", text):
        flags.append("RED_FLAG_SEVERE_PAIN_BLEEDING")
    return flags
