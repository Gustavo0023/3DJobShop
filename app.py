import streamlit as st
import streamlit.components.v1 as components
import sys, os
from io import BytesIO
from pathlib import Path
from email_validator import validate_email, EmailNotValidError

# Page configuration must be set first
st.set_page_config(
    page_title="3D-JobShop Angebotsportal",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Cookie-Hinweis oben als Inline-Popup
if "cookies_accepted" not in st.session_state:
    col1, col2 = st.columns([8,1])
    with col1:
        st.info("Wir verwenden Cookies für Sitzungs-Handling und anonyme Analyse.")
    with col2:
        if st.button("Akzeptieren", key="cookie_btn"):
            st.session_state["cookies_accepted"] = True
            st.experimental_rerun()  # sofort neu rendern, Banner verschwindet
    # kein st.stop(), App bleibt bedienbar

# Add src to PATH für eigene Module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from core.data_loader import load_materials
from core.notifier import send_order_email

# Konstanten
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB
MATERIAL_PULVER_XLSX = "LMD_Materialliste_Pulver.xlsx"
MATERIAL_DRAHT_XLSX  = "LMD_Materialliste_Draht.xlsx"

# Sidebar-Navigation
st.sidebar.title("🛠️ Dein 3D-JobShop")
st.sidebar.markdown("###### Dein Weg zum Bauteil in 7 Schritten")
p_steps = ["Auftragsspezifikation", "Beschichtungsdicke", "Stückzahl", "Material", "Beschreibung", "Datei-Upload", "Kontaktdaten"]
for step in p_steps:
    st.sidebar.markdown(f"- {step}")
st.sidebar.markdown("---")
st.sidebar.caption("Lunovu – powered by Sato")
st.sidebar.markdown("[🌐 Zur Hauptseite von Sato](https://www.sato.de)", unsafe_allow_html=True)

# Rechtstexte im Sidebar
with st.sidebar.expander("ℹ️ Impressum"):
    st.markdown(Path("Impressum.md").read_text(encoding="utf-8"), unsafe_allow_html=True)
with st.sidebar.expander("🔒 Datenschutz"):
    st.markdown(Path("Datenschutz.md").read_text(encoding="utf-8"), unsafe_allow_html=True)
with st.sidebar.expander("🍪 Cookie-Hinweis"):
    st.markdown(Path("Cookies.md").read_text(encoding="utf-8"), unsafe_allow_html=True)
with st.sidebar.expander("📄 AGB"):
    st.markdown(Path("AGB.md").read_text(encoding="utf-8"), unsafe_allow_html=True)

# Hero Section
st.markdown("""
<div style="text-align:center; padding:20px 0;">
  <h1 style="color:#0066CC; margin:20px 0;">Willkommen bei 3D-JobShop</h1>
  <p style="font-size:18px;">Lade Deine Datei hoch, wähle Deine Optionen und erhalte in Kürze Dein Angebot – schnell, zuverlässig, einfach!</p>
</div>
""", unsafe_allow_html=True)
st.markdown("---")

# Materialien laden
pulver_materials, draht_materials = [], []
try:
    pulver_materials = load_materials(MATERIAL_PULVER_XLSX)
except FileNotFoundError:
    st.warning(f"⚠️ Pulver-Materialliste nicht gefunden: {MATERIAL_PULVER_XLSX}")
try:
    draht_materials = load_materials(MATERIAL_DRAHT_XLSX)
except FileNotFoundError:
    st.warning(f"⚠️ Draht-Materialliste nicht gefunden: {MATERIAL_DRAHT_XLSX}")

# Auftragsformular
with st.form("order_form", clear_on_submit=False):
    st.subheader("Auftragsspezifikation")
    aub = st.radio("Wähle den Auftragstyp:", ["Neuproduktion", "Reparatur", "Beschichtung"], index=0)

    st.subheader("Beschichtungsdicke (optional)")
    dicht = st.slider("Dicke in mm:", 0.01, 5.0, 0.1, step=0.01) if aub == "Beschichtung" else None

    st.subheader("Stückzahl")
    anzahl = st.number_input("Anzahl der Teile:", min_value=1, value=1, step=1)

    st.subheader("Material")
    mat_typ = st.selectbox("Materialart:", ["Pulver", "Draht"])
    options = (pulver_materials if mat_typ == "Pulver" else draht_materials) + ["Anderes Material"]
    material = st.selectbox("Material auswählen:", options)
    desired_material = st.text_input("Spezifiziere Dein Material:") if material == "Anderes Material" else None

    st.subheader("Beschreibung")
    beschreibung = st.text_area("Genauere Angaben:")

    st.subheader("Datei-Upload")
    send_physical = st.checkbox("Bauteil physisch einschicken? 📦")
    uploaded_file = st.file_uploader("STL, STEP oder SPT hier hochladen:", type=["stl","step","stp"]) if not send_physical else None
    if uploaded_file and uploaded_file.size > MAX_FILE_SIZE:
        st.error("Maximal 20 MB pro Datei.")
        uploaded_file = None

    st.subheader("Zusätzliche Anhänge (optional)")
    additional_files = st.file_uploader("Weitere Anhänge (bis 5 Dateien):", accept_multiple_files=True)
    if additional_files and len(additional_files) > 5:
        st.warning("Nur die ersten 5 Dateien werden übernommen.")
        additional_files = additional_files[:5]

    st.markdown("---")
    st.subheader("Kontakt & Angebot anfordern ✉️")
    name = st.text_input("Name:")
    firma = st.text_input("Firma:")
    email = st.text_input("E-Mail:")
    telefon = st.text_input("Telefon (optional):")
    submitted = st.form_submit_button("Angebot anfordern 🚀")

    if submitted:
        errors = []
        if not name:
            errors.append("Name ist erforderlich.")
        if not firma:
            errors.append("Firma ist erforderlich.")
        try:
            validate_email(email)
        except Exception:
            errors.append("Ungültige E-Mail-Adresse.")
        if not send_physical and not uploaded_file:
            errors.append("Bitte lade eine 3D-Datei hoch oder wähle Einschicken.")
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
                send_order_email(order_data, file_bytes, uploaded_file.name if uploaded_file else None, add_bytes, add_names)
            except Exception as e:
                st.error(f"E-Mail-Versand fehlgeschlagen: {e}")
