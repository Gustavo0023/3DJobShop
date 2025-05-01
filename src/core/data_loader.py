# Datei: src/core/data_loader.py
import os, pandas as pd

BASE_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),  # .../3DJobShop/src/core
        os.pardir,                   # .../3DJobShop/src
        os.pardir,                   # .../3DJobShop
        "Excel"                      # .../3DJobShop/Excel
    )
)

def load_materials(filename: str) -> list[str]:
    path = os.path.join(BASE_DIR, filename)
    df = pd.read_excel(path)
    return df["Material"].dropna().tolist()

def load_process_data(filename: str) -> tuple[list[str], pd.DataFrame]:
    path = os.path.join(BASE_DIR, filename)
    df = pd.read_excel(path, header=4)
    df.columns = [c.strip() for c in df.columns]
    df = df[df["Beschreibung"].notna()]
    return df["Beschreibung"].tolist(), df
