# src/parsers/stp_parser.py

import trimesh
from io import BytesIO

def load_and_validate_stp(file_buffer: BytesIO) -> trimesh.Trimesh:
    """
    Lädt eine STEP/STP-Datei aus einem BytesIO-Buffer, prüft,
    ob sie lesbar ist, und gibt ein zusammengefasstes Mesh zurück.
    Wirft eine RuntimeError bei Problemen.
    """
    try:
        # STEP-Dateien können als 'step' oder 'stp' übergeben werden
        scene = trimesh.load(file_buffer, file_type='step')
        # Wenn die Szene mehrere Meshes enthält, alle zusammenfügen
        if hasattr(scene, 'geometry'):
            # bei neueren trimesh-Versionen: scene.dump() gibt Liste von Meshes
            meshes = scene.dump() if hasattr(scene, 'dump') else scene.geometry.values()
            mesh = trimesh.util.concatenate(meshes)
        else:
            mesh = scene
        # Einfache Plausibilitätsprüfung
        if mesh.is_empty:
            raise ValueError("Mesh ist leer oder ungültig.")
        return mesh
    except Exception as e:
        raise RuntimeError(f"Fehler beim Laden der STEP-Datei: {e}")
