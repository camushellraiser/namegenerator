import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Naming Convention Generator", layout="centered")
st.title("🧩 Naming Convention Generator")
st.markdown("""
<style>
    .stTextInput>div>div>input {
        font-size: 16px;
    }
    .stMultiSelect>div>div>div>div {
        font-size: 16px;
    }
    .stMarkdown h3 {
        color: #a30000;
    }
    .generated-table td {
        font-size: 15px !important;
    }
</style>
""", unsafe_allow_html=True)

# --- Session State Initialization ---
if "generated" not in st.session_state:
    st.session_state.generated = False
if "warning" not in st.session_state:
    st.session_state.warning = False

# --- Helper Functions ---
def get_initial_lastname(full_name):
    parts = full_name.strip().split()
    if len(parts) >= 2:
        return parts[0][0] + parts[-1]
    return parts[0] if parts else ""

def build_workfront_name():
    return f"{st.session_state['GTS ID']}_Web_{get_initial_lastname(st.session_state['Requested by'])}_{st.session_state['Title']}_{st.session_state['Reference Number']}"

def build_wordbee_name():
    name = f"{st.session_state['GTS ID']}_Web_{get_initial_lastname(st.session_state['Requested by'])}_{st.session_state['Title']}"
    systems = []
    if "Marketing" in st.session_state['Content Type']:
        systems.append("AEM")
    if "Product" in st.session_state['Content Type']:
        systems.append("Iris")
    if systems:
        name += "_" + "_".join(systems)
    langs = st.session_state['Target Language(s)']
    if len(langs) == 1:
        name += f"_{langs[0]}"
    return name

# --- Callbacks ---
def reset_form():
    # Clear all input fields except GTS ID
    for field in ["Title", "Requested by", "Reference Number", "Requestor Email", "HFM", "Target Language(s)", "Content Type"]:
        st.session_state.pop(field, None)
    st.session_state.generated = False
    st.session_state.warning = False
    st.rerun()

def generate_names():
    # Validate required fields
    title = st.session_state.get("Title", "").strip()
    gts = st.session_state.get("GTS ID", "").strip()
    req = st.session_state.get("Requested by", "").strip()
    ref = st.session_state.get("Reference Number", "").strip()
    if title and gts and req and ref:
        # Build names
        st.session_state.workfront_name = build_workfront_name()
        st.session_state.wordbee_name = build_wordbee_name()
        # Build AEM name if Marketing
        aem = None
        if "Marketing" in st.session_state.get('Content Type', []):
            aem = f"{gts}_Web_{get_initial_lastname(req)}_{title}_AEM"
            langs = st.session_state.get('Target Language(s)', [])
            if len(langs) == 1:
                aem += f"_{langs[0]}"
        st.session_state.aem_name = aem
        # Prepare results table
        data = {
            "Field": [
                "Title", "GTS ID", "Requested by", "Reference Number",
                "Requestor Email", "HFM", "Target Language(s)", "Content Type",
                "Workfront Name"
            ],
            "Value": [
                title, gts, req, ref,
                st.session_state.get("Requestor Email", ""), st.session_state.get("HFM", ""),
                ", ".join(st.session_state.get('Target Language(s)', [])),
                ", ".join(st.session_state.get('Content Type', [])),
                st.session_state.workfront_name
            ]
        }
        if st.session_state.aem_name:
            data['Field'].append('AEM Name')
            data['Value'].append(st.session_state.aem_name)
        data['Field'].append('Wordbee Name')
        data['Value'].append(st.session_state.wordbee_name)
        st.session_state.result_df = pd.DataFrame(data)
        st.session_state.generated = True
        st.session_state.warning = False
    else:
        st.session_state.generated = False
        st.session_state.warning = True

# --- UI Elements ---
st.button("🔄 Reset Form", on_click=reset_form)

