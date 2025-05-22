
import streamlit as st
import pandas as pd
import re
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

# --- Input Fields ---
st.subheader("🔤 Input Details")
title = st.text_input("Title", "Gibco Efficient-Pro Feed 3")
gts_id = st.text_input("GTS ID", "GTS2500")
requested_by = st.text_input("Requested by", "Yumiko Kotani")
reference_number = st.text_input("Reference Number", "11014150")
requestor_email = st.text_input("Requestor Email", "yumiko.kotani@thermofisher.com")
hfm = st.text_input("HFM", "LSSINGAPORE")
target_languages = st.multiselect("Target Language(s)", ["DE", "ES", "FR", "JP", "KR", "CN", "TW", "BR"], default=["JP"])
content_type = st.multiselect("Content Type", ["Marketing", "Product"])

# --- Helper functions ---
def get_initial_lastname(full_name):
    parts = full_name.strip().split()
    if len(parts) >= 2:
        return parts[0][0] + parts[-1]
    elif len(parts) == 1:
        return parts[0]  # fallback
    return ""

def build_workfront_name():
    return f"{gts_id}_Web_{get_initial_lastname(requested_by)}_{title}_{reference_number}"

def build_wordbee_name():
    name = f"{gts_id}_Web_{get_initial_lastname(requested_by)}_{title}"
    systems = []
    if "Marketing" in content_type:
        systems.append("AEM")
    if "Product" in content_type:
        systems.append("Iris")
    if systems:
        name += "_" + "_".join(systems)
    if len(target_languages) == 1:
        name += f"_{target_languages[0]}"
    return name

# --- Generate Names ---
st.markdown("---")
st.subheader("📛 Generated Names")
workfront_name = build_workfront_name()
aem_name = workfront_name if "Marketing" in content_type else None
wordbee_name = build_wordbee_name()

# --- Display Table ---
data = {
    "Field": ["Workfront Name"],
    "Value": [workfront_name]
}

if aem_name:
    data["Field"].append("AEM Name")
    data["Value"].append(aem_name)

data["Field"].append("Wordbee Name")
data["Value"].append(wordbee_name)

result_df = pd.DataFrame(data)
st.dataframe(result_df.style.set_properties(**{'font-size': '15px'}), use_container_width=True)

# --- Excel Export ---
def convert_df_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Naming Results')
        worksheet = writer.sheets['Naming Results']
        worksheet.set_column('A:A', 25)
        worksheet.set_column('B:B', 70)
    output.seek(0)
    return output

excel_bytes = convert_df_to_excel(result_df)
st.download_button(
    label="📥 Download as Excel",
    data=excel_bytes,
    file_name="naming_conventions.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
