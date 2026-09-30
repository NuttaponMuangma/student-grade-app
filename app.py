import html
import urllib.parse

import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="ผลการเรียนออนไลน์ - โรงเรียนบ้านสันถนน",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="collapsed",
)

SCHOOL_NAME = "โรงเรียนบ้านสันถนน"
SCHOOL_DISTRICT = "สำนักงานเขตพื้นที่การศึกษาประถมศึกษาเชียงราย เขต 3"
ACADEMIC_YEAR = "2569"
SEMESTER = "1"

SHEET_ID = "1FXRBsGcqjpDjKjzmArhz8SAnKd2sE-gl_zT9NhfzOPM"
GSHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit?usp=sharing"
SHEET_NAMES = ["ม.1", "ม.2", "ม.3"]

# รหัสครู: ตั้งใน Streamlit Cloud > Settings > Secrets  ->  TEACHER_PASSWORD = "รหัสของท่าน"
TEACHER_PASSWORD = st.secrets.get("TEACHER_PASSWORD", "1234")


def clean_html(s):
    return "".join(line.strip() for line in s.split("\n"))


def esc(v):
    return html.escape(str(v))


def get_subject_info(subj_name):
    info_map = [
        ("อังกฤษเพิ่ม", 1.0, "เพิ่มเติม"), ("คณิตเพิ่ม", 1.0, "เพิ่มเติม"),
        ("ภาษาไทย", 1.5, "พื้นฐาน"), ("คณิตศาสตร์", 1.5, "พื้นฐาน"),
        ("วิทยาศาสตร์", 1.5, "พื้นฐาน"), ("วิทยาการ", 1.0, "พื้นฐาน"),
        ("ประวัติ", 0.5, "พื้นฐาน"), ("สังคม", 1.5, "พื้นฐาน"),
        ("อังกฤษ", 1.5, "พื้นฐาน"), ("สุขพละ", 1.0, "พื้นฐาน"),
        ("สุข", 1.0, "พื้นฐาน"), ("พละ", 1.0, "พื้นฐาน"),
        ("ทัศนศิลป์", 1.0, "พื้นฐาน"), ("ดนตรี", 1.0, "พื้นฐาน"),
        ("การงาน", 1.0, "พื้นฐาน"), ("ออกแบบ", 1.0, "เพิ่มเติม"),
        ("ทักษะอาชีพ", 0.5, "เพิ่มเติม"), ("ต้านทุจริต", 0.5, "เพิ่มเติม"),
    ]
    for key, cr, stype in info_map:
        if key in subj_name:
            return cr, stype
    return 1.0, "พื้นฐาน"


