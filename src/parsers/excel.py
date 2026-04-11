import pandas as pd
from pathlib import Path


def parse_excel(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".csv":
        df = pd.read_csv(path)
    else:
        df = pd.read_excel(path)
    return df.to_string(index=False)
