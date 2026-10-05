import html
import os
from datetime import datetime, timedelta, timezone
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
TEACHER_PASSWORD = st.secrets.get("TEACHER_PASSWORD", "57030121")


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
:root{--bg:#EAF4FF;--ink:#12305F;--muted:#5B6F94;--accent:#1E6FEB;--accent-d:#0B57D0;--card:rgba(255,255,255,.9);--card-b:rgba(30,111,235,.16);--line:rgba(30,111,235,.14);--amber:#B26A00;}
html,body,[class*="css"],.stMarkdown,.stTextInput,.stTabs{font-family:'Sarabun','TH Sarabun New',Thonburi,sans-serif;}
.stApp{background:radial-gradient(900px 480px at 85% -8%,#1D3F82 0%,transparent 60%),radial-gradient(700px 400px at -10% 8%,#0E4A68 0%,transparent 55%),var(--bg);background-attachment:fixed;color:var(--ink);}
#MainMenu,footer,header[data-testid="stHeader"]{visibility:hidden;height:0;}
[data-testid="stSidebar"],[data-testid="stSidebarCollapsedControl"],[data-testid="collapsedControl"]{display:none;}
.block-container{max-width:880px;padding:1.4rem 1rem 3rem 1rem;}
.hero{padding:10px 4px 22px 4px;}
.pill{display:inline-flex;align-items:center;gap:9px;background:var(--card);border:1px solid var(--card-b);border-radius:999px;padding:6px 15px;font-size:.95rem;color:var(--muted);}
.pill .dot{width:8px;height:8px;border-radius:50%;background:var(--accent);box-shadow:0 0 0 4px rgba(94,234,212,.2);}
.hero h1{font-family:'Prompt',sans-serif;font-size:2.5rem;font-weight:600;line-height:1.25;margin:18px 0 10px 0;padding:0;color:var(--ink);}
.hero h1 span{color:var(--accent);}
.hero p{margin:0 0 6px 0;font-size:1.1rem;color:var(--muted);line-height:1.6;}
.hero .sch{font-size:.98rem;color:var(--accent);font-weight:600;}
.stTabs [data-baseweb="tab-list"]{gap:4px;background:var(--card);border:1px solid var(--card-b);border-radius:999px;padding:5px;flex-wrap:nowrap;}
.stTabs button[data-baseweb="tab"]{flex:1 1 0;justify-content:center;background:transparent;border:none;border-radius:999px;padding:10px 8px;height:auto;white-space:nowrap;}
.stTabs button[data-baseweb="tab"] p{font-size:1.08rem;font-weight:600;color:var(--muted);margin:0;}
.stTabs button[data-baseweb="tab"]:hover p{color:var(--ink);}
.stTabs button[data-baseweb="tab"][aria-selected="true"]{background:var(--accent);}
.stTabs button[data-baseweb="tab"][aria-selected="true"] p{color:#05302B;}
.stTabs [data-baseweb="tab-highlight"],.stTabs [data-baseweb="tab-border"]{display:none;}
.stTabs .stTabs [data-baseweb="tab-list"]{background:transparent;border:none;padding:0;gap:8px;}
.stTabs .stTabs button[data-baseweb="tab"]{flex:none;border:1px solid var(--card-b);padding:7px 18px;}
.stTabs .stTabs button[data-baseweb="tab"] p{font-size:1rem;}
.stApp [data-baseweb="input"],.stApp [data-baseweb="base-input"]{background:rgba(255,255,255,.07) !important;border-radius:16px;}
.stApp [data-baseweb="input"]{border:1.5px solid var(--card-b) !important;}
.stApp [data-baseweb="input"]:focus-within{border-color:var(--accent) !important;box-shadow:0 0 0 3px rgba(94,234,212,.18);}
.stApp .stTextInput input{font-size:1.15rem;padding:13px 16px;color:var(--ink) !important;-webkit-text-fill-color:var(--ink) !important;background:transparent !important;}
.stApp .stTextInput input::placeholder{color:#7F90B8 !important;-webkit-text-fill-color:#7F90B8 !important;opacity:1;}
.stApp [data-baseweb="select"]>div{background:rgba(255,255,255,.07) !important;border-radius:14px;color:var(--ink) !important;}
.stApp [data-testid="stWidgetLabel"] p,.stApp .stRadio label p{color:var(--ink) !important;}
.stApp .stButton button,.stApp .stLinkButton a{border-radius:999px;font-weight:600;}
.h2{font-family:'Prompt',sans-serif;font-size:1.3rem;font-weight:600;color:var(--ink);margin:26px 0 12px 0;}
.hint{color:var(--muted);font-size:1.02rem;margin:14px 0 10px 0;}
.card{background:var(--card);border:1px solid var(--card-b);border-radius:22px;padding:20px 22px;margin-bottom:16px;backdrop-filter:blur(8px);}
.rc-head{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;flex-wrap:wrap;border-bottom:1px dashed var(--line);padding-bottom:14px;margin-bottom:16px;}
.rc-school{font-size:.95rem;color:var(--muted);line-height:1.5;}
.rc-school b{color:var(--ink);font-size:1.1rem;}
.rc-term{background:rgba(94,234,212,.14);color:var(--accent);font-weight:600;border-radius:999px;padding:4px 14px;font-size:.95rem;white-space:nowrap;}
.rc-name{font-family:'Prompt',sans-serif;font-size:1.7rem;font-weight:600;margin:0;line-height:1.35;color:var(--ink);}
.rc-meta{color:var(--muted);font-size:1.05rem;margin-bottom:16px;}
.stats,.kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:18px;}
.kpis{margin-bottom:6px;}
.stat,.kpi{background:rgba(255,255,255,.07);border:1px solid var(--line);border-radius:18px;padding:13px 15px;}
.stat .k,.kpi .k{font-size:.93rem;color:var(--muted);}
.stat .v,.kpi .v{font-family:'Prompt',sans-serif;font-size:1.85rem;font-weight:600;color:var(--ink);line-height:1.25;}
.stat .v small{font-size:.95rem;font-weight:500;color:var(--muted);}
.stat.main{background:linear-gradient(135deg,#14B8A6,#2B6CB0);border:none;}
.stat.main .k{color:rgba(255,255,255,.88);}
.stat.main .v{color:#fff;}
.tbl-wrap{overflow-x:auto;border:1px solid var(--line);border-radius:16px;margin-bottom:6px;}
.rt{width:100%;border-collapse:collapse;font-size:1.05rem;color:var(--ink);}
.rt th{background:rgba(255,255,255,.09);color:var(--muted);font-weight:600;padding:11px 12px;text-align:center;white-space:nowrap;}
.rt td{padding:10px 12px;border-top:1px solid var(--line);text-align:center;}
.rt td.l{text-align:left;font-weight:600;}
.rt tbody tr:nth-child(even){background:rgba(255,255,255,.035);}
.rt tfoot td{background:rgba(94,234,212,.08);font-weight:700;border-top:2px solid var(--accent);color:var(--accent);}
.chip{display:inline-block;min-width:52px;text-align:center;font-family:'Prompt',sans-serif;font-weight:600;font-size:1.2rem;border-radius:12px;padding:4px 10px;color:#fff;}
.g4{background:#1FA971;}.g3{background:#3B82F6;}.g2{background:#D6A21A;}.g1{background:#E8812F;}.g0{background:#E5484D;}.gx{background:#6B7A99;}
.wait{background:rgba(244,197,66,.15);color:var(--amber);font-size:.95rem;font-weight:600;border-radius:999px;padding:4px 12px;}
.bar{background:rgba(255,255,255,.1);border-radius:999px;height:12px;overflow:hidden;}
.bar i{display:block;height:100%;border-radius:999px;background:linear-gradient(90deg,var(--accent-d),var(--accent));}
.cls-row{display:flex;justify-content:space-between;align-items:baseline;gap:8px;flex-wrap:wrap;margin-bottom:7px;}
.cls-row b{font-family:'Prompt',sans-serif;font-size:1.15rem;color:var(--ink);}
.cls-row span{color:var(--muted);font-size:.98rem;}
.top{display:flex;align-items:center;gap:14px;padding:11px 0;border-bottom:1px solid var(--line);}
.top:last-child{border-bottom:none;}
.rk{width:38px;height:38px;border-radius:50%;background:rgba(255,255,255,.1);display:flex;align-items:center;justify-content:center;font-family:'Prompt',sans-serif;font-weight:600;color:var(--ink);flex:none;}
.rk.r1{background:#F4C542;color:#4A3600;}.rk.r2{background:#CBD5E1;color:#26304A;}.rk.r3{background:#E0A878;color:#4A2A10;}
.top .nm{flex:1;font-weight:600;font-size:1.1rem;color:var(--ink);}
.top .no{color:var(--muted);font-size:.92rem;font-weight:400;display:block;}
.top .gp{font-family:'Prompt',sans-serif;font-weight:600;font-size:1.25rem;color:var(--accent);}
.avg{display:grid;grid-template-columns:minmax(120px,32%) 1fr 52px;gap:12px;align-items:center;padding:7px 0;}
.avg .l{font-size:1.02rem;line-height:1.3;color:var(--ink);}
.avg .n{text-align:right;font-family:'Prompt',sans-serif;font-weight:600;color:var(--ink);}
.avg .bar i.g4{background:#1FA971;}.avg .bar i.g3{background:#3B82F6;}.avg .bar i.g2{background:#D6A21A;}.avg .bar i.g1{background:#E8812F;}.avg .bar i.g0{background:#E5484D;}.avg .bar i.gx{background:#6B7A99;}
.how{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:14px;}
.how .it{background:var(--card);border:1px solid var(--card-b);border-radius:20px;padding:16px 18px;}
.how .ic{font-size:1.7rem;margin-bottom:6px;}
.how b{display:block;font-size:1.1rem;color:var(--ink);margin-bottom:3px;}
.how span{color:var(--muted);font-size:.98rem;line-height:1.5;}
.note{background:rgba(244,197,66,.1);border:1px solid rgba(244,197,66,.3);color:#F7DC8A;border-radius:16px;padding:12px 16px;font-size:.98rem;line-height:1.6;}
.pgfoot{text-align:center;color:var(--muted);font-size:.9rem;line-height:1.7;margin-top:34px;}
@media (max-width:600px){.block-container{padding:1rem .7rem 2.5rem .7rem;}.hero h1{font-size:1.9rem;}.stTabs button[data-baseweb="tab"]{padding:9px 4px;}.stTabs button[data-baseweb="tab"] p{font-size:1rem;}.rt{font-size:.95rem;}.rt th,.rt td{padding:8px 6px;}.rc-name{font-size:1.4rem;}.top .nm{font-size:1rem;}.stats,.kpis{gap:8px;}.stat,.kpi{padding:11px 11px;}.stat .v,.kpi .v{font-size:1.4rem;}.avg{grid-template-columns:1fr 46px;}.avg .bar{grid-column:1 / 3;grid-row:2;}.card{padding:16px;}.how{grid-template-columns:1fr;}}
.stApp{color-scheme:light;background:linear-gradient(180deg,#D6ECFF 0%,#F2F9FF 55%,#FFFFFF 100%) !important;color:var(--ink);}
.hero{background:rgba(255,255,255,.78);backdrop-filter:blur(10px);border:1px solid var(--card-b);border-radius:26px;padding:22px 24px 20px 24px;margin-bottom:18px;box-shadow:0 8px 28px rgba(30,111,235,.12);}
.hero h1 span{color:#F59E0B;}
.hero .sch{color:var(--accent);}
.pill{background:#fff;}
.pill .dot{background:#22C55E;box-shadow:0 0 0 4px rgba(34,197,94,.2);}
.card{box-shadow:0 6px 20px rgba(30,111,235,.08);}
.rc-term{background:rgba(30,111,235,.1);color:var(--accent);}
.stat,.kpi{background:rgba(30,111,235,.06);}
.stat.main{background:linear-gradient(135deg,#1E6FEB,#38BDF8);}
.rt th{background:rgba(30,111,235,.1);color:var(--ink);}
.rt tbody tr:nth-child(even){background:rgba(30,111,235,.04);}
.rt tfoot td{background:rgba(30,111,235,.08);color:var(--accent);}
.wait{background:rgba(255,183,3,.22);color:#8A5200;}
.bar{background:rgba(30,111,235,.12);}
.rk{background:rgba(30,111,235,.1);}
.note{background:rgba(255,183,3,.16);border-color:rgba(255,183,3,.55);color:#7A4A00;}
.stApp .stTabs [data-baseweb="tab-list"]{background:rgba(255,255,255,.92) !important;border:1px solid var(--card-b) !important;border-radius:999px !important;padding:5px !important;gap:4px !important;}
.stApp .stTabs button[data-baseweb="tab"]{flex:1 1 0 !important;background:transparent !important;border:none !important;border-radius:999px !important;padding:10px 8px !important;height:auto !important;justify-content:center !important;}
.stApp .stTabs button[data-baseweb="tab"] p{color:var(--muted) !important;font-weight:600 !important;}
.stApp .stTabs button[data-baseweb="tab"][aria-selected="true"]{background:var(--accent) !important;}
.stApp .stTabs button[data-baseweb="tab"][aria-selected="true"] p{color:#fff !important;}
.stApp .stTabs [data-baseweb="tab-highlight"],.stApp .stTabs [data-baseweb="tab-border"]{display:none !important;}
.stApp .stTabs .stTabs [data-baseweb="tab-list"]{background:transparent !important;border:none !important;padding:0 !important;gap:8px !important;}
.stApp .stTabs .stTabs button[data-baseweb="tab"]{flex:none !important;background:rgba(255,255,255,.92) !important;border:1px solid var(--card-b) !important;padding:7px 18px !important;}
.stApp .stTabs .stTabs button[data-baseweb="tab"][aria-selected="true"]{background:var(--accent) !important;}
.stApp [data-baseweb="input"],.stApp [data-baseweb="base-input"],.stApp .stTextInput input{background:#fff !important;}
.stApp [data-baseweb="input"]{border:2px solid rgba(30,111,235,.35) !important;border-radius:16px !important;box-shadow:0 4px 14px rgba(30,111,235,.12) !important;}
.stApp [data-baseweb="input"]:focus-within{border-color:var(--accent) !important;}
.stApp .stTextInput input{color:#12305F !important;-webkit-text-fill-color:#12305F !important;caret-color:#1E6FEB !important;font-size:1.2rem !important;}
.stApp .stTextInput input::placeholder{color:#8EA0C4 !important;-webkit-text-fill-color:#8EA0C4 !important;opacity:1;}
.stApp [data-baseweb="select"]>div{background:#fff !important;color:#12305F !important;}
.stApp .stButton button,.stApp .stLinkButton a{background:var(--accent) !important;color:#fff !important;border:none !important;}
.stApp .stButton button p,.stApp .stLinkButton a p{color:#fff !important;}
</style>
"""
st.markdown(clean_html(CSS), unsafe_allow_html=True)


BG_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 900" preserveAspectRatio="xMidYMax slice"><defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#6FC3FF"/><stop offset="1" stop-color="#EAF7FF"/></linearGradient><radialGradient id="glow"><stop offset="0" stop-color="#FFE98A" stop-opacity=".9"/><stop offset="1" stop-color="#FFE98A" stop-opacity="0"/></radialGradient><g id="cloud"><ellipse cx="0" cy="0" rx="90" ry="32"/><circle cx="-35" cy="-22" r="34"/><circle cx="20" cy="-34" r="42"/><circle cx="62" cy="-10" r="26"/></g></defs><rect width="1600" height="900" fill="url(#sky)"/><circle cx="1330" cy="140" r="150" fill="url(#glow)"/><circle cx="1330" cy="140" r="68" fill="#FFD54A"/><g fill="#fff" opacity=".95"><use href="#cloud" x="300" y="150"/><use href="#cloud" x="780" y="95" transform="translate(0 0)"/><use href="#cloud" x="1060" y="250"/><use href="#cloud" x="1500" y="360" transform="translate(0 0)"/></g><g fill="none" stroke="#35538F" stroke-width="4" stroke-linecap="round"><path d="M640 220q14-16 28 0q14-16 28 0"/><path d="M700 260q10-12 20 0q10-12 20 0"/><path d="M1130 120q12-14 24 0q12-14 24 0"/></g><path d="M0 610Q300 470 620 580T1200 550T1600 530V900H0Z" fill="#B4EBC0"/><path d="M0 690Q420 560 820 660T1600 640V900H0Z" fill="#86DC9E"/><rect y="745" width="1600" height="155" fill="#5CC97B"/><path d="M0 790Q400 765 800 790T1600 780V900H0Z" fill="#4DBB6D"/><path d="M262 745H338L580 900H100Z" fill="#F6E7BE"/><g><rect x="60" y="620" width="90" height="125" fill="#FFD98A"/><rect x="450" y="620" width="90" height="125" fill="#FFD98A"/><rect x="130" y="560" width="340" height="185" fill="#FFE9A8"/><polygon points="105,562 300,468 495,562" fill="#FF7A59"/><polygon points="40,622 105,576 170,622" fill="#F2674F"/><polygon points="430,622 495,576 560,622" fill="#F2674F"/><circle cx="300" cy="528" r="24" fill="#fff" stroke="#FFB703" stroke-width="6"/><path d="M300 528V512M300 528L312 534" stroke="#35538F" stroke-width="4" stroke-linecap="round"/><g fill="#9AD8FF" stroke="#fff" stroke-width="4"><rect x="150" y="598" width="42" height="52" rx="6"/><rect x="212" y="598" width="42" height="52" rx="6"/><rect x="346" y="598" width="42" height="52" rx="6"/><rect x="408" y="598" width="42" height="52" rx="6"/><rect x="79" y="655" width="42" height="48" rx="6"/><rect x="479" y="655" width="42" height="48" rx="6"/></g><g stroke="#fff" stroke-width="3"><path d="M171 598V650M150 624H192M233 598V650M212 624H254M367 598V650M346 624H388M429 598V650M408 624H450"/></g><rect x="272" y="640" width="56" height="105" rx="8" fill="#4C8DF6"/><path d="M300 640V745" stroke="#fff" stroke-width="3"/><circle cx="292" cy="696" r="3.5" fill="#fff"/><circle cx="308" cy="696" r="3.5" fill="#fff"/><rect x="258" y="732" width="84" height="13" rx="4" fill="#E8D5A2"/></g><g><line x1="590" y1="470" x2="590" y2="745" stroke="#9AA7B8" stroke-width="6" stroke-linecap="round"/><circle cx="590" cy="466" r="7" fill="#F5B72E"/><rect x="596" y="480" width="86" height="6" fill="#E5384B"/><rect x="596" y="486" width="86" height="6" fill="#fff"/><rect x="596" y="492" width="86" height="12" fill="#2B4C9B"/><rect x="596" y="504" width="86" height="6" fill="#fff"/><rect x="596" y="510" width="86" height="6" fill="#E5384B"/></g><g><rect x="880" y="665" width="215" height="78" rx="20" fill="#FFC83D"/><rect x="880" y="722" width="215" height="9" fill="#F59E0B"/><g fill="#BDE8FF"><rect x="897" y="681" width="34" height="30" rx="6"/><rect x="940" y="681" width="34" height="30" rx="6"/><rect x="983" y="681" width="34" height="30" rx="6"/><rect x="1050" y="681" width="32" height="38" rx="6"/></g><g fill="#35405A"><circle cx="940" cy="744" r="19"/><circle cx="1042" cy="744" r="19"/></g><g fill="#CBD5E1"><circle cx="940" cy="744" r="7"/><circle cx="1042" cy="744" r="7"/></g></g><g><rect x="1233" y="555" width="34" height="195" rx="8" fill="#A9714B"/><g fill="#3FB56B"><circle cx="1250" cy="515" r="92"/><circle cx="1182" cy="572" r="62"/><circle cx="1320" cy="572" r="66"/><circle cx="1250" cy="450" r="60"/></g><g fill="#5BD184" opacity=".7"><circle cx="1225" cy="490" r="34"/><circle cx="1290" cy="540" r="26"/><circle cx="1175" cy="560" r="22"/></g><rect x="1470" y="640" width="18" height="110" rx="6" fill="#A9714B"/><g fill="#3FB56B"><circle cx="1479" cy="615" r="52"/><circle cx="1438" cy="650" r="36"/><circle cx="1520" cy="650" r="38"/></g><g fill="#3FB56B"><ellipse cx="700" cy="748" rx="55" ry="30"/><ellipse cx="750" cy="755" rx="40" ry="22"/><ellipse cx="30" cy="750" rx="60" ry="32"/></g><g fill="#5BD184" opacity=".7"><ellipse cx="690" cy="740" rx="26" ry="14"/><ellipse cx="20" cy="742" rx="28" ry="15"/></g></g><g><g fill="#FF8FB1"><circle cx="420" cy="815"  r="7"/><circle cx="780" cy="830" r="7"/><circle cx="1180" cy="820" r="7"/><circle cx="1400" cy="845" r="7"/></g><g fill="#fff"><circle cx="460" cy="835" r="6"/><circle cx="860" cy="815" r="6"/><circle cx="1120" cy="850" r="6"/><circle cx="1540" cy="830" r="6"/></g></g></svg>"""


def bg_css():
    import base64
    data = base64.b64encode(BG_SVG.encode("utf-8")).decode()
    return (
        "<style>.stApp{background-color:#EAF7FF !important;"
        f"background-image:url(data:image/svg+xml;base64,{data}) !important;"
        "background-size:cover !important;background-position:center bottom !important;"
        "background-repeat:no-repeat !important;background-attachment:fixed !important;}"
        "@media (max-width:700px){.stApp{background-position:18% bottom !important;}}</style>"
    )


st.markdown(bg_css(), unsafe_allow_html=True)


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
TH_MONTHS = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
             "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]
TH_DAYS = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]


def thai_now():
    n = datetime.now(timezone(timedelta(hours=7)))
    return f"วัน{TH_DAYS[n.weekday()]}ที่ {n.day} {TH_MONTHS[n.month - 1]} {n.year + 543} · {n:%H:%M} น."


st.markdown(clean_html(f"""
<div class="hero"><div class="pill"><span class="dot"></span>{thai_now()}</div>
<h1>ภาคเรียนนี้<br>ได้เกรดเท่าไหร่ <span>นะ?</span></h1>
<p>พิมพ์ชื่อตัวเองแล้วดูผลการเรียนได้เลย ไม่ต้องรอที่โรงเรียน</p>
<div class="sch">{SCHOOL_NAME} · ภาคเรียนที่ {SEMESTER}/{ACADEMIC_YEAR}</div></div>"""), unsafe_allow_html=True)

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
    else:
        st.markdown(clean_html("""
<div class="h2">ดูผลการเรียนง่ายๆ</div>
<div class="how">
<div class="it"><div class="ic">⌨️</div><b>พิมพ์ชื่อ</b><span>ชื่อหรือนามสกุล อย่างน้อย 2 ตัวอักษร</span></div>
<div class="it"><div class="ic">📋</div><b>ดูเกรดรายวิชา</b><span>พร้อมเกรดเฉลี่ยและอันดับในห้อง</span></div>
<div class="it"><div class="ic">⏳</div><b>บางวิชายังไม่ขึ้น?</b><span>ครูยังบันทึกไม่เสร็จ จะแสดงว่า รอผล</span></div>
</div>
<div class="note">⚠️ ผลการเรียนในหน้านี้เป็นข้อมูลอย่างไม่เป็นทางการ ไว้ให้ดูที่บ้านเท่านั้น ผลที่เป็นทางการให้ยึดตามเอกสารของโรงเรียน</div>"""), unsafe_allow_html=True)

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

st.markdown(clean_html(f"""
<div class="pgfoot">{SCHOOL_NAME} · {SCHOOL_DISTRICT}<br>ข้อมูลมาจากครูประจำวิชาโดยตรง และอัปเดตอัตโนมัติทุก 5 นาที</div>"""), unsafe_allow_html=True)
