import streamlit as st
import pandas as pd
from io import BytesIO

# App configuration
st.set_page_config(page_title="Naming Convention Generator", layout="centered")
st.title("🧩 Naming Convention Generator")
st.markdown("""
<style>
    .stTextInput>div>div>input { font-size: 16px; }
    .stMultiSelect>div>div>div>div { font-size: 16px; }
    .stMarkdown h3 { color: #a30000; }
    .generated-table td { font-size: 15px !important; }
</style>
""", unsafe_allow_html=True)

# Initialize session state flags
if 'generated' not in st.session_state:
    st.session_state['generated'] = False
if 'warning' not in st.session_state:
    st.session_state['warning'] = False

# --- Reset callback ---
def reset_form():
    # Clear inputs except GTS ID
    for key in ['Title', 'Requested by', 'Reference Number', 'Requestor Email', 'HFM']:
        st.session_state.pop(key, None)
    st.session_state.pop('target_disp', None)
    st.session_state.pop('content_type', None)
    # Clear results
    for key in ['shared_name', 'workfront_name', 'wordbee_name', 'aem_list', 'result_df', 'generated', 'warning']:
        st.session_state.pop(key, None)

# Reset button
st.button("🔄 Reset Form", on_click=reset_form)

# --- Input Fields ---
st.subheader("🔤 Input Details")
title = st.text_input("Title", key='Title')
gts_id = st.text_input("GTS ID", value="GTS2500", key='GTS ID')
requested_by = st.text_input("Requested by", key='Requested by')
reference_number = st.text_input("Reference Number", key='Reference Number')
requestor_email = st.text_input("Requestor Email", key='Requestor Email')
hfm = st.text_input("HFM", key='HFM')

# --- Language & Content Type ---
LANGUAGE_OPTIONS = [
    ("BR","🇧🇷"),("CN","🇨🇳"),("DE","🇩🇪"),("ES","🇪🇸"),
    ("FR","🇫🇷"),("JP","🇯🇵"),("KR","🇰🇷"),("TW","🇹🇼"),
]
# Flags on left, sorted by code
display_options = [f"{emoji} {code}" for code, emoji in sorted(LANGUAGE_OPTIONS)]
selected_disp = st.multiselect("Target Language(s)", display_options, key='target_disp')
# Extract codes
languages = [opt.split()[1] for opt in selected_disp]

content_type = st.multiselect("Content Type", ["Marketing","Product"], key='content_type')

# --- Name Builders ---
def get_initial_lastname(full_name: str) -> str:
    parts = full_name.strip().split()
    return (parts[0][0] + parts[-1]) if len(parts)>=2 else (parts[0] if parts else "")

def build_shared(name_id, req):
    return f"{name_id}_Web_{get_initial_lastname(req)}"

def build_workfront(name_id, req, ttl, ref):
    return f"{build_shared(name_id, req)}_{ttl}_{ref}"

def build_wordbee(name_id, req, ttl, langs, ct):
    base = f"{build_shared(name_id, req)}_{ttl}"
    systems = []
    if 'Marketing' in ct:
        systems.append('AEM')
    if 'Product' in ct:
        systems.append('Iris')
    if systems:
        base += '_' + '_'.join(systems)
    if len(langs) == 1:
        base += f"_{langs[0]}"
    return base

def build_aem_list(name_id, req, ttl, langs, ct):
    if 'Marketing' not in ct:
        return []
    base = f"{build_shared(name_id, req)}_{ttl}_AEM"
    # Generate one per language
    return [f"{base}_{lang}" for lang in (langs if langs else [''])]

# --- Generate Names ---
if st.button("🚀 Generate Names"):
    # Validate required fields
    if all([st.session_state.get('Title'), st.session_state.get('GTS ID'),
            st.session_state.get('Requested by'), st.session_state.get('Reference Number')]):
        ttl = st.session_state['Title']
        gid = st.session_state['GTS ID']
        req = st.session_state['Requested by']
        ref = st.session_state['Reference Number']
        # Build names
        shared = build_shared(gid, req)
        work = f"{shared}_{ttl}_{ref}"
        wbee = build_wordbee(gid, req, ttl, languages, content_type)
        aem_list = build_aem_list(gid, req, ttl, languages, content_type)
        # Save to session
        st.session_state['shared_name'] = shared
        st.session_state['workfront_name'] = work
        st.session_state['wordbee_name'] = wbee
        st.session_state['aem_list'] = aem_list
        # Build results table
        data = {
            'Field':[ 'Title','GTS ID','Requested by','Reference Number',
                      'Requestor Email','HFM','Target Language(s)','Content Type','GTS Shared Library Name','Workfront Name'],
            'Value':[ ttl,gid,req,ref,
                      st.session_state.get('Requestor Email',''),st.session_state.get('HFM',''),
                      ', '.join(languages), ', '.join(content_type), shared, work ]
        }
        # AEM names
        for name in aem_list:
            data['Field'].append('AEM Name')
            data['Value'].append(name)
        # Wordbee
        data['Field'].append('Wordbee Name')
        data['Value'].append(wbee)
        df = pd.DataFrame(data)
        st.session_state['result_df'] = df
        st.session_state['generated'] = True
        st.session_state['warning'] = False
    else:
        st.session_state['generated'] = False
        st.session_state['warning'] = True

# Show warning
if st.session_state['warning']:
    st.warning("Complete all required fields to generate names.")

# Display results
if st.session_state['generated']:
    st.markdown('---')
    st.subheader('📛 Generated Names')
    # Shared
    st.markdown('#### 📚 GTS Shared Library Name')
    st.code(st.session_state['shared_name'], language='none')
    # Workfront
    st.markdown('#### 🧾 Workfront Name')
    st.code(st.session_state['workfront_name'], language='none')
    # AEM multiple
    for name in st.session_state.get('aem_list', []):
        st.markdown('#### 📂 AEM Name')
        st.code(name, language='none')
    # Wordbee
    st.markdown('#### 🐝 Wordbee Name')
    st.code(st.session_state['wordbee_name'], language='none')
    
    # Summary
    with st.expander('📝 Wordbee Form Summary', expanded=False):
        st.text(f"Order Title:               {st.session_state['Title']}")
        st.text(f"Reference:                 {st.session_state['GTS ID']}")
        st.text(f"Contact Name:              {st.session_state['Requested by']}")
        st.text(f"Email:                     {st.session_state['Requestor Email']}")
        st.text(f"If submitting for someone: {st.session_state['Requested by']}")
        st.text(f"HFM Code:                  {st.session_state['HFM']}")
        st.text(f"Languages:                 {', '.join(languages)}")
        st.text(f"Content Type:              {', '.join(content_type)}")
        st.text(f"Generated Name:            {st.session_state['workfront_name']}")

    # Table
    st.dataframe(st.session_state['result_df'].style.set_properties(**{'font-size':'15px'}), use_container_width=True)
    
    # Download Excel
    def to_excel(df):
        buf = BytesIO()
        with pd.ExcelWriter(buf, engine='xlsxwriter') as w:
            df.to_excel(w, index=False, sheet_name='Naming Results')
            ws = w.sheets['Naming Results']
            ws.set_column('A:A', 25); ws.set_column('B:B', 70)
        buf.seek(0); return buf
    excel_buf = to_excel(st.session_state['result_df'])
    fname = f"{st.session_state['GTS ID'].strip()} Naming Convention.xlsx"
    st.download_button('📥 Download as Excel', data=excel_buf, file_name=fname,
                       mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
