import streamlit as st
import pandas as pd
import re
from io import BytesIO

# -----------------------------------------------------------------------------
# 0) Reset button and logic
if st.button("🔄 Reset Form"):
    keys = [
        'parsed','raw_input',
        'Title','Requested by','Reference Number',
        'Requestor Email','HFM',
        'target_disp','content_type',
        'shared_name','workfront_name','wordbee_list',
        'aem_list','result_df','generated','warning'
    ]
    for k in keys:
        if k in st.session_state:
            del st.session_state[k]
    st.experimental_rerun()

# -----------------------------------------------------------------------------
# 1) App configuration
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

# -----------------------------------------------------------------------------
# 2) Language options and emoji map
LANGUAGE_OPTIONS = [
    ("BR", "🇧🇷"), ("CN", "🇨🇳"), ("DE", "🇩🇪"), ("ES", "🇪🇸"),
    ("FR", "🇫🇷"), ("JP", "🇯🇵"), ("KR", "🇰🇷"), ("TW", "🇹🇼"),
]
lang_emojis = {code: emoji for code, emoji in LANGUAGE_OPTIONS}

# -----------------------------------------------------------------------------
# 3) Session-state flags
for flag in ('parsed','generated','warning'):
    if flag not in st.session_state:
        st.session_state[flag] = False

# -----------------------------------------------------------------------------
# 4) Paste-and-parse area (once)
raw = st.text_area(
    "📋 Paste full Issue/Workfront page content here:",
    key="raw_input",
    height=200
)
if raw and not st.session_state.parsed:
    # Title: last non-empty line after each "Issue"
    titles = re.findall(r"Issue\s*\n([^\n]+)", raw)
    good   = [t.strip() for t in titles if t.strip().lower() != "issue"]
    if good:
        st.session_state.Title = good[-1]

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
        st.session_state.HFM = m.group(1).strip()

    # Content types
    m = re.search(r"Content to be translated\*\s*\n([^\n]+)", raw)
    if m:
        st.session_state.content_type = [c.strip() for c in m.group(1).split(",")]

    # Target languages
    codes = re.findall(r"\b([A-Z]{2})\b(?=\s*-\s*[A-Za-z])", raw)
    seen = []
    for c in codes:
        if c in lang_emojis and c not in seen:
            seen.append(c)
    st.session_state.target_disp = [f"{lang_emojis[c]} {c}" for c in seen]

    st.session_state.parsed = True

# -----------------------------------------------------------------------------
# 5) Input form
with st.form("input_form"):
    st.subheader("🔤 Input Details")
    st.text_input("Title", key="Title")
    st.text_input("GTS ID", value="GTS2500", key="GTS ID")
    st.text_input("Requested by", key="Requested by")
    st.text_input("Reference Number", key="Reference Number")
    st.text_input("Requestor Email", key="Requestor Email")
    st.text_input("HFM", key="HFM")

    display_opts = [f"{emoji} {code}" for code, emoji in sorted(LANGUAGE_OPTIONS)]
    st.multiselect("Target Language(s)", display_opts, key="target_disp")
    st.multiselect("Content Type", ["Marketing", "Product"], key="content_type")

    submit = st.form_submit_button("🚀 Generate Names")

# -----------------------------------------------------------------------------
# 6) Helpers
def get_initial_lastname(full_name: str) -> str:
    parts = full_name.strip().split()
    return (parts[0][0] + parts[-1]) if len(parts) >= 2 else (parts[0] if parts else "")

def build_shared(gts_id, req):
    return f"{gts_id}_Web_{get_initial_lastname(req)}"

def build_workfront(shared, title, ref):
    return f"{shared}_{title}_{ref}"

def build_wordbee_list(shared, title, langs, ct):
    base = f"{shared}_{title}"
    sy = []
    if 'Marketing' in ct: sy.append('AEM')
    if 'Product'   in ct: sy.append('Iris')
    if sy: base += '_' + '_'.join(sy)
    return [f"{base}_{langs[0]}"] if len(langs)==1 else [base] if langs else [base]

