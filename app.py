import streamlit as st
import sys, os
from io import BytesIO
from email_validator import validate_email, EmailNotValidError

# set_page_config must be the first Streamlit command
st.set_page_config(page_title="3D-Druck Angebotsportal", layout="wide")

# src-Ordner ins PYTHONPATH aufnehmen
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

# from core.parser import load_mesh_from_file  # Removed in v2
from core.data_loader import load_materials
from core.notifier import send_order_email

# Maximale Dateigröße in Bytes (20 MB)
MAX_FILE_SIZE = 20 * 1024 * 1024

# Excel-Dateinamen
MATERIAL_PULVER_XLSX = os.path.join("Excel", "LMD_Materialliste_Pulver.xlsx")
MATERIAL_DRAHT_XLSX  = os.path.join("Excel", "LMD_Materialliste_Draht.xlsx")

# Hero Section
st.image("assets/hero.jpg", use_column_width=True)
st.title("Willkommen bei 3D-JobShop 🚀")
st.subheader("Dein schneller Weg zum perfekten Bauteil – einfach Datei hochladen und Angebot erhalten!")
# Trust Badge
st.markdown("**ISO-zertifiziert** | ⭐⭐⭐⭐⭐ Kundenzufriedenheit")
st.markdown("---")

# Load material lists
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

# 1) Auftragsspezifikation
st.subheader("Schritt 1/7: 🏷️ Auftragsspezifikation")
aub = st.radio(
    "Auftragstyp auswählen:",
    ["3D-Druck Neuproduktion", "3D-Druck Reparatur", "Beschichtung"]
)

# 2) Beschichtungsdicke nur bei Beschichtung
dicht = None
if aub == "Beschichtung":
    st.subheader("Schritt 2/7: 🖌️ Beschichtungsdicke (mm)")
    dicht = st.number_input(
        "Gewünschte Beschichtungsdicke in mm",
        min_value=0.01,
        value=0.1,
        step=0.01,
        help="Wie dick soll die Schicht werden?"
    )

# 3) Stückzahl
st.subheader("Schritt 3/7: 📦 Stückzahl")
anzahl = st.number_input(
    "Stückzahl",
    min_value=1,
    value=1,
    step=1,
    help="Wie viele Teile benötigst Du?"
)

# 4) Materialtyp auswählen
st.subheader("Schritt 4/7: 🔧 Materialtyp")
mat_typ = st.radio("Materialtyp auswählen", ["Pulver", "Draht"])
options = (pulver_materials if mat_typ == "Pulver" else draht_materials) + ["Andere"]
material = st.selectbox(
    "Material auswählen", options,
    help="Wähle aus unserem Lager oder gib Dein Spezialmaterial an."
)
desired_material = None
if material == "Andere":
    desired_material = st.text_input(
        "Eigenes Material:",
        placeholder="z.B. Titan-Legierung"
    )

# 5) Beschreibung
st.subheader("Schritt 5/7: 📝 Beschreibung")
beschreibung = st.text_area(
    "Bitte beschreibe Deine Vorgaben:",
    placeholder="Welche Toleranzen, Oberflächen oder Besonderheiten?"
)

# 6) Upload oder Einsendung
st.subheader("Schritt 6/7: 📂 3D-Datei hochladen")
send_physical = st.checkbox(
    "Ich möchte mein Bauteil einschicken für 3D-Scan"
)

uploaded_file = None
if not send_physical:
    uploaded_file = st.file_uploader(
        "Datei auswählen (STL, STEP, SPT)",
        type=None,
        help="Zieh Deine Datei hierher oder klick zum Auswählen."
    )
    if uploaded_file:
        name_lower = uploaded_file.name.lower()
        if not name_lower.endswith((".stl", ".step", ".stp")):
            st.error("Nur STL, STEP oder SPT erlaubt.")
            uploaded_file = None
        elif uploaded_file.size > MAX_FILE_SIZE:
            st.error("Maximal 20 MB pro Datei.")
            uploaded_file = None
else:
    st.info("Bitte sende Dein Bauteil nach Auftragsbestätigung an Sato Maschinenbau GmbH & Co. KG.")

# 7) Zusätzliche Anhänge
st.subheader("Schritt 7/7: 📎 Zusätzliche Anhänge (optional)")
additional_files = st.file_uploader(
    "Weitere Dateien anhängen",
    type=None,
    accept_multiple_files=True
)
if additional_files and len(additional_files) > 5:
    st.warning("Maximal 5 Anhänge – die ersten 5 werden übernommen.")
    additional_files = additional_files[:5]

valid_additional = []
for f in additional_files or []:
    if f.size <= MAX_FILE_SIZE:
        valid_additional.append(f)
    else:
        st.warning(f"'{f.name}' ist zu groß und wurde entfernt.")
additional_files = valid_additional

# Kontaktformular & Absenden
st.markdown("---")
with st.form("order_form"):
    st.subheader("Deine Kontaktdaten & Absenden")
    name = st.text_input("Name", placeholder="Max Mustermann")
    firma = st.text_input("Firma", placeholder="z.B. Muster GmbH")
    email = st.text_input("E-Mail", placeholder="deine@firma.de")
    telefon = st.text_input("Telefon (optional)", placeholder="z.B. +49 123 4567890")
    submitted = st.form_submit_button("Angebot anfordern 🚀")

    if submitted:
        errors = []
        if not aub:
            errors.append("Auftragstyp fehlt.")
        if not send_physical and not uploaded_file:
            errors.append("Bitte 3D-Datei hochladen oder Einsendungsoption wählen.")
        if not name:
            errors.append("Name eingeben.")
        if not firma:
            errors.append("Firma eingeben.")
        try:
            validate = validate_email(email)
            email = validate.email
        except EmailNotValidError:
            errors.append("Ungültige E-Mail-Adresse.")
        if material == "Andere" and not desired_material:
            errors.append("Material angeben.")

        if errors:
            for e in errors:
                st.error(e)
        else:
            st.success("👍 Deine Anfrage ist raus – wir melden uns in Kürze!")
            # Dateien verarbeiten und E-Mail versenden
            file_bytes = uploaded_file.read() if uploaded_file else None
            add_bytes = [f.read() for f in additional_files]
            add_names = [f.name for f in additional_files]

            order_data = {
                "auftragstyp": aub,
                "anzahl": anzahl,
                "materialtyp": mat_typ,
                "material": desired_material or material,
                "beschichtungsdicke_mm": dicht,
                "beschreibung": beschreibung,
                "name": name,
                "firma": firma,
                "email": email,
                "telefon": telefon,
                "dateiname": uploaded_file.name if uploaded_file else None,
                "einsendung": send_physical
            }
            try:
                send_order_email(
                    order_data=order_data,
                    attachment_bytes=file_bytes,
                    attachment_name=uploaded_file.name if uploaded_file else None,
                    additional_bytes_list=add_bytes,
                    additional_names_list=add_names
                )
            except Exception as e:
                st.error(f"Fehler beim Versand: {e}")
