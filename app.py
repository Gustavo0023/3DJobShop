import streamlit as st
import sys, os
from io import BytesIO
from email_validator import validate_email, EmailNotValidError

# Page configuration must be set first
st.set_page_config(
    page_title="3D-JobShop Angebotsportal",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# add src to PATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

# data and notifier imports
from core.data_loader import load_materials
from core.notifier import send_order_email

# constants
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB
MATERIAL_PULVER_XLSX = "LMD_Materialliste_Pulver.xlsx"
MATERIAL_DRAHT_XLSX  = "LMD_Materialliste_Draht.xlsx"

# -- Sidebar for progress --
st.sidebar.title("🛠️ Dein 3D-JobShop")
st.sidebar.markdown("###### Dein Weg zum Bauteil in 7 Schritten")
p_steps = ["Auftragsspezifikation", "Beschichtungsdicke", "Stückzahl", "Material", "Beschreibung", "Datei-Upload", "Kontaktdaten"]
for step in p_steps:
    st.sidebar.markdown(f"- {step}")
# Footer powered by Sato
st.sidebar.markdown("---")
st.sidebar.caption("Lunovu – powered by Sato")

from pathlib import Path

with st.sidebar.expander("ℹ️ Impressum"):
    st.markdown(Path("Impressum.md").read_text(encoding="utf-8"), unsafe_allow_html=True)

with st.sidebar.expander("🔒 Datenschutz"):
    st.markdown(Path("Datenschutz.md").read_text(encoding="utf-8"), unsafe_allow_html=True)

with st.sidebar.expander("🍪 Cookie-Hinweis"):
    st.markdown(Path("Cookies.md").read_text(encoding="utf-8"), unsafe_allow_html=True)

with st.sidebar.expander("📄 AGB"):
    st.markdown(Path("AGB.md").read_text(encoding="utf-8"), unsafe_allow_html=True)


# -- Hero Section --
st.markdown("""
<div style="text-align:center; padding:20px 0;">
  <h1 style="color:#0066CC; margin:20px 0;">Willkommen bei 3D-JobShop 🚀</h1>
  <p style="font-size:18px;">Lade Deine Datei hoch, wähle Deine Optionen und erhalte in Kürze Dein Angebot &ndash; schnell, zuverlässig, einfach!</p>
</div>
""", unsafe_allow_html=True)
st.markdown("---")

# Load materials
pulver_materials, draht_materials = [], []
try:
    pulver_materials = load_materials(MATERIAL_PULVER_XLSX)
except FileNotFoundError:
    st.warning("⚠️ Pulver-Materialliste nicht gefunden.")
try:
    draht_materials = load_materials(MATERIAL_DRAHT_XLSX)
except FileNotFoundError:
    st.warning("⚠️ Draht-Materialliste nicht gefunden.")

# -- Form starts --
with st.form(key="order_form", clear_on_submit=False):
    st.subheader("Auftragsspezifikation")
    aub = st.radio("Wähle den Auftragstyp:", ["Neuproduktion", "Reparatur", "Beschichtung"], index=0)

    st.subheader("Beschichtungsdicke (optional)")
    dicht = None
    if aub == "Beschichtung":
        dicht = st.slider(
            "Dicke in mm:", min_value=0.01, max_value=5.0, value=0.1, step=0.01,
            help="Wie dick soll die Schicht werden?"
        )

    st.subheader("Stückzahl")
    anzahl = st.number_input(
        "Anzahl der Teile:", min_value=1, value=1, step=1,
        help="Wie viele Teile benötigst Du?"
    )

    st.subheader("Material")
    mat_typ = st.selectbox(
        "Materialart:", ["Pulver", "Draht"],
        help="Wähle Pulver oder Draht."
    )
    options = (pulver_materials if mat_typ == "Pulver" else draht_materials) + ["Anderes Material"]
    material = st.selectbox(
        "Material wählen:", options,
        help="Wähle aus unserem Lager oder gib Dein Spezialmaterial an."
    )
    desired_material = None
    if material == "Anderes Material":
        desired_material = st.text_input(
            "Spezifiziere Dein Material:", placeholder="z.B. Titan-Legierung"
        )

    st.subheader("Beschreibung")
    beschreibung = st.text_area(
        "Genauere Angaben:", placeholder="Welche Toleranzen, Oberflächen oder Besonderheiten?"
    )

    st.subheader("Datei-Upload")
    send_physical = st.checkbox("Bauteil physisch einschicken? 📦")
    uploaded_file = None
    if not send_physical:
        uploaded_file = st.file_uploader(
            "STL, STEP oder SPT hier hochladen:", type=None,
            help="Zieh Deine Datei hierher oder klick zum Auswählen."
        )
        if uploaded_file:
            name_lower = uploaded_file.name.lower()
            if not name_lower.endswith((".stl", ".step", ".stp")):
                st.error("Nur .stl, .step oder .stp erlaubt.")
                uploaded_file = None
            elif uploaded_file.size > MAX_FILE_SIZE:
                st.error("Maximal 20 MB pro Datei.")
                uploaded_file = None
    else:
        st.info("Bitte Dein Bauteil nach Bestätigung an Sato Maschinenbau schicken.")

    st.subheader("Zusätzliche Anhänge (optional)")
    additional_files = st.file_uploader(
        "Weitere Anhänge (bis 5 Dateien):", accept_multiple_files=True
    )
    if additional_files and len(additional_files) > 5:
        st.warning("Nur die ersten 5 Dateien werden übernommen.")
        additional_files = additional_files[:5]

    # Contact & submit
    st.markdown("---")
    st.subheader("Kontakt & Angebot anfordern ✉️")
    name = st.text_input("Name:", placeholder="Max Mustermann")
    firma = st.text_input("Firma:", placeholder="Muster GmbH")
    email = st.text_input("E-Mail:", placeholder="deine@firma.de")
    telefon = st.text_input("Telefon (optional):", placeholder="+49 123 4567890")
    submit_button = st.form_submit_button(label="Angebot anfordern 🚀")

    if submit_button:
        errors = []
        if not aub:
            errors.append("Bitte wähle einen Auftragstyp.")
        if not send_physical and not uploaded_file:
            errors.append("Bitte lade eine 3D-Datei hoch oder wähle Einschicken.")
        if not name:
            errors.append("Name ist erforderlich.")
        if not firma:
            errors.append("Firma ist erforderlich.")
        try:
            validate_email(email)
        except EmailNotValidError:
            errors.append("Ungültige E-Mail-Adresse.")
        if material == "Anderes Material" and not desired_material:
            errors.append("Bitte gib Dein spezielles Material an.")

        if errors:
            for err in errors:
                st.error(err)
        else:
            st.success("👍 Deine Anfrage ist unterwegs – wir melden uns umgehend!")
            file_bytes = uploaded_file.read() if uploaded_file else None
            add_bytes = [f.read() for f in additional_files] if additional_files else []
            add_names = [f.name for f in additional_files] if additional_files else []

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
                st.error(f"E-Mail-Versand fehlgeschlagen: {e}")