# ---------------------------------------------------------------- สไตล์
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Prompt:wght@500;600;700&family=Sarabun:wght@400;500;600;700&display=swap');
:root{--ink:#141A3A;--teal:#2B3A9F;--teal-d:#1A2466;--mist:#EEF1FA;--line:#D5DBEE;--muted:#5B6488;--amber:#E7A33E;--paper:#FFFFFF;}
html,body,[class*="css"],.stMarkdown,.stTextInput,.stTabs{font-family:'Sarabun','TH Sarabun New',Thonburi,sans-serif;}
.stApp{background:var(--mist);color:var(--ink);}
#MainMenu,footer,header[data-testid="stHeader"]{visibility:hidden;height:0;}
.block-container{max-width:920px;padding:1.2rem 1rem 3rem 1rem;}
.hero{background:linear-gradient(135deg,var(--teal-d),var(--teal));color:#fff;border-radius:20px;padding:26px 28px;margin-bottom:18px;}
.hero h1{font-family:'Prompt',sans-serif;font-size:1.75rem;font-weight:600;margin:0 0 4px 0;color:#fff;padding:0;line-height:1.3;}
.hero p{margin:0;font-size:1.05rem;opacity:.88;}
[data-testid="stSidebar"],[data-testid="stSidebarCollapsedControl"],[data-testid="collapsedControl"]{display:none;}
.stTabs [data-baseweb="tab-list"]{gap:8px;background:transparent;border-bottom:none;flex-wrap:nowrap;}
.stTabs [data-baseweb="tab"]{flex:1;justify-content:center;background:var(--paper);border:1.5px solid var(--line);border-radius:12px;padding:12px 10px;height:auto;font-size:1.1rem;font-weight:600;color:var(--teal);box-shadow:0 2px 0 var(--line);white-space:nowrap;}
.stTabs [data-baseweb="tab"]:hover{border-color:var(--teal);}
.stTabs [aria-selected="true"]{background:var(--teal);color:#fff;border-color:var(--teal);box-shadow:0 2px 0 var(--teal-d);}
.stTabs [aria-selected="true"] p{color:#fff;}
.stTabs [data-baseweb="tab-highlight"],.stTabs [data-baseweb="tab-border"]{display:none;}
.stTabs .stTabs [data-baseweb="tab-list"]{gap:4px;border-bottom:2px solid var(--line);}
.stTabs .stTabs [data-baseweb="tab"]{flex:none;background:transparent;border:none;border-radius:0;box-shadow:none;padding:8px 18px;color:var(--muted);}
.stTabs .stTabs [aria-selected="true"]{background:transparent;color:var(--teal);box-shadow:inset 0 -3px 0 var(--teal);}
.stTabs .stTabs [aria-selected="true"] p{color:var(--teal);}
.tbl-wrap{overflow-x:auto;border:1px solid var(--line);border-radius:12px;margin-bottom:12px;}
.rt{width:100%;border-collapse:collapse;font-size:1.05rem;}
.rt th{background:var(--teal-d);color:#fff;font-weight:600;padding:10px 12px;text-align:center;white-space:nowrap;}
.rt td{padding:9px 12px;border-top:1px solid var(--line);text-align:center;}
.rt td.l{text-align:left;font-weight:600;}
.rt tbody tr:nth-child(even){background:#F6F8FD;}
.rt tfoot td{background:var(--mist);font-weight:700;border-top:2px solid var(--teal);}
.stTextInput input{font-size:1.15rem;padding:12px 14px;border-radius:12px;border:1.5px solid var(--line);background:#fff;}
.stTextInput input:focus{border-color:var(--teal);box-shadow:0 0 0 3px rgba(43,58,159,.15);}
.h2{font-family:'Prompt',sans-serif;font-size:1.35rem;font-weight:600;color:var(--teal-d);margin:26px 0 10px 0;}
.hint{color:var(--muted);font-size:1rem;margin:0 0 12px 0;}
.card{background:var(--paper);border:1px solid var(--line);border-radius:18px;padding:20px 22px;margin-bottom:16px;}
.rc-head{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;flex-wrap:wrap;border-bottom:1px dashed var(--line);padding-bottom:14px;margin-bottom:16px;}
.rc-school{font-size:.95rem;color:var(--muted);line-height:1.5;}
.rc-school b{color:var(--teal-d);font-size:1.1rem;}
.rc-term{background:var(--mist);color:var(--teal-d);font-weight:600;border-radius:999px;padding:4px 14px;font-size:.95rem;white-space:nowrap;}
.rc-name{font-family:'Prompt',sans-serif;font-size:1.6rem;font-weight:600;margin:0;line-height:1.35;}
.rc-meta{color:var(--muted);font-size:1.05rem;margin-bottom:16px;}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:18px;}
.stat{background:var(--mist);border-radius:14px;padding:12px 14px;}
.stat .k{font-size:.92rem;color:var(--muted);}
.stat .v{font-family:'Prompt',sans-serif;font-size:1.8rem;font-weight:600;color:var(--teal-d);line-height:1.25;}
.stat .v small{font-size:.95rem;font-weight:500;color:var(--muted);}
.stat.main{background:var(--teal);}
.stat.main .k{color:#D3D9F5;}
.stat.main .v{color:#fff;}
.subj{display:flex;align-items:center;gap:12px;padding:11px 0;border-bottom:1px solid var(--mist);}
.subj:last-of-type{border-bottom:none;}
.subj .nm{flex:1;min-width:0;}
.subj .nm b{font-weight:600;font-size:1.1rem;display:block;line-height:1.35;}
.subj .nm span{color:var(--muted);font-size:.92rem;}
.chip{min-width:52px;text-align:center;font-family:'Prompt',sans-serif;font-weight:600;font-size:1.25rem;border-radius:12px;padding:5px 10px;color:#fff;}
.g4{background:#1E8E5A;}.g3{background:#2A7FB8;}.g2{background:#C99A1B;}.g1{background:#D9772B;}.g0{background:#C8453A;}.gx{background:#8A9BA5;}
.wait{background:#FFF1D6;color:#8A5A00;font-size:.95rem;font-weight:600;border-radius:999px;padding:4px 12px;}
.foot{color:var(--muted);font-size:.95rem;margin-top:12px;padding-top:12px;border-top:1px dashed var(--line);}
.kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:6px;}
.kpi{background:var(--paper);border:1px solid var(--line);border-radius:16px;padding:16px 18px;}
.kpi .k{color:var(--muted);font-size:.95rem;}
.kpi .v{font-family:'Prompt',sans-serif;font-size:1.9rem;font-weight:600;color:var(--teal-d);line-height:1.3;}
.bar{background:var(--mist);border-radius:999px;height:12px;overflow:hidden;}
.bar i{display:block;height:100%;border-radius:999px;background:var(--teal);}
.cls-row{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px;}
.cls-row b{font-family:'Prompt',sans-serif;font-size:1.15rem;}
.cls-row span{color:var(--muted);font-size:.98rem;}
.top{display:flex;align-items:center;gap:14px;padding:11px 0;border-bottom:1px solid var(--mist);}
.top:last-child{border-bottom:none;}
.rk{width:38px;height:38px;border-radius:50%;background:var(--mist);display:flex;align-items:center;justify-content:center;font-family:'Prompt',sans-serif;font-weight:600;color:var(--teal-d);flex:none;}
.rk.r1{background:#F4C542;color:#5A4200;}.rk.r2{background:#C9D3D8;color:#33385A;}.rk.r3{background:#E0A878;color:#5A3210;}
.top .nm{flex:1;font-weight:600;font-size:1.1rem;}
.top .no{color:var(--muted);font-size:.92rem;font-weight:400;display:block;}
.top .gp{font-family:'Prompt',sans-serif;font-weight:600;font-size:1.25rem;color:var(--teal-d);}
.avg{display:grid;grid-template-columns:minmax(120px,32%) 1fr 52px;gap:12px;align-items:center;padding:7px 0;}
.avg .l{font-size:1.02rem;line-height:1.3;}
.avg .n{text-align:right;font-family:'Prompt',sans-serif;font-weight:600;}
.avg .bar i.g4{background:#1E8E5A;}.avg .bar i.g3{background:#2A7FB8;}.avg .bar i.g2{background:#C99A1B;}.avg .bar i.g1{background:#D9772B;}.avg .bar i.g0{background:#C8453A;}.avg .bar i.gx{background:#8A9BA5;}
@media (max-width:600px){.block-container{padding:.8rem .6rem 2.5rem .6rem;}.stTabs [data-baseweb="tab"]{padding:10px 4px;font-size:1rem;}.rt{font-size:.95rem;}.rt th,.rt td{padding:8px 6px;}.rc-name{font-size:1.35rem;}.top .nm{font-size:1rem;}.stTextInput input{font-size:1.05rem;}.hero{padding:20px;}.hero h1{font-size:1.4rem;}.stats,.kpis{grid-template-columns:1fr 1fr 1fr;gap:8px;}.stat .v,.kpi .v{font-size:1.4rem;}.avg{grid-template-columns:1fr 46px;}.avg .bar{grid-column:1 / 3;grid-row:2;}.card{padding:16px;}}
</style>
"""
st.markdown(clean_html(CSS), unsafe_allow_html=True)


# ---------------------------------------------------------------- ข้อมูล
def load_sheet_data(sheet_name):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(sheet_name)}"
        df_raw = pd.read_csv(url, header=None)

        header_idx = None
        for idx, row in df_raw.iterrows():
            if row.astype(str).str.contains("ชื่อ - นามสกุล|ชื่อ-นามสกุล|ชื่อนามสกุล").any():
                header_idx = idx
                break
        if header_idx is None:
            return pd.DataFrame(), []

        df = pd.read_csv(url, header=header_idx)
        df.columns = [str(c).strip() for c in df.columns]
        name_col = next((c for c in df.columns if "ชื่อ" in c and "นามสกุล" in c), None)
        if not name_col:
            return pd.DataFrame(), []

        df = df[df[name_col].astype(str).str.strip() != name_col]
        df = df.dropna(subset=[name_col])
        df = df[df[name_col].astype(str).str.strip() != ""]
        if name_col != "ชื่อ - นามสกุล":
            df = df.rename(columns={name_col: "ชื่อ - นามสกุล"})

        cols = [c for c in df.columns if not str(c).startswith("Unnamed") and "merged" not in str(c).lower()]
        df = df[cols]

        skip = ["เลขที่", "ชื่อ - นามสกุล", "เกรดเฉลี่ย", "ลำดับที่", "รวม", "เฉลี่ย", "ผลการเรียน"]
        subject_cols = [c for c in df.columns if c not in skip]

        def calc_gpa(row):
            pts = crs = 0
            for col in subject_cols:
                credit, _ = get_subject_info(col)
                try:
                    v = float(row[col])
                    if not np.isnan(v):
                        pts += v * credit
                        crs += credit
                except (ValueError, TypeError):
                    pass
            return round(pts / crs, 2) if crs > 0 else np.nan

        df["เกรดเฉลี่ย"] = df.apply(calc_gpa, axis=1)
        df["ลำดับที่"] = df["เกรดเฉลี่ย"].rank(ascending=False, method="min").astype("Int64")
        return df, subject_cols
    except Exception as e:
        st.error(f"ไม่สามารถโหลดข้อมูลแผ่นงาน {sheet_name} ได้: {e}")
        return pd.DataFrame(), []


@st.cache_data(ttl=300, show_spinner="กำลังโหลดข้อมูลล่าสุด...")
def load_all_data():
    data, subjects = {}, {}
    for sheet in SHEET_NAMES:
        df, subjs = load_sheet_data(sheet)
        if not df.empty:
            data[sheet], subjects[sheet] = df, subjs
    return data, subjects


def is_missing(v):
    return pd.isna(v) or str(v).strip().lower() in ("", "nan", "none")


def grade_class(v):
    try:
        g = float(v)
    except (ValueError, TypeError):
        return "gx"
    if g >= 3.5: return "g4"
    if g >= 2.5: return "g3"
    if g >= 1.5: return "g2"
    if g >= 0.5: return "g1"
    return "g0"


def fmt_grade(v):
    try:
        g = float(v)
        return str(int(g)) if g == int(g) else f"{g:.1f}"
    except (ValueError, TypeError):
        return esc(v)


# ---------------------------------------------------------------- ส่วนแสดงผล
def render_report(row, sheet_name, subject_cols, total_students):
    no = int(row["เลขที่"]) if pd.notna(row.get("เลขที่")) else "-"
    gpa = f"{row['เกรดเฉลี่ย']:.2f}" if pd.notna(row["เกรดเฉลี่ย"]) else "-"
    rank = row["ลำดับที่"] if pd.notna(row["ลำดับที่"]) else "-"
    basic = extra = 0.0
    rows = ""
    for col in subject_cols:
        credit, stype = get_subject_info(col)
        if stype == "พื้นฐาน":
            basic += credit
        else:
            extra += credit
        v = row[col]
        right = '<span class="wait">รอผล</span>' if is_missing(v) else f'<span class="chip {grade_class(v)}">{fmt_grade(v)}</span>'
        rows += f'<tr><td>{len(rows.split("<tr>"))}</td><td class="l">{esc(col)}</td><td>{stype}</td><td>{credit:.1f}</td><td>{right}</td></tr>'

    return clean_html(f"""
<div class="card">
<div class="rc-head">
<div class="rc-school"><b>{SCHOOL_NAME}</b><br>{SCHOOL_DISTRICT}</div>
<div class="rc-term">ภาคเรียนที่ {SEMESTER}/{ACADEMIC_YEAR}</div>
</div>
<p class="rc-name">{esc(row['ชื่อ - นามสกุล'])}</p>
<div class="rc-meta">ชั้น {esc(sheet_name)} &nbsp;|&nbsp; เลขที่ {no}</div>
<div class="stats">
<div class="stat main"><div class="k">เกรดเฉลี่ย</div><div class="v">{gpa}</div></div>
<div class="stat"><div class="k">อันดับในห้อง</div><div class="v">{rank} <small>/ {total_students}</small></div></div>
<div class="stat"><div class="k">หน่วยกิตรวม</div><div class="v">{basic + extra:.1f}</div></div>
</div>
<div class="tbl-wrap"><table class="rt">
<thead><tr><th>ลำดับ</th><th>ชื่อวิชา</th><th>ประเภท</th><th>หน่วยกิต</th><th>ผลการเรียน</th></tr></thead>
<tbody>{rows}</tbody>
<tfoot><tr><td colspan="3">รวมหน่วยกิต (พื้นฐาน {basic:.1f} + เพิ่มเติม {extra:.1f})</td><td>{basic + extra:.1f}</td><td>GPA {gpa}</td></tr></tfoot>
</table></div>
</div>""")


def render_top5(df):
    out = ""
    for _, r in df.iterrows():
        rk = int(r["ลำดับที่"]) if pd.notna(r["ลำดับที่"]) else 0
        no = int(r["เลขที่"]) if pd.notna(r.get("เลขที่")) else "-"
        cls = f"r{rk}" if rk in (1, 2, 3) else ""
        out += f'<div class="top"><div class="rk {cls}">{rk}</div><div class="nm">{esc(r["ชื่อ - นามสกุล"])}<span class="no">เลขที่ {no}</span></div><div class="gp">{r["เกรดเฉลี่ย"]:.2f}</div></div>'
    return clean_html(f'<div class="card" style="padding:8px 22px;">{out}</div>')


# ---------------------------------------------------------------- หน้าเว็บ
st.markdown(clean_html(f"""
<div class="hero"><h1>ผลการเรียนออนไลน์</h1>
<p>{SCHOOL_NAME} | ภาคเรียนที่ {SEMESTER} ปีการศึกษา {ACADEMIC_YEAR}</p></div>"""), unsafe_allow_html=True)

all_data, all_subject_cols = load_all_data()
tab_student, tab_dash, tab_teacher = st.tabs(["🔍 ผลการเรียน", "📊 ภาพรวม", "🔑 ครู"])
# ---- 1. นักเรียน
with tab_student:
    st.markdown('<p class="hint">พิมพ์ชื่อหรือนามสกุลของนักเรียน อย่างน้อย 2 ตัวอักษร</p>', unsafe_allow_html=True)
    q = st.text_input("ค้นหาชื่อ", placeholder="เช่น สมชาย", label_visibility="collapsed").strip()

    if len(q) == 1:
        st.info("พิมพ์เพิ่มอีกอย่างน้อย 1 ตัวอักษร")
    elif q:
        found = 0
        for sheet, df in all_data.items():
            hits = df[df["ชื่อ - นามสกุล"].astype(str).str.contains(q, na=False, case=False, regex=False)]
            for _, s in hits.head(10).iterrows():
                found += 1
                st.markdown(render_report(s, sheet, all_subject_cols[sheet], len(df)), unsafe_allow_html=True)
        if not found:
            st.warning("ไม่พบรายชื่อนี้ ลองตรวจการสะกดหรือค้นด้วยนามสกุลแทน")

# ---- 2. แดชบอร์ด
with tab_dash:
    progress, tot_all, filled_all = {}, 0, 0
    for sheet, df in all_data.items():
        subjs = all_subject_cols[sheet]
        total = len(df) * len(subjs)
        filled = int(sum((~df[c].apply(is_missing)).sum() for c in subjs))
        progress[sheet] = dict(total=total, filled=filled, pct=round(filled / total * 100, 1) if total else 0,
                               n=len(df), gpa=df["เกรดเฉลี่ย"].mean())
        tot_all += total
        filled_all += filled
    overall = round(filled_all / tot_all * 100, 1) if tot_all else 0

    st.markdown('<div class="h2">ความคืบหน้าการบันทึกคะแนน</div>', unsafe_allow_html=True)
    st.markdown(clean_html(f"""
<div class="kpis">
<div class="kpi"><div class="k">ความคืบหน้ารวม</div><div class="v">{overall}%</div></div>
<div class="kpi"><div class="k">กรอกแล้ว</div><div class="v">{filled_all:,}</div></div>
<div class="kpi"><div class="k">คงเหลือ</div><div class="v">{tot_all - filled_all:,}</div></div>
</div>"""), unsafe_allow_html=True)

    cls_html = ""
    for sheet in SHEET_NAMES:
        p = progress.get(sheet)
        if not p:
            continue
        gpa_txt = f"{p['gpa']:.2f}" if pd.notna(p["gpa"]) else "-"
        cls_html += f'<div style="margin-bottom:16px;"><div class="cls-row"><b>{sheet}</b><span>{p["n"]} คน | เกรดเฉลี่ยห้อง {gpa_txt} | กรอกแล้ว {p["pct"]}%</span></div><div class="bar"><i style="width:{p["pct"]}%"></i></div></div>'
    st.markdown(clean_html(f'<div class="card" style="margin-top:12px;padding-bottom:6px;">{cls_html}</div>'), unsafe_allow_html=True)

    st.markdown('<div class="h2">5 อันดับเกรดเฉลี่ยสูงสุด</div>', unsafe_allow_html=True)
    tops = st.tabs([f"ชั้น {s}" for s in SHEET_NAMES])
    for t, sheet in zip(tops, SHEET_NAMES):
        with t:
            if sheet in all_data:
                top5 = all_data[sheet].dropna(subset=["เกรดเฉลี่ย"]).sort_values("เกรดเฉลี่ย", ascending=False).head(5)
                st.markdown(render_top5(top5), unsafe_allow_html=True)
            else:
                st.info("ยังไม่มีข้อมูลชั้นนี้")

    st.markdown('<div class="h2">เกรดเฉลี่ยรายวิชา</div>', unsafe_allow_html=True)
    pick = st.radio("ชั้น", SHEET_NAMES, horizontal=True, label_visibility="collapsed")
    if pick in all_data:
        bars = ""
        for col in all_subject_cols[pick]:
            vals = pd.to_numeric(all_data[pick][col], errors="coerce").dropna()
            avg = round(vals.mean(), 2) if len(vals) else 0.0
            bars += f'<div class="avg"><div class="l">{esc(col)}</div><div class="bar"><i class="{grade_class(avg)}" style="width:{avg / 4 * 100:.0f}%"></i></div><div class="n">{avg:.2f}</div></div>'
        st.markdown(clean_html(f'<div class="card">{bars}</div>'), unsafe_allow_html=True)

# ---- 3. ครู
with tab_teacher:
    pw = st.text_input("รหัสผ่านสำหรับคุณครู", type="password")
    if pw and pw == TEACHER_PASSWORD:
        st.success("ยืนยันตัวตนสำเร็จ")
        st.link_button("เปิด Google Sheet เพื่อแก้ไขคะแนน", GSHEET_URL)
        sel = st.selectbox("ดูตารางคะแนนล่าสุด", SHEET_NAMES)
        if sel in all_data:
            st.dataframe(all_data[sel], use_container_width=True, hide_index=True)
        if st.button("โหลดข้อมูลใหม่จาก Google Sheet"):
            load_all_data.clear()
            st.rerun()
    elif pw:
        st.error("รหัสผ่านไม่ถูกต้อง")
