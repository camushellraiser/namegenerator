import streamlit as st
import pandas as pd
import re
from io import BytesIO

# -----------------------------------------------------------------------------
# App configuration
st.set_page_config(page_title="Naming Convention Generator", layout="centered")
st.title("🧩 Naming Convention Generator")

# -----------------------------------------------------------------------------
# Initialize session state flags
def init_flag(key):
    if key not in st.session_state:
        st.session_state[key] = False
for flag in ['parsed','generated','warning']:
    init_flag(flag)

# -----------------------------------------------------------------------------
# 1) Paste-and-parse area
raw = st.text_area(
    "📋 Paste full Issue/Workfront page content here:",
    key="raw_input", height=200
)
if raw and not st.session_state.parsed:
    titles = re.findall(r"Issue\s*\n([^\n]+)", raw)
    good = [t.strip() for t in titles if t.strip().lower() != "issue"]
    if good:
        st.session_state['Title'] = good[-1]
    m = re.search(r"Reference Number\s*\n(\d+)", raw)
    if m: st.session_state['Reference Number'] = m.group(1).strip()
    m = re.search(r"Requested by\s*\n(.+)", raw)
    if m: st.session_state['Requested by'] = m.group(1).strip()
    m = re.search(r"Requestor Email\s*\n(\S+@\S+)", raw)
    if m: st.session_state['Requestor Email'] = m.group(1).strip()
    m = re.search(r"HFM Entity Code\s*\n(.+)", raw)
    if m: st.session_state['HFM'] = m.group(1).strip()
    m = re.search(r"Content to be translated\*\s*\n([^\n]+)", raw)
    if m: st.session_state['content_type'] = [c.strip() for c in m.group(1).split(",")]
    # Languages
    LANGUAGE_OPTIONS = [
        ("BR","🇧🇷"),("CN","🇨🇳"),("DE","🇩🇪"),("ES","🇪🇸"),
        ("FR","🇫🇷"),("JP","🇯🇵"),("KR","🇰🇷"),("TW","🇹🇼"),
    ]
    lang_emojis = {c:e for c,e in LANGUAGE_OPTIONS}
    codes = re.findall(r"\b([A-Z]{2})\b(?=\s*-\s*[A-Za-z])", raw)
    seen=[]
    for c in codes:
        if c in lang_emojis and c not in seen:
            seen.append(c)
    st.session_state['target_disp'] = [f"{lang_emojis[c]} {c}" for c in seen]
    st.session_state.parsed = True

# -----------------------------------------------------------------------------
# 2) Input form
with st.form('input_form'):
    st.subheader("🔤 Input Details")
    st.text_input("Title", key='Title')
    st.text_input("GTS ID", value="GTS2500", key='GTS ID')
    st.text_input("Requested by", key='Requested by')
    st.text_input("Reference Number", key='Reference Number')
    st.text_input("Requestor Email", key='Requestor Email')
    st.text_input("HFM", key='HFM')
    LANGUAGE_OPTIONS = [
        ("BR","🇧🇷"),("CN","🇨🇳"),("DE","🇩🇪"),("ES","🇪🇸"),
        ("FR","🇫🇷"),("JP","🇯🇵"),("KR","🇰🇷"),("TW","🇹🇼"),
    ]
    display_opts = [f"{e} {c}" for c,e in sorted(LANGUAGE_OPTIONS)]
    st.multiselect("Target Language(s)", display_opts, key='target_disp')
    st.multiselect("Content Type", ["Marketing","Product"], key='content_type')
    generate = st.form_submit_button("🚀 Generate Names")

# -----------------------------------------------------------------------------
# Helpers

def get_initial_lastname(full_name:str)->str:
    parts=full_name.strip().split()
    return (parts[0][0]+parts[-1]) if len(parts)>=2 else (parts[0] if parts else "")
def build_shared(gid,req): return f"{gid}_Web_{get_initial_lastname(req)}"
def build_workfront(shared,ttl,ref): return f"{shared}_{ttl}_{ref}"
def build_wordbee(shared,ttl,langs,ct):
    base=f"{shared}_{ttl}";sy=[]
    if 'Marketing' in ct: sy.append('AEM')
    if 'Product' in ct: sy.append('Iris')
    if sy: base+= '_'+'_'.join(sy)
    return [f"{base}_{langs[0]}"] if len(langs)==1 else [base] if langs else [base]
