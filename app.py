import streamlit as st
import sys, os
from io import BytesIO
from pathlib import Path
from email_validator import validate_email, EmailNotValidError

# Page configuration
st.set_page_config(
    page_title="3D-JobShop Angebotsportal",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Cookie-Hinweis oben, dezent neben Button ---
if not st.session_state.get("cookies_accepted", False):
    placeholder = st.empty()
    with placeholder.container():
        col_text, col_button = st.columns([7,1])
        with col_text:
            st.markdown(
                "🍪 Wir verwenden Cookies für Sitzungs-Handling und anonyme Analyse.",
                unsafe_allow_html=True
            )
        with col_button:
            if st.button("Akzeptieren", key="cookie_accept_top"):
                st.session_state["cookies_accepted"] = True
                placeholder.empty()  # Entfernt Banner im selben Lauf
    st.markdown("---")

# Add src to PATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))
from core.data_loader import load_materials
from core.notifier import send_order_email

# Constants
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB
MATERIAL_PULVER_XLSX = "LMD_Materialliste_Pulver.xlsx"
MATERIAL_DRAHT_XLSX  = "LMD_Materialliste_Draht.xlsx"

# Sidebar navigation
st.sidebar.title("🛠️ Dein 3D-JobShop")
st.sidebar.markdown("###### Dein Weg zum Bauteil in 7 Schritten")
p_steps = ["Auftragsspezifikation", "Beschichtungsdicke", "Stückzahl", "Material", "Beschreibung", "Datei-Upload", "Kontaktdaten"]
for step in p_steps:
    st.sidebar.markdown(f"- {step}")
st.sidebar.markdown("---")
st.sidebar.caption("Lunovu – powered by Sato")
st.sidebar.markdown("[🌐 Zur Hauptseite von Sato](https://www.sato.de)", unsafe_allow_html=True)

# Legal text expanders
for title, filename in [
    ("ℹ️ Impressum", "Impressum.md"),
    ("🔒 Datenschutz", "Datenschutz.md"),
    ("🍪 Cookie-Hinweis", "Cookies.md"),
    ("📄 AGB", "AGB.md")
]:
    with st.sidebar.expander(title):
        st.markdown(Path(filename).read_text(encoding="utf-8"), unsafe_allow_html=True)

# Hero section
st.markdown(
    """
    <div style="text-align:center; padding:20px 0;">
      <h1 style="color:#0066CC;">Willkommen bei 3D-JobShop</h1>
      <p>Lade Deine Datei hoch, wähle Deine Optionen und erhalte in Kürze Dein Angebot – schnell, zuverlässig, einfach!</p>
    </div>
    """, unsafe_allow_html=True
)
st.markdown("---")

# Load materials
pulver_materials, draht_materials = [], []
try:
    pulver_materials = load_materials(MATERIAL_PULVER_XLSX)
except FileNotFoundError:
    st.warning(f"⚠️ Pulver-Materialliste nicht gefunden: {MATERIAL_PULVER_XLSX}")
try:
    draht_materials = load_materials(MATERIAL_DRAHT_XLSX)
except FileNotFoundError:
    st.warning(f"⚠️ Draht-Materialliste nicht gefunden: {MATERIAL_DRAHT_XLSX}")

# Order form
with st.form("order_form", clear_on_submit=False):
    st.subheader("Auftragsspezifikation")
    aub = st.radio("Wähle den Auftragstyp:", ["Neuproduktion", "Reparatur", "Beschichtung"], index=0)

    st.subheader("Beschichtungsdicke (optional)")
    dicht = st.slider("Dicke in mm:", 0.01, 5.0, 0.1) if aub == "Beschichtung" else None

    st.subheader("Stückzahl")
    anzahl = st.number_input("Anzahl der Teile:", min_value=1, value=1)

    st.subheader("Material")
    mat_typ = st.selectbox("Materialart:", ["Pulver", "Draht"])
    options = (pulver_materials if mat_typ == "Pulver" else draht_materials) + ["Anderes Material"]
    material = st.selectbox("Material auswählen:", options)
    desired_material = st.text_input("Spezifiziere Dein Material:") if material == "Anderes Material" else None

    st.subheader("Beschreibung")
    beschreibung = st.text_area("Genauere Angaben:")

    st.subheader("Datei-Upload")
    send_physical = st.checkbox("Bauteil physisch einschicken? 📦")
    uploaded_file = st.file_uploader(
        "STL, STEP oder SPT hochladen:",
        type=None,
        help="Wähle deine STL-, STEP- oder SPT-Datei aus deinem Dateimanager."
    ) if not send_physical else None
        # iOS Safari Hinweis für Dateitypen
    st.caption("Tipp: In Safari auf 'Durchsuchen' tippen und im Dateiauswahl-Dialog oben 'Alle Dateien' wählen, um STL/STEP/SPT anzuzeigen.")
    # Manuelle Formatprüfung für iOS Safari
    if uploaded_file:
        name_lower = uploaded_file.name.lower()
