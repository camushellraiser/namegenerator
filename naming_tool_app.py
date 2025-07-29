import streamlit as st
import pandas as pd
import re
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

# --- Auto-extract from pasted page ---
raw = st.text_area(
    "📋 Paste full Issue/Workfront page content here:",
    key="raw_input",
    height=200
)

if raw:
    # Title: first line after the literal "Issue" keyword
    m = re.search(r"^Issue\s*$\s*(.+)", raw, re.MULTILINE)
    if m:
        st.session_state["Title"] = m.group(1).strip()

    # Reference Number
    m = re.search(r"Reference Number\s*\n(\d+)", raw)
    if m:
        st.session_state["Reference Number"] = m.group(1).strip()

    # Requested by
    m = re.search(r"Requested by\s*\n(.+)", raw)
    if m:
        st.session_state["Requested by"] = m.group(1).strip()

    # Requestor Email
    m = re.search(r"Requestor Email\s*\n(\S+@\S+)", raw)
    if m:
        st.session_state["Requestor Email"] = m.group(1).strip()

    # HFM Entity Code
    m = re.search(r"HFM Entity Code\s*\n(.+)", raw)
    if m:
        st.session_state["HFM"] = m.group(1).strip()

    # Content types (Marketing, Product)
    m = re.search(r"Content to be translated\*\s*\n([^\n]+)", raw)
    if m:
        ct_list = [c.strip() for c in m.group(1).split(",")]
        st.session_state["content_type"] = ct_list

    # Target languages: pull all codes like "CN", "JP" next to "- LanguageName"
    codes = re.findall(r"\b([A-Z]{2})\b(?=\s*-\s*[A-Za-z])", raw)
    # Dedupe & filter to known
    target_codes = []
    for code in codes:
        if code in lang_emojis and code not in target_codes:
            target_codes.append(code)
    # Build display list
    st.session_state["target_disp"] = [f"{lang_emojis[c]} {c}" for c in target_codes]

# --- Reset callback ---
def reset_form():
    # Clear inputs except GTS ID
    for key in ['Title', 'Requested by', 'Reference Number', 'Requestor Email', 'HFM']:
        st.session_state.pop(key, None)
    st.session_state.pop('target_disp', None)
    st.session_state.pop('content_type', None)
    for key in ['shared_name', 'workfront_name', 'wordbee_list',
                'aem_list', 'result_df', 'generated', 'warning']:
        st.session_state.pop(key, None)
    st.session_state.pop('raw_input', None)

# Reset button
st.button("🔄 Reset Form", on_click=reset_form)

# --- Input Form ---
with st.form(key='input_form'):
    st.subheader("🔤 Input Details")

    # These will pick up session_state defaults if set above
    st.text_input("Title", key='Title')
    st.text_input("GTS ID", value="GTS2500", key='GTS ID')
    st.text_input("Requested by", key='Requested by')
    st.text_input("Reference Number", key='Reference Number')
    st.text_input("Requestor Email", key='Requestor Email')
    st.text_input("HFM", key='HFM')

    # Language & Content Type
    display_options = [f"{emoji} {code}" for code, emoji in sorted(LANGUAGE_OPTIONS)]
    st.multiselect("Target Language(s)", display_options, key='target_disp')
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
    if langs:
        return [f"{base}_{langs[0]}"] if len(langs) == 1 else [base]
    return [base]

def build_aem_list(shared, ttl, langs, ct):
    if 'Marketing' not in ct:
        return []
    base = f"{shared}_{ttl}_AEM"
    return [f"{base}_{lang}" for lang in langs] if langs else [base]

# --- Generate Logic ---
if submit:
    if all([st.session_state.get('Title'),
            st.session_state.get('GTS ID'),
            st.session_state.get('Requested by'),
            st.session_state.get('Reference Number')]):
        ttl = st.session_state['Title']
        gid = st.session_state['GTS ID']
        req = st.session_state['Requested by']
        ref = st.session_state['Reference Number']
        ct = st.session_state.get('content_type', [])
        # pull codes back out of the display strings
        langs = [d.split()[1] for d in st.session_state.get('target_disp', [])]

        shared = build_shared(gid, req)
        work = build_workfront(shared, ttl, ref)
        wbee_list = build_wordbee_list(shared, ttl, langs, ct)
        aem_list = build_aem_list(shared, ttl, langs, ct)

        st.session_state.update({
            'shared_name': shared,
            'workfront_name': work,
            'wordbee_list': wbee_list,
            'aem_list': aem_list,
            'generated': True,
            'warning': False
        })

        # Build table
        data = {
            'Field': [
                'Title','GTS ID','Requested by','Reference Number',
                'Requestor Email','HFM','Target Language(s)',
                'Content Type','GTS Shared Library Name','Workfront Name'
            ],
            'Value': [
                ttl, gid, req, ref,
                st.session_state.get('Requestor Email',''),
                st.session_state.get('HFM',''),
                ', '.join(langs), ', '.join(ct), shared, work
            ]
        }
        for name in aem_list:
            code = name.split('_')[-1]
            data['Field'].append(f"AEM Name - {code}")
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
        code = name.split('_')[-1]
        flag = lang_emojis.get(code, '')
        st.markdown(f"#### 📂 AEM Name - {code} {flag}")
        st.code(name, language='none')

    st.markdown('#### 🐝 Wordbee Name')
    st.code(st.session_state['wordbee_list'][0], language='none')

    with st.expander('📝 Wordbee Form Summary', expanded=False):
        s = st.session_state
        st.text(f"Order Title:               {s['Title']}")
        st.text(f"Reference:                 {s['GTS ID']}")
        st.text(f"Contact Name:              {s['Requested by']}")
        st.text(f"Email:                     {s['Requestor Email']}")
        st.text(f"If submitting for someone: {s['Requested by']}")
        st.text(f"HFM Code:                  {s['HFM']}")
        st.text(f"Languages:                 {', '.join(langs)}")
        st.text(f"Content Type:              {', '.join(s['content_type'])}")
        st.text(f"Generated Name:            {s['workfront_name']}")

    st.dataframe(
        st.session_state['result_df']
          .style.set_properties(**{'font-size':'15px'}),
        use_container_width=True
    )

    # Download Excel
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine='xlsxwriter') as w:
        st.session_state['result_df'].to_excel(
            w, index=False, sheet_name='Naming Results'
        )
        ws = w.sheets['Naming Results']
        ws.set_column('A:A', 25)
        ws.set_column('B:B', 70)
    buf.seek(0)
    st.download_button(
        '📥 Download as Excel',
        data=buf,
        file_name=f"{st.session_state['GTS ID']} Naming Convention.xlsx",
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
