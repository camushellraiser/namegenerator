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

# --- Clear Session State to Reset Form ---
if "reset_triggered" not in st.session_state:
    st.session_state.reset_triggered = False

if st.button("🔄 Reset Form"):
    st.session_state.reset_triggered = True
    st.experimental_set_query_params(reset="true")
    st.stop()

if st.session_state.reset_triggered:
    st.session_state["Title"] = ""
    st.session_state["Requested by"] = ""
    st.session_state["Reference Number"] = ""
    st.session_state["Requestor Email"] = ""
    st.session_state["HFM"] = ""
    st.session_state["Target Language(s)"] = []
    st.session_state["Content Type"] = []
    st.session_state.reset_triggered = False

# --- Input Fields ---
st.subheader("🔤 Input Details")
title = st.text_input("Title", key="Title")
gts_id = st.text_input("GTS ID", value="GTS2500", key="GTS ID")
requested_by = st.text_input("Requested by", key="Requested by")
reference_number = st.text_input("Reference Number", key="Reference Number")
requestor_email = st.text_input("Requestor Email", key="Requestor Email")
hfm = st.text_input("HFM", key="HFM")
target_languages = st.multiselect("Target Language(s)", ["DE", "ES", "FR", "JP", "KR", "CN", "TW", "BR"], key="Target Language(s)")
content_type = st.multiselect("Content Type", ["Marketing", "Product"], key="Content Type")

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

# --- Generate Button ---
if st.button("🚀 Generate Names"):
    if title and gts_id and requested_by and reference_number:
        st.markdown("---")
        st.subheader("📛 Generated Names")
        workfront_name = build_workfront_name()
        wordbee_name = build_wordbee_name()
        aem_name = wordbee_name if "Marketing" in content_type else None

        st.markdown("#### 🧾 Workfront Name")
        st.code(workfront_name, language='none', line_numbers=False)

        if aem_name:
            st.markdown("#### 📂 AEM Name")
            st.code(aem_name, language='none', line_numbers=False)

        st.markdown("#### 🐝 Wordbee Name")
        st.code(wordbee_name, language='none', line_numbers=False)

        # --- Display Table ---
        data = {
            "Field": [
                "Title", "GTS ID", "Requested by", "Reference Number",
                "Requestor Email", "HFM", "Target Language(s)", "Content Type",
                "Workfront Name"
            ],
            "Value": [
                title, gts_id, requested_by, reference_number,
                requestor_email, hfm, ", ".join(target_languages), ", ".join(content_type),
                workfront_name
            ]
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
        filename = f"{gts_id.strip()} Naming Convention.xlsx"
        st.download_button(
            label="📥 Download as Excel",
            data=excel_bytes,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("Please complete all required fields (Title, GTS ID, Requested by, Reference Number) to generate names.")
