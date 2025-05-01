import streamlit as st
import sys, os
from io import BytesIO
from email_validator import validate_email, EmailNotValidError

# src-Ordner ins PYTHONPATH aufnehmen
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

#from core.parser import load_mesh_from_file
from core.data_loader import load_materials
from core.notifier import send_order_email

# Maximale Dateigröße in Bytes (20 MB)
MAX_FILE_SIZE = 20 * 1024 * 1024

# Excel-Dateinamen
MATERIAL_PULVER_XLSX = "LMD_Materialliste_Pulver.xlsx"
MATERIAL_DRAHT_XLSX  = "LMD_Materialliste_Draht.xlsx"

# Materiallisten laden
try:
    pulver_materials = load_materials(MATERIAL_PULVER_XLSX)
except FileNotFoundError:
    st.error(f"Pulver-Materialliste nicht gefunden: {MATERIAL_PULVER_XLSX}")
    pulver_materials = []
try:
    draht_materials = load_materials(MATERIAL_DRAHT_XLSX)
except FileNotFoundError:
    st.error(f"Draht-Materialliste nicht gefunden: {MATERIAL_DRAHT_XLSX}")
    draht_materials = []

st.set_page_config(page_title="3D-Druck Angebotsportal", layout="centered")
st.title("3D-JobShop")

# 1) Auftragsspezifikation
st.markdown("---")
st.header("Auftragsspezifikation")
aub = st.radio(
    "Auftragstyp auswählen:",
    ["3D-Druck Neuproduktion", "3D-Druck Reparatur", "Beschichtung"]
)

# Beschichtungsdicke nur bei Beschichtung
dicht = None
if aub == "Beschichtung":
    st.markdown("---")
    st.header("Beschichtungsdicke (mm)")
    dicht = st.number_input(
        "Gewünschte Beschichtungsdicke in mm",
        min_value=0.01,
        value=0.1,
        step=0.01
    )

# 2) Stückzahl
st.markdown("---")
st.header("Stückzahl")
anzahl = st.number_input("Stückzahl", min_value=1, value=1, step=1)

# 3) Materialtyp auswählen
st.markdown("---")
st.header("Materialtyp")
mat_typ = st.radio("Materialtyp auswählen", ["Pulver", "Draht"])
options = (pulver_materials if mat_typ == "Pulver" else draht_materials) + ["Andere"]
material = st.selectbox("Material auswählen", options)
desired_material = None
if material == "Andere":
    desired_material = st.text_input("Bitte geben Sie Ihr Material an")
    if not desired_material.strip():
        st.error("Bitte geben Sie Ihr Material im Textfeld an.")

# 4) Beschreibung
st.markdown("---")
st.header("Beschreibung")
beschreibung = st.text_area(
    "Bitte beschreiben Sie Ihre Vorgaben so präzise wie möglich."
)

# 5) Upload oder Einsendung
st.markdown("---")
st.header("3D-Datei hochladen oder Einsendung")
send_physical = st.checkbox(
    "Möchten Sie Ihr Bauteil einschicken, damit wir einen 3D-Scan erstellen?"
)

uploaded_file = None
if not send_physical:
    uploaded_file = st.file_uploader(
        "Datei auswählen (STL, STEP, SPT)",
        type=["stl", "step", "stp"]
    )
    if uploaded_file and uploaded_file.size > MAX_FILE_SIZE:
        st.error("Datei überschreitet die maximal erlaubte Größe von 20 MB.")
        uploaded_file = None
else:
    st.info(
        "Sie haben die Einsendungsoption gewählt. "
        "Bitte senden Sie Ihr Bauteil an:\n"
        "Sato Maschinenbau GmbH & Co. KG nach Auftragsbestätigung."
    )

