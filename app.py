import streamlit as st
import pandas as pd
import urllib.parse
from streamlit_gsheets import GSheetsConnection

# --- ตั้งค่าหน้าเว็บสำหรับมือถือและคอมพิวเตอร์ ---
st.set_page_config(
    page_title="ระบบเช็คผลการเรียนออนไลน์", 
    page_icon="🎓", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ลิงก์ Google Sheet ---
GSHEET_URL = "https://docs.google.com/spreadsheets/d/1FXRBsGcqjpDjKjzmArhz8SAnKd2sE-gl_zT9NhfzOPM/edit?usp=sharing"
SHEET_ID = "1FXRBsGcqjpDjKjzmArhz8SAnKd2sE-gl_zT9NhfzOPM"
SHEET_NAMES = ["ม.1", "ม.2", "ม.3"]

# --- Custom CSS แต่งสไตล์เว็บ ---
st.markdown("""
    <style>
        .stMetric {
            background-color: #f8fafc;
            padding: 15px;
            border-radius: 12px;
            box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.05);
            border-left: 5px solid #3b82f6;
        }
        .main-header {
            font-size: 2rem;
            color: #1e3a8a;
            font-weight: 700;
            text-align: center;
            margin-bottom: 20px;
        }
        .sub-header {
            color: #2563eb;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 8px;
            margin-bottom: 15px;
        }
        
        /* สไตล์ตารางนักเรียนรองรับการดูบนมือถือและคอม */
        .student-table-container {
            width: 100%;
            overflow-x: auto;
            margin-top: 10px;
            margin-bottom: 20px;
        }
        .student-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
            font-family: sans-serif;
        }
        .student-table th {
            border: 1px solid #cbd5e1;
            background-color: #f1f5f9;
            color: #0f172a;
            padding: 6px 2px;
            vertical-align: bottom;
            text-align: center;
            font-weight: 600;
        }
        .student-table th.rotate-header {
            height: 110px;
            white-space: nowrap;
        }
        .student-table th.rotate-header > div {
            writing-mode: vertical-rl;
            transform: rotate(180deg);
            margin: 0 auto;
            max-height: 100px;
            line-height: 1.1;
            font-size: 11px;
        }
        .student-table td {
            border: 1px solid #cbd5e1;
            padding: 8px 4px;
            text-align: center;
            color: #1e293b;
        }
        /* ช่องสีเหลืองสำหรับงานที่ยังไม่ได้ส่ง */
        .student-table td.missing-cell {
            background-color: #fef08a !important;
            color: #854d0e;
            font-weight: bold;
            font-size: 11px;
        }
        .student-table td.name-cell {
            text-align: left;
            white-space: nowrap;
            font-weight: 600;
            padding-left: 8px;
            padding-right: 8px;
        }
    </style>
""", unsafe_allow_html=True)

# --- ฟังก์ชันอ่านข้อมูลจาก Google Sheet ---
def load_sheet_data(sheet_name):
    try:
        # อ่านไฟล์ CSV จาก Google Sheets gviz API
        encoded_sheet = urllib.parse.quote(sheet_name)
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={encoded_sheet}"
        df = pd.read_csv(url)
        
        # ปรับความสะอาดข้อมูล
        df = df.dropna(how='all')
        if 'ชื่อ - นามสกุล' in df.columns:
            df = df.dropna(subset=['ชื่อ - นามสกุล'])
            
        # กรองคอลัมน์ Unnamed ออก
        cols = [c for c in df.columns if not str(c).startswith('Unnamed') and not 'merged' in str(c)]
        return df[cols]
    except Exception as e:
        st.error(f"ไม่สามารถโหลดข้อมูลแผ่นงาน {sheet_name} ได้: {e}")
        return pd.DataFrame()

def load_all_data():
    all_data = {}
    for sheet in SHEET_NAMES:
        df = load_sheet_data(sheet)
        if not df.empty:
            all_data[sheet] = df
    return all_data

# --- สร้างตาราง HTML สไตล์พิเศษสำหรับนักเรียน ---
def render_student_table_html(df):
    html = '<div class="student-table-container"><table class="student-table"><thead><tr>'
    normal_cols = ['เลขที่', 'ชื่อ - นามสกุล', 'ผลการเรียน', 'เฉลี่ย', 'เกรด']
    
    for col in df.columns:
        if any(nc in str(col) for nc in normal_cols):
            html += f'<th style="height: auto; padding: 8px;">{col}</th>'
        else:
            html += f'<th class="rotate-header"><div>{col}</div></th>'
            
    html += '</tr></thead><tbody>'
    non_score_cols = ['เลขที่', 'ชื่อ - นามสกุล']
    
    for _, row in df.iterrows():
        html += '<tr>'
        for col in df.columns:
            val = row[col]
            is_missing = pd.isna(val) or val is None or str(val).strip() == '' or str(val).strip().lower() == 'nan'
            
            if col in non_score_cols:
                if col == 'ชื่อ - นามสกุล':
                    html += f'<td class="name-cell">{val if not is_missing else ""}</td>'
                else:
                    html += f'<td>{int(val) if not is_missing and isinstance(val, float) and val.is_integer() else val}</td>'
            else:
                if is_missing:
                    html += '<td class="missing-cell">ยังไม่ส่ง</td>'
                else:
                    if isinstance(val, float):
                        formatted_val = f"{val:.2f}".rstrip('0').rstrip('.') if val % 1 != 0 else f"{int(val)}"
                    else:
                        formatted_val = str(val)
                    html += f'<td>{formatted_val}</td>'
        html += '</tr>'
        
    html += '</tbody></table></div>'
    return html

# ==========================================
# เริ่มต้นหน้าตา UI
# ==========================================
st.markdown('<div class="main-header">🎓 ระบบผลการเรียนออนไลน์</div>', unsafe_allow_html=True)

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135810.png", width=80)
    st.markdown("## 📍 เมนูหลัก")
    menu = st.radio("เลือกหน้าต่างการทำงาน:", [
        "🔍 สำหรับนักเรียน (ค้นหาคะแนน)", 
        "📊 แดชบอร์ดภาพรวม", 
        "📝 สำหรับครู (จัดการคะแนน)"
    ])
    st.markdown("---")
    st.caption("📱 รองรับการใช้งานผ่านมือถือและคอมพิวเตอร์")

all_data = load_all_data()

# ==========================================
# 1. หน้า สำหรับนักเรียน
# ==========================================
if menu == "🔍 สำหรับนักเรียน (ค้นหาคะแนน)":
    st.markdown('<h2 class="sub-header">🔍 ค้นหาผลการเรียน</h2>', unsafe_allow_html=True)
    
    search_name = st.text_input("พิมพ์ชื่อ หรือนามสกุล ของนักเรียน (เช่น พชร)", placeholder="กรอกชื่อเพื่อค้นหา...")
    
    if search_name:
        found = False
        st.markdown(f"#### 📑 ผลการค้นหาสำหรับ: **{search_name}**")
        
        for sheet_name, df in all_data.items():
            if 'ชื่อ - นามสกุล' in df.columns:
                student_data = df[df['ชื่อ - นามสกุล'].astype(str).str.contains(search_name, na=False)]
                if not student_data.empty:
                    found = True
                    with st.expander(f"📖 ระดับชั้น: {sheet_name}", expanded=True):
                        st.markdown(render_student_table_html(student_data), unsafe_allow_html=True)
                        
        if not found:
            st.warning("⚠️ ไม่พบรายชื่อนี้ในระบบ กรุณาตรวจสอบการสะกดคำอีกครั้ง")

# ==========================================
# 2. หน้า แดชบอร์ดภาพรวม
# ==========================================
elif menu == "📊 แดชบอร์ดภาพรวม":
    st.markdown('<h2 class="sub-header">📊 สรุปภาพรวมรายชั้นเรียน</h2>', unsafe_allow_html=True)
    
    total_students = sum(len(df) for df in all_data.values())
    
    col1, col2 = st.columns(2)
    col1.metric("📚 จำนวนระดับชั้น", f"{len(all_data)} ระดับชั้น")
    col2.metric("🧑‍🎓 จำนวนนักเรียนรวม", f"{total_students} คน")
    
    st.markdown("<br>", unsafe_allow_html=True)
    selected_dash_sheet = st.selectbox("เลือกชั้นเรียนที่ต้องการดูรายละเอียด:", SHEET_NAMES)
    
    if selected_dash_sheet in all_data:
        df = all_data[selected_dash_sheet]
        st.markdown(f"### 📋 รายชื่อและคะแนนทั้งหมด ({selected_dash_sheet})")
        st.markdown(render_student_table_html(df), unsafe_allow_html=True)

# ==========================================
# 3. หน้า สำหรับครู
# ==========================================
elif menu == "📝 สำหรับครู (จัดการคะแนน)":
    st.markdown('<h2 class="sub-header">📝 ระบบจัดการคะแนน</h2>', unsafe_allow_html=True)
    
    password = st.text_input("🔑 รหัสผ่านสำหรับคุณครู", type="password")
    
    if password == "1234":
        st.success("🔓 ยืนยันตัวตนสำเร็จ")
        st.info("💡 คุณครูสามารถเข้าไปแก้ไขคะแนนโดยตรงได้ที่ Google Sheets ลิงก์ด้านล่าง ระบบจะอัปเดตข้อมูลบนเว็บโดยอัตโนมัติทันที:")
        st.markdown(f"👉 **[คลิกที่นี่เพื่อเปิด Google Sheet แก้ไขคะแนน]({GSHEET_URL})**")
        
        selected_sheet = st.selectbox("📌 เลือกดูตารางคะแนนล่าสุด", SHEET_NAMES)
        if selected_sheet in all_data:
            st.dataframe(all_data[selected_sheet], use_container_width=True, hide_index=True)
            
    elif password != "":
        st.error("❌ รหัสผ่านไม่ถูกต้อง!")