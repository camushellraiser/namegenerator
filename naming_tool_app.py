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

# Language options and emoji map (global)
LANGUAGE_OPTIONS = [
    ("BR", "🇧🇷"), ("CN", "🇨🇳"), ("DE", "🇩🇪"), ("ES", "🇪🇸"),
    ("FR", "🇫🇷"), ("JP", "🇯🇵"), ("KR", "🇰🇷"), ("TW", "🇹🇼"),
]
lang_emojis = {code: emoji for code, emoji in LANGUAGE_OPTIONS}

# Initialize session state
for flag in ['generated', 'warning']:
    if flag not in st.session_state:
        st.session_state[flag] = False

# --- Reset callback ---
def reset_form():
    # Clear inputs except GTS ID
    for key in ['Title', 'Requested by', 'Reference Number', 'Requestor Email', 'HFM']:
        st.session_state.pop(key, None)
    # clear dropdown states
    st.session_state.pop('target_disp', None)
    st.session_state.pop('content_type', None)
    # Clear results
    for key in ['shared_name', 'workfront_name', 'wordbee_list', 'aem_list', 'result_df', 'generated', 'warning']:
        st.session_state.pop(key, None)

# Reset button
st.button("🔄 Reset Form", on_click=reset_form)

# --- Input Form ---
with st.form(key='input_form'):
    st.subheader("🔤 Input Details")
    st.text_input("Title", key='Title')
    st.text_input("GTS ID", value="GTS2500", key='GTS ID')
    st.text_input("Requested by", key='Requested by')
    st.text_input("Reference Number", key='Reference Number')
    st.text_input("Requestor Email", key='Requestor Email')
    st.text_input("HFM", key='HFM')
    
    # Language & Content Type
    display_options = [f"{emoji} {code}" for code, emoji in sorted(LANGUAGE_OPTIONS)]
    selected_disp = st.multiselect("Target Language(s)", display_options, key='target_disp')
    languages = [opt.split()[1] for opt in selected_disp]
    
    st.multiselect("Content Type", ["Marketing", "Product"], key='content_type')
    
    submit = st.form_submit_button("🚀 Generate Names")

# --- Name Builders ---
def get_initial_lastname(full_name: str) -> str:
    parts = full_name.strip().split()
    return (parts[0][0] + parts[-1]) if len(parts) >= 2 else (parts[0] if parts else "")

def build_shared(name_id, req):
    return f"{name_id}_Web_{get_initial_lastname(req)}"

def build_workfront(shared, ttl, ref):
    return f"{shared}_{ttl}_{ref}"

def build_wordbee_list(shared, ttl, langs, ct):
    base = f"{shared}_{ttl}"
    systems = []
    if 'Marketing' in ct:
        systems.append('AEM')
    if 'Product' in ct:
        systems.append('Iris')
    if systems:
        base += '_' + '_'.join(systems)
    # One per language if multiple, else append code
    if langs:
        return [f"{base}_{lang}" for lang in langs]
    return [base]

def build_aem_list(shared, ttl, langs, ct):
    if 'Marketing' not in ct:
        return []
    base = f"{shared}_{ttl}_AEM"
    if langs:
        return [f"{base}_{lang}" for lang in langs]
    return [base]

# --- Generate Logic ---
if submit:
    if all([st.session_state.get('Title'), st.session_state.get('GTS ID'),
            st.session_state.get('Requested by'), st.session_state.get('Reference Number')]):
        ttl = st.session_state['Title']
        gid = st.session_state['GTS ID']
        req = st.session_state['Requested by']
        ref = st.session_state['Reference Number']
        ct = st.session_state.get('content_type', [])
        shared = build_shared(gid, req)
        work = build_workfront(shared, ttl, ref)
        wbee_list = build_wordbee_list(shared, ttl, languages, ct)
        aem_list = build_aem_list(shared, ttl, languages, ct)
        # store
        st.session_state.update({
            'shared_name': shared,
            'workfront_name': work,
            'wordbee_list': wbee_list,
            'aem_list': aem_list,
            'generated': True,
            'warning': False
        })
        # build table
        data = {
            'Field': ['Title','GTS ID','Requested by','Reference Number','Requestor Email','HFM','Target Language(s)','Content Type','GTS Shared Library Name','Workfront Name'],
            'Value': [ttl, gid, req, ref, st.session_state.get('Requestor Email',''), st.session_state.get('HFM',''), ', '.join(languages), ', '.join(ct), shared, work]
        }
        for name in aem_list:
            data['Field'].append('AEM Name')
            data['Value'].append(name)
        for name in wbee_list:
            data['Field'].append('Wordbee Name')
            data['Value'].append(name)
        st.session_state['result_df'] = pd.DataFrame(data)
    else:
        st.session_state['generated'] = False
        st.session_state['warning'] = True

# --- Display ---
if st.session_state['warning']:
    st.warning("Complete all required fields to generate names.")

if st.session_state['generated']:
    st.markdown('---')
    st.subheader('📛 Generated Names')
    st.markdown('#### 📚 GTS Shared Library Name')
    st.code(st.session_state['shared_name'], language='none')
    st.markdown('#### 🧾 Workfront Name')
    st.code(st.session_state['workfront_name'], language='none')
    for name in st.session_state.get('aem_list', []):
        st.markdown('#### 📂 AEM Name')
        st.code(name, language='none')
    for name in st.session_state.get('wordbee_list', []):
        code = name.split('_')[-1]
        flag = lang_emojis.get(code, '')
        st.markdown(f"#### 🐝 Wordbee Name {flag}")
        st.code(name, language='none')
    # Summary
    with st.expander('📝 Wordbee Form Summary', expanded=False):
        s = st.session_state
        st.text(f"Order Title:               {s['Title']}")
        st.text(f"Reference:                 {s['GTS ID']}")
        st.text(f"Contact Name:              {s['Requested by']}")
        st.text(f"Email:                     {s['Requestor Email']}")
        st.text(f"If submitting for someone: {s['Requested by']}")
        st.text(f"HFM Code:                  {s['HFM']}")
        st.text(f"Languages:                 {', '.join(languages)}")
        st.text(f"Content Type:              {', '.join(st.session_state.get('content_type', []))}")
        st.text(f"Generated Name:            {s['workfront_name']}")
    st.dataframe(st.session_state['result_df'].style.set_properties(**{'font-size':'15px'}), use_container_width=True)
    # Download Excel
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine='xlsxwriter') as w:
        st.session_state['result_df'].to_excel(w, index=False, sheet_name='Naming Results')
        ws = w.sheets['Naming Results']
        ws.set_column('A:A',25)
        ws.set_column('B:B',70)
    buf.seek(0)
    st.download_button('📥 Download as Excel', data=buf, file_name=f"{st.session_state['GTS ID']} Naming Convention.xlsx", mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