st.subheader("🔤 Input Details")
st.text_input("Title", key="Title")
st.text_input("GTS ID", value="GTS2500", key="GTS ID")
st.text_input("Requested by", key="Requested by")
st.text_input("Reference Number", key="Reference Number")
st.text_input("Requestor Email", key="Requestor Email")
st.text_input("HFM", key="HFM")

# --- Language & Content Type Inputs ---
# Language options with flags, sorted alphabetically by code
LANGUAGE_OPTIONS = [
    ("BR", "🇧🇷"),
    ("CN", "🇨🇳"),
    ("DE", "🇩🇪"),
    ("ES", "🇪🇸"),
    ("FR", "🇫🇷"),
    ("JP", "🇯🇵"),
    ("KR", "🇰🇷"),
    ("TW", "🇹🇼"),
]
# Display dropdown with flags
display_options = [f"{code} {emoji}" for code, emoji in LANGUAGE_OPTIONS]
selected_display = st.multiselect("Target Language(s)", display_options, key="Target Language(s)_disp")
# Store codes in session_state
st.session_state['Target Language(s)'] = [opt.split()[0] for opt in selected_display]

# Content type
st.multiselect("Content Type", ["Marketing", "Product"], key="Content Type")

# Generate button
st.button("🚀 Generate Names", on_click=generate_names), on_click=generate_names)("🔄 Reset Form", on_click=reset_form)

st.subheader("🔤 Input Details")
st.text_input("Title", key="Title")
st.text_input("GTS ID", value="GTS2500", key="GTS ID")
st.text_input("Requested by", key="Requested by")
st.text_input("Reference Number", key="Reference Number")
st.text_input("Requestor Email", key="Requestor Email")
st.text_input("HFM", key="HFM")
st.multiselect("Target Language(s)", ["DE", "ES", "FR", "JP", "KR", "CN", "TW", "BR"], key="Target Language(s)")
st.multiselect("Content Type", ["Marketing", "Product"], key="Content Type")
st.button("🚀 Generate Names", on_click=generate_names)

# Show warning if needed
if st.session_state.warning:
    st.warning("Please complete all required fields (Title, GTS ID, Requested by, Reference Number) to generate names.")

# Display results if generated persists
if st.session_state.generated:
    st.markdown("---")
    st.subheader("📛 Generated Names")
    st.markdown("#### 🧾 Workfront Name")
    st.code(st.session_state.workfront_name, language='none', line_numbers=False)
    if st.session_state.aem_name:
        st.markdown("#### 📂 AEM Name")
        st.code(st.session_state.aem_name, language='none', line_numbers=False)
    st.markdown("#### 🐝 Wordbee Name")
    st.code(st.session_state.wordbee_name, language='none', line_numbers=False)

    # Wordbee Form Summary
    with st.expander("📝 Wordbee Form Summary", expanded=False):
        st.text(f"Order Title:               {st.session_state['Title']}")
        st.text(f"Reference:                 {st.session_state['GTS ID']}")
        st.text(f"Contact Name:              {st.session_state['Requested by']}")
        st.text(f"Email:                     {st.session_state['Requestor Email']}")
        st.text(f"If submitting for someone: {st.session_state['Requested by']}")
        st.text(f"HFM Code:                  {st.session_state['HFM']}")
        st.text(f"Languages:                 {', '.join(st.session_state.get('Target Language(s)', []))}")
        st.text(f"Content Type:              {', '.join(st.session_state.get('Content Type', []))}")
        st.text(f"Generated Name:            {st.session_state.workfront_name}")

    # Display results table
    st.dataframe(st.session_state.result_df.style.set_properties(**{'font-size': '15px'}), use_container_width=True)

    # Download as Excel
    def convert_df_to_excel(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Naming Results')
            ws = writer.sheets['Naming Results']
            ws.set_column('A:A', 25)
            ws.set_column('B:B', 70)
        output.seek(0)
        return output

    excel_bytes = convert_df_to_excel(st.session_state.result_df)
    filename = f"{st.session_state['GTS ID'].strip()} Naming Convention.xlsx"
    st.download_button(
        label="📥 Download as Excel",
        data=excel_bytes,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
