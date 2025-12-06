from dataclasses import dataclass

@dataclass
class Image:
    b64: str
    filename: str
    mime_type: str