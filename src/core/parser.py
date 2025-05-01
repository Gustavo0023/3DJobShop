# Datei: src/core/parser.py
import os
import tempfile
from io import BytesIO
import trimesh

from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.IFSelect import IFSelect_RetDone
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
from OCC.Core.StlAPI import StlAPI_Writer


def load_mesh_from_file(buffer: BytesIO, filename: str) -> trimesh.Trimesh:
    """
    Erzeugt ein Trimesh-Mesh aus STEP/STEP- oder STL-Daten basierend auf der Dateierweiterung.
    """
    ext = os.path.splitext(filename.lower())[1]
    if ext in (".stp", ".step"):
        return load_mesh_from_step(buffer)
    elif ext == ".stl":
        try:
            mesh = trimesh.load(buffer, file_type="stl")
            if mesh.is_empty:
                raise RuntimeError("Mesh ist leer oder ungültig.")
            return mesh
        except Exception as e:
            raise RuntimeError(f"Fehler beim Laden der STL-Datei: {e}")
    else:
        raise RuntimeError(f"Unbekanntes Dateiformat: {ext}")


def load_mesh_from_step(buffer: BytesIO) -> trimesh.Trimesh:
    """
    Lädt eine STEP-Datei aus dem Buffer, trianguliert sie via OpenCascade,
    schreibt sie temporär als STL und lädt sie mit trimesh.
    """
    # 1) Buffer in temporäre STEP-Datei schreiben
    with tempfile.NamedTemporaryFile(delete=False, suffix=".stp") as tmp_step:
        tmp_step.write(buffer.read())
        tmp_step.flush()
        step_path = tmp_step.name

    # 2) STEP-Datei laden
    reader = STEPControl_Reader()
    status = reader.ReadFile(step_path)
    if status != IFSelect_RetDone:
        raise RuntimeError("STEP-Datei konnte nicht gelesen werden.")
    # Alle Root-Shapes übertragen
    for i in range(1, reader.NbRootsForTransfer() + 1):
        reader.TransferRoot(i)
    shape = reader.Shape()

    # 3) Triangulation erzwingen
    mesh_builder = BRepMesh_IncrementalMesh(shape, 0.1)
    mesh_builder.Perform()

    # 4) Export als STL
    stl_file = tempfile.NamedTemporaryFile(delete=False, suffix=".stl").name
    writer = StlAPI_Writer()
    writer.SetASCIIMode(False)
    writer.Write(shape, stl_file)

    # 5) Mit trimesh laden
    try:
        mesh = trimesh.load(stl_file, file_type="stl", process=False)
        if mesh.is_empty:
            raise RuntimeError("Mesh ist leer oder ungültig nach Konvertierung.")
        return mesh
    except Exception as e:
        raise RuntimeError(f"Fehler beim Laden der STL: {e}")