def build_aem(shared,ttl,langs,ct):
    if 'Marketing' not in ct: return []
    base=f"{shared}_{ttl}_AEM"
    return [f"{base}_{l}" for l in langs] if langs else [base]

# -----------------------------------------------------------------------------
# 3) Generation logic
if generate:
    if not all([st.session_state.get(k) for k in ['Title','GTS ID','Requested by','Reference Number']]):
        st.session_state.generated=False;st.session_state.warning=True
    else:
        ttl, gid, req, ref = [st.session_state[k] for k in ['Title','GTS ID','Requested by','Reference Number']]
        ct=st.session_state.get('content_type',[])
        langs=[d.split()[1] for d in st.session_state.get('target_disp',[])]
        shared=build_shared(gid,req)
        work=build_workfront(shared,ttl,ref)
        wbee=build_wordbee(shared,ttl,langs,ct)
        aem=build_aem(shared,ttl,langs,ct)
        st.session_state.update({'shared_name':shared,'workfront_name':work,'wordbee_list':wbee,'aem_list':aem,'generated':True,'warning':False})
        data={'Field':['Title','GTS ID','Requested by','Reference Number','Requestor Email','HFM','Target Language(s)','Content Type','GTS Shared Library Name','Workfront Name'],
              'Value':[ttl,gid,req,ref,st.session_state.get('Requestor Email',''),st.session_state.get('HFM',''),', '.join(langs),', '.join(ct),shared,work]}
        for n in aem:
            c=n.split('_')[-1];data['Field'].append(f'AEM Name - {c}');data['Value'].append(n)
        for n in wbee:
            data['Field'].append('Wordbee Name');data['Value'].append(n)
        st.session_state['result_df']=pd.DataFrame(data)

# -----------------------------------------------------------------------------
# 4) Display & Download
if st.session_state.warning and not st.session_state.generated:
    st.warning("Complete all required fields to generate names.")
if st.session_state.generated:
    st.markdown('---');st.subheader('📛 Generated Names')
    st.markdown('#### 📚 GTS Shared Library Name');st.code(st.session_state['shared_name'],language='none')
    st.markdown('#### 🧾 Workfront Name');st.code(st.session_state['workfront_name'],language='none')
    for nm in st.session_state['aem_list']:
        c=nm.split('_')[-1];flag=lang_emojis.get(c,'');st.markdown(f'#### 📂 AEM Name - {c} {flag}');st.code(nm,language='none')
    st.markdown('#### 🐝 Wordbee Name');st.code(st.session_state['wordbee_list'][0],language='none')
    with st.expander('📝 Wordbee Form Summary',expanded=False):
        s=st.session_state;st.text(f"Order Title:               {s['Title']}");st.text(f"Reference:                 {s['GTS ID']}");st.text(f"Contact Name:              {s['Requested by']}");st.text(f"Email:                     {s['Requestor Email']}");st.text(f"HFM Code:                  {s['HFM']}");st.text(f"Languages:                 {', '.join(langs)}");st.text(f"Content Type:              {', '.join(ct)}");st.text(f"Generated Name:            {s['workfront_name']}")
    st.dataframe(st.session_state['result_df'].style.set_properties(**{'font-size':'15px'}),use_container_width=True)
    buf=BytesIO();
    with pd.ExcelWriter(buf,engine='xlsxwriter') as w:
        st.session_state['result_df'].to_excel(w,index=False,sheet_name='Naming Results');ws=w.sheets['Naming Results'];ws.set_column('A:A',25);ws.set_column('B:B',70)
    buf.seek(0);
    st.download_button('📥 Download as Excel',data=buf,file_name=f"{st.session_state['GTS ID']} Naming Convention.xlsx",mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

# -----------------------------------------------------------------------------
# 5) Reset Form button at bottom
if st.button('🔄 Reset Form'):
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.experimental_rerun()
