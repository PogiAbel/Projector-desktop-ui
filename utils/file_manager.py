import os
from pathlib import Path

def find_books() -> list[str]:
    """Find sql databases in database/books | returns their name without extension"""
    path = Path(__file__).parent.parent / "database" / "books"
    files = os.listdir(path)
    return [f.split(".")[0] for f in files]