# 6) Zusätzliche Anhänge (optional)
st.markdown("---")
st.header("Zusätzliche Anhänge (optional)")
additional_files = st.file_uploader(
    "Wählen Sie bis zu 5 Dateien als Anhang aus",
    type=None,
    accept_multiple_files=True
)
# Limit auf 5 Dateien
if additional_files and len(additional_files) > 5:
    st.error("Maximal 5 Anhänge erlaubt – die ersten 5 werden verwendet.")
    additional_files = additional_files[:5]

# Größencheck
valid_additional = []
if additional_files:
    for f in additional_files:
        if f.size > MAX_FILE_SIZE:
            st.warning(f"'{f.name}' ({f.size/1024/1024:.1f} MB) ist zu groß und wird entfernt.")
        else:
            valid_additional.append(f)
    additional_files = valid_additional

# 7) Kontaktdaten
st.markdown("---")
st.header("Kontaktdaten")
name    = st.text_input("Name")
firma   = st.text_input("Firma")
email   = st.text_input("E-Mail")
telefon = st.text_input("Telefon (optional)")

# 8) Absenden
st.markdown("---")
if st.button("Absenden"):
    errors = []

    # Pflichtfelder
    if not aub:
        errors.append("Bitte wählen Sie eine Auftragsart aus.")
    if not send_physical and not uploaded_file:
        errors.append("Bitte laden Sie eine 3D-Datei hoch oder wählen Sie die Einsendungsoption.")
    if not name.strip():
        errors.append("Bitte geben Sie Ihren Namen an.")
    if not firma.strip():
        errors.append("Bitte geben Sie Ihre Firma an.")
    if not email.strip():
        errors.append("Bitte geben Sie Ihre E-Mail-Adresse an.")
    else:
        # E-Mail-Format validieren
        try:
            valid = validate_email(email)
            email = valid.email  # ggf. normalisierte Adresse
        except EmailNotValidError as e:
            errors.append(f"E-Mail ungültig: {e}")

    if material == "Andere" and (desired_material is None or not desired_material.strip()):
        errors.append("Bitte geben Sie Ihr Material an.")

    # Fehlermeldungen anzeigen
    if errors:
        for err in errors:
            st.error(err)
    else:
        st.success("Daten erfasst. Weiterleitung erfolgt...")
        # Dateien lesen
        file_bytes = uploaded_file.read() if uploaded_file else None
        buffer     = BytesIO(file_bytes) if file_bytes else None

        # Zusätzliche Anhänge lesen
        add_bytes_list = []
        add_names_list = []
        if additional_files:
            for f in additional_files:
                data = f.read()
                add_bytes_list.append(data)
                add_names_list.append(f.name)

        try:
            """ volume = area = None
            # Volumen & Fläche nur bei Neuproduktion mit Datei
            if aub == "3D-Druck Neuproduktion" and buffer:
                mesh = load_mesh_from_file(buffer, uploaded_file.name)
                volume = mesh.volume
                area   = mesh.area
                st.write("**Volumen:**", f"{volume:.2f} mm³")
                st.write("**Fläche:**", f"{area:.2f} mm²") """

            # Daten zusammenstellen
            mat_selected = desired_material if material == "Andere" else material
            order_data = {
                "auftragstyp": aub,
                "anzahl": anzahl,
                "materialtyp": mat_typ,
                "material": mat_selected,
                "beschichtungsdicke_mm": dicht,
                "beschreibung": beschreibung,
                "name": name,
                "firma": firma,
                "email": email,
                "telefon": telefon,
                "dateiname": uploaded_file.name if uploaded_file else None,
                "einsendung": send_physical,
               #"volumen_mm3": volume,
               #"area_mm2": area
            }

            # E-Mail versenden
            send_order_email(
                order_data=order_data,
                attachment_bytes=file_bytes,
                attachment_name=uploaded_file.name if uploaded_file else None,
                additional_bytes_list=add_bytes_list,
                additional_names_list=add_names_list
            )
            st.success("✅ E-Mail wurde versendet.")
        except Exception as e:
            st.error(f"Fehler beim Versand: {e}")