def build_aem_list(shared, title, langs, ct):
    if 'Marketing' not in ct:
        return []
    base = f"{shared}_{title}_AEM"
    return [f"{base}_{l}" for l in langs] if langs else [base]

# -----------------------------------------------------------------------------
# 7) Generate
if submit:
    valid = all([
        st.session_state.get("Title"),
        st.session_state.get("GTS ID"),
        st.session_state.get("Requested by"),
        st.session_state.get("Reference Number")
    ])
    if not valid:
        st.session_state.generated = False
        st.session_state.warning = True
    else:
        ttl   = st.session_state.Title
        gid   = st.session_state["GTS ID"]
        req   = st.session_state["Requested by"]
        ref   = st.session_state["Reference Number"]
        ct    = st.session_state.get("content_type", [])
        langs = [d.split()[1] for d in st.session_state.get("target_disp", [])]

        shared = build_shared(gid, req)
        work   = build_workfront(shared, ttl, ref)
        wbee   = build_wordbee_list(shared, ttl, langs, ct)
        aem    = build_aem_list(shared, ttl, langs, ct)

        st.session_state.update({
            "shared_name": shared,
            "workfront_name": work,
            "wordbee_list": wbee,
            "aem_list": aem,
            "generated": True,
            "warning": False
        })

        # Build DataFrame
        data = {
            "Field": [
                "Title","GTS ID","Requested by","Reference Number",
                "Requestor Email","HFM","Target Language(s)",
                "Content Type","GTS Shared Library Name","Workfront Name"
            ],
            "Value": [
                ttl, gid, req, ref,
                st.session_state.get("Requestor Email",""),
                st.session_state.get("HFM",""),
                ", ".join(langs), ", ".join(ct),
                shared, work
            ]
        }
        for n in aem:
            code = n.split("_")[-1]
            data["Field"].append(f"AEM Name - {code}")
            data["Value"].append(n)
        for n in wbee:
            data["Field"].append("Wordbee Name")
            data["Value"].append(n)

        st.session_state.result_df = pd.DataFrame(data)

# -----------------------------------------------------------------------------
# 8) Display & Download
if st.session_state.warning:
    st.warning("Complete all required fields to generate names.")

if st.session_state.generated:
    st.markdown("---")
    st.subheader("📛 Generated Names")

    langs = [d.split()[1] for d in st.session_state.get("target_disp", [])]
    ct    = st.session_state.get("content_type", [])

    st.markdown("#### 📚 GTS Shared Library Name")
    st.code(st.session_state.shared_name, language="none")

    st.markdown("#### 🧾 Workfront Name")
    st.code(st.session_state.workfront_name, language="none")

    for name in st.session_state.aem_list:
        code = name.split("_")[-1]
        flag = lang_emojis.get(code, "")
        st.markdown(f"#### 📂 AEM Name - {code} {flag}")
        st.code(name, language="none")

    st.markdown("#### 🐝 Wordbee Name")
    st.code(st.session_state.wordbee_list[0], language="none")

    with st.expander("📝 Wordbee Form Summary", expanded=False):
        s = st.session_state
        st.text(f"Order Title:               {s.Title}")
        st.text(f"Reference:                 {s['GTS ID']}")
        st.text(f"Contact Name:              {s['Requested by']}")
        st.text(f"Email:                     {s['Requestor Email']}")
        st.text(f"HFM Code:                  {s.HFM}")
        st.text(f"Languages:                 {', '.join(langs)}")
        st.text(f"Content Type:              {', '.join(ct)}")
        st.text(f"Generated Name:            {s.workfront_name}")

    st.dataframe(
        st.session_state.result_df
          .style.set_properties(**{"font-size":"15px"}),
        use_container_width=True
    )

    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        st.session_state.result_df.to_excel(writer, index=False, sheet_name="Naming Results")
        ws = writer.sheets["Naming Results"]
        ws.set_column("A:A", 25)
        ws.set_column("B:B", 70)
    buf.seek(0)

    st.download_button(
        "📥 Download as Excel",
        data=buf,
        file_name=f"{st.session_state['GTS ID']} Naming Convention.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
