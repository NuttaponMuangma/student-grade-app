import streamlit as st
import pandas as pd
import numpy as np
import urllib.parse

# --- ตั้งค่าหน้าเว็บสำหรับมือถือและคอมพิวเตอร์ ---
st.set_page_config(
    page_title="ระบบรายงานผลการเรียนออนไลน์", 
    page_icon="🎓", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ข้อมูลโรงเรียนสำหรับแบบฟอร์ม ปพ.6 ---
SCHOOL_NAME = "โรงเรียนบ้านสันถนน"
SCHOOL_DISTRICT = "สำนักงานเขตพื้นที่การศึกษาประถมศึกษาเชียงราย เขต 3 จังหวัดเชียงราย"
ACADEMIC_YEAR = "2569"
SEMESTER = "1"

# --- ลิงก์ Google Sheet ---
GSHEET_URL = "https://docs.google.com/spreadsheets/d/1FXRBsGcqjpDjKjzmArhz8SAnKd2sE-gl_zT9NhfzOPM/edit?usp=sharing"
SHEET_ID = "1FXRBsGcqjpDjKjzmArhz8SAnKd2sE-gl_zT9NhfzOPM"
SHEET_NAMES = ["ม.1", "ม.2", "ม.3"]

# ฟังก์ชันลบช่องว่างส่วนเกินเพื่อป้องกันไม่ให้ Streamlit แปลง HTML เป็น Code Block
def clean_html(html_str):
    return "".join([line.strip() for line in html_str.split('\n')])

# --- ฟังก์ชันกำหนดประเภทและหน่วยกิตของแต่ละวิชา ---
def get_subject_info(subj_name):
    info = {
        'ภาษาไทย': (1.5, 'พื้นฐาน'),
        'คณิตศาสตร์': (1.5, 'พื้นฐาน'),
        'วิทยาศาสตร์': (1.5, 'พื้นฐาน'),
        'วิทยาการ': (1.0, 'พื้นฐาน'),
        'สังคม': (1.5, 'พื้นฐาน'),
        'ประวัติ': (0.5, 'พื้นฐาน'),
        'อังกฤษ': (1.5, 'พื้นฐาน'),
        'สุข': (1.0, 'พื้นฐาน'),
        'พละ': (1.0, 'พื้นฐาน'),
        'ทัศนศิลป์': (1.0, 'พื้นฐาน'),
        'ดนตรี': (1.0, 'พื้นฐาน'),
        'การงาน': (1.0, 'พื้นฐาน'),
        'ออกแบบ': (1.0, 'เพิ่มเติม'),
        'คณิตเพิ่ม': (1.0, 'เพิ่มเติม'),
        'อังกฤษเพิ่ม': (1.0, 'เพิ่มเติม'),
        'ทักษะอาชีพ': (0.5, 'เพิ่มเติม'),
        'ต้านทุจริต': (0.5, 'เพิ่มเติม')
    }
    for key, val in info.items():
        if key in subj_name:
            return val
    return (1.0, 'พื้นฐาน')

# --- Custom CSS แต่งสไตล์เว็บ และกำหนดฟอนต์ TH Sarabun PSK ---
st.markdown(clean_html("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Sarabun:ital,wght@0,300;0,400;0,600;0,700;1,400&display=swap');
        
        html, body, [class*="css"], div, p, span, h1, h2, h3, h4, h5, h6, table, td, th, input, button, select {
            font-family: 'TH Sarabun PSK', 'TH Sarabun New', 'Sarabun', Thonburi, sans-serif !important;
        }
        
        .main-header { font-size: 2.6rem; color: #1e3a8a; font-weight: 700; text-align: center; margin-bottom: 20px; }
        .sub-header { color: #2563eb; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px; margin-bottom: 15px; font-size: 2rem; }
        
        /* สไตล์หน้ากระดาษ ปพ.6 */
        .pp6-paper {
            background-color: #ffffff;
            color: #000000;
            padding: 40px 50px;
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.12);
            margin: 0 auto 30px auto;
            max-width: 850px;
            border: 1px solid #cbd5e1;
        }
        .pp6-header { text-align: center; margin-bottom: 25px; }
        .pp6-header h3 { margin: 5px 0; color: #000000; font-weight: bold; font-size: 26px; }
        .pp6-header h4 { margin: 5px 0; color: #000000; font-weight: bold; font-size: 22px; }
        .pp6-header p { margin: 3px 0; font-size: 18px; color: #222222; }
        
        .pp6-info { 
            margin-bottom: 20px; 
            font-size: 19px; 
            color: #000000; 
            background-color: #f8fafc;
            padding: 12px 18px;
            border-radius: 6px;
            border-left: 5px solid #2563eb;
        }
        
        .pp6-table { width: 100%; border-collapse: collapse; margin-bottom: 25px; font-size: 18px; }
        .pp6-table th, .pp6-table td { border: 1px solid #000000 !important; padding: 6px 10px !important; color: #000000 !important; }
        .pp6-table th { background-color: #f1f5f9 !important; text-align: center; font-weight: bold; }
        
        .pp6-summary { margin-top: 15px; }
        .pp6-summary table { width: 100%; border-collapse: collapse; font-size: 18px; }
        .pp6-summary td { border: 1px solid #000000 !important; padding: 6px 12px !important; color: #000000 !important; }
        .pp6-summary td.bg-light { background-color: #f8fafc !important; font-weight: bold; }
        
        /* สไตล์ตาราง Dashboard */
        .dash-table-container { width: 100%; overflow-x: auto; margin-top: 10px; margin-bottom: 20px; }
        .dash-table { width: 100%; border-collapse: collapse; font-size: 16px; }
        .dash-table th { border: 1px solid #cbd5e1; background-color: #f1f5f9; padding: 6px 2px; text-align: center; font-weight: 600; }
        .dash-table th.rotate-header { height: 110px; white-space: nowrap; }
        .dash-table th.rotate-header > div { writing-mode: vertical-rl; transform: rotate(180deg); margin: 0 auto; }
        .dash-table td { border: 1px solid #cbd5e1; padding: 8px 4px; text-align: center; }
        .dash-table td.missing-cell { background-color: #fef08a !important; color: #854d0e; font-weight: bold; font-size: 15px; }
        .dash-table td.name-cell { text-align: left; white-space: nowrap; font-weight: 600; padding-left: 8px; }
    </style>
"""), unsafe_allow_html=True)

# --- ฟังก์ชันอ่านและคำนวณข้อมูล ---
def load_sheet_data(sheet_name):
    try:
        encoded_sheet = urllib.parse.quote(sheet_name)
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={encoded_sheet}"
        
        df_raw = pd.read_csv(url, header=None)
        
        header_idx = None
        for idx, row in df_raw.iterrows():
            if row.astype(str).str.contains('ชื่อ - นามสกุล|ชื่อ-นามสกุล|ชื่อนามสกุล').any():
                header_idx = idx
                break
                
        if header_idx is not None:
            df = pd.read_csv(url, header=header_idx)
            df.columns = [str(c).strip() for c in df.columns]
            
            name_col = next((c for c in df.columns if 'ชื่อ' in c and 'นามสกุล' in c), None)
            
            if name_col:
                df = df[df[name_col].astype(str).str.strip() != name_col]
                df = df.dropna(subset=[name_col])
                df = df[df[name_col].astype(str).str.strip() != '']
                
                if name_col != 'ชื่อ - นามสกุล':
                    df = df.rename(columns={name_col: 'ชื่อ - นามสกุล'})
                    
                cols = [c for c in df.columns if not str(c).startswith('Unnamed') and 'merged' not in str(c).lower()]
                df = df[cols]
                
                non_subj_keywords = ['เลขที่', 'ชื่อ - นามสกุล', 'เกรดเฉลี่ย', 'ลำดับที่', 'รวม', 'เฉลี่ย', 'ผลการเรียน']
                subject_cols = [c for c in df.columns if c not in ['เลขที่', 'ชื่อ - นามสกุล'] and not any(kw == c for kw in non_subj_keywords)]
                
                def calc_gpa(row):
                    total_points = 0
                    total_credits = 0
                    for col in subject_cols:
                        val = row[col]
                        credit, _ = get_subject_info(col)
                        try:
                            v_float = float(val)
                            if not np.isnan(v_float):
                                total_points += v_float * credit
                                total_credits += credit
                        except (ValueError, TypeError):
                            pass
                    return round(total_points / total_credits, 2) if total_credits > 0 else np.nan

                df['เกรดเฉลี่ย'] = df.apply(calc_gpa, axis=1)
                df['ลำดับที่'] = df['เกรดเฉลี่ย'].rank(ascending=False, method='min').astype('Int64')
                
                return df, subject_cols
                
        return pd.DataFrame(), []
    except Exception as e:
        st.error(f"ไม่สามารถโหลดข้อมูลแผ่นงาน {sheet_name} ได้: {e}")
        return pd.DataFrame(), []

def load_all_data():
    all_data, all_subject_cols = {}, {}
    for sheet in SHEET_NAMES:
        df, subjs = load_sheet_data(sheet)
        if not df.empty:
            all_data[sheet] = df
            all_subject_cols[sheet] = subjs
    return all_data, all_subject_cols

# --- สร้างหน้ากระดาษ ปพ.6 ---
def render_porpor6(row, sheet_name, subject_cols, total_students):
    student_no = int(row['เลขที่']) if pd.notna(row['เลขที่']) else "-"
    student_name = row['ชื่อ - นามสกุล']
    rank = row['ลำดับที่']
    gpa = f"{row['เกรดเฉลี่ย']:.2f}" if pd.notna(row['เกรดเฉลี่ย']) else "-"
    
    total_basic_cr = 0.0
    total_add_cr = 0.0
    
    tbody_html = ""
    for i, col in enumerate(subject_cols, 1):
        credit, subj_type = get_subject_info(col)
        
        if subj_type == 'พื้นฐาน':
            total_basic_cr += credit
        else:
            total_add_cr += credit
            
        val = row[col]
        is_missing = pd.isna(val) or val is None or str(val).strip() == '' or str(val).strip().lower() in ['nan', 'none']
        if is_missing:
            grade_str = 'ยังไม่ส่ง'
        else:
            grade_str = f"{val:.1f}".rstrip('0').rstrip('.') if isinstance(val, float) and val % 1 != 0 else str(int(val)) if isinstance(val, float) else str(val)
            
        tbody_html += f"""
        <tr>
            <td style="text-align: center;">{i}</td>
            <td style="text-align: left;">{col}</td>
            <td style="text-align: center;">{subj_type}</td>
            <td style="text-align: center;">{credit:.1f}</td>
            <td style="text-align: center;">{grade_str}</td>
        </tr>"""
        
    total_cr = total_basic_cr + total_add_cr

    raw_html = f"""
<div class="pp6-paper">
    <div class="pp6-header">
        <h3>แบบรายงานผลพัฒนาคุณภาพผู้เรียนรายบุคคล</h3>
        <p>ปีการศึกษา {ACADEMIC_YEAR} ภาคเรียนที่ {SEMESTER}</p>
        <h4>{SCHOOL_NAME}</h4>
        <p>{SCHOOL_DISTRICT}</p>
    </div>
    
    <div class="pp6-info">
        <b>เลขที่:</b> {student_no} &nbsp;&nbsp;&nbsp;&nbsp; <b>ชื่อ - นามสกุล:</b> {student_name} &nbsp;&nbsp;&nbsp;&nbsp; <b>ชั้น:</b> {sheet_name}
    </div>
    
    <table class="pp6-table">
        <thead>
            <tr>
                <th width="8%">ลำดับ</th>
                <th width="42%">ชื่อวิชา</th>
                <th width="20%">ประเภท</th>
                <th width="15%">จำนวน<br>หน่วยกิต</th>
                <th width="15%">ระดับ<br>ผลการเรียน</th>
            </tr>
        </thead>
        <tbody>
            {tbody_html}
        </tbody>
    </table>
    
    <div class="pp6-summary">
        <b style="font-size: 19px;">สรุปผลการประเมิน</b>
        <table style="margin-top: 8px;">
            <tr>
                <td width="65%">จำนวนหน่วยกิต/น้ำหนักวิชาพื้นฐาน</td>
                <td width="35%"><b>{total_basic_cr:.2f}</b></td>
            </tr>
            <tr>
                <td>จำนวนหน่วยกิต/น้ำหนักวิชาเพิ่มเติม</td>
                <td><b>{total_add_cr:.2f}</b></td>
            </tr>
            <tr>
                <td class="bg-light">รวมจำนวนหน่วยกิต/น้ำหนัก</td>
                <td class="bg-light"><b>{total_cr:.2f}</b></td>
            </tr>
            <tr>
                <td class="bg-light">ระดับผลการเรียนเฉลี่ย (GPA)</td>
                <td class="bg-light"><b style="color: #1e3a8a; font-size: 20px;">{gpa}</b></td>
            </tr>
            <tr>
                <td class="bg-light">อันดับที่ในห้องเรียน</td>
                <td class="bg-light"><b>{rank}</b> (จากนักเรียนจำนวน {total_students} คน)</td>
            </tr>
        </table>
    </div>
</div>
"""
    return clean_html(raw_html)

# --- สร้างตาราง Dashboard ---
def render_dashboard_table(df, subject_cols):
    html = '<div class="dash-table-container"><table class="dash-table"><thead><tr>'
    normal_cols = ['เลขที่', 'ชื่อ - นามสกุล', 'เกรดเฉลี่ย', 'ลำดับที่']
    display_cols = [c for c in df.columns if c in normal_cols or c in subject_cols]
    
    for col in display_cols:
        if any(nc in str(col) for nc in normal_cols):
            html += f'<th style="height: auto; padding: 8px;">{col}</th>'
        else:
            html += f'<th class="rotate-header"><div>{col}</div></th>'
            
    html += '</tr></thead><tbody>'
    for _, row in df.iterrows():
        html += '<tr>'
        for col in display_cols:
            val = row[col]
            is_missing = pd.isna(val) or val is None or str(val).strip() == '' or str(val).strip().lower() in ['nan', 'none']
            if col in ['เลขที่', 'ชื่อ - นามสกุล', 'ลำดับที่']:
                if col == 'ชื่อ - นามสกุล':
                    html += f'<td class="name-cell">{val if not is_missing else ""}</td>'
                else:
                    html += f'<td>{int(val) if not is_missing and isinstance(val, float) and val.is_integer() else (val if not is_missing else "-")}</td>'
            else:
                if is_missing:
                    html += '<td class="missing-cell">ยังไม่ส่ง</td>'
                else:
                    html += f'<td>{f"{val:.2f}".rstrip("0").rstrip(".") if isinstance(val, float) and val % 1 != 0 else (int(val) if isinstance(val, float) else val)}</td>'
        html += '</tr>'
    html += '</tbody></table></div>'
    return clean_html(html)

# ==========================================
# เริ่มต้นหน้าตา UI
# ==========================================
st.markdown(clean_html('<div class="main-header">🎓 ระบบรายงานผลการเรียนออนไลน์</div>'), unsafe_allow_html=True)

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135810.png", width=80)
    st.markdown("## 📍 เมนูหลัก")
    menu = st.radio("เลือกหน้าต่างการทำงาน:", [
        "🔍 สำหรับนักเรียน (ค้นหาคะแนน)", 
        "📊 แดชบอร์ดสรุปภาพรวม", 
        "📝 สำหรับครู (จัดการคะแนน)"
    ])

all_data, all_subject_cols = load_all_data()

# ==========================================
# 1. หน้า สำหรับนักเรียน (รูปแบบ ปพ.6)
# ==========================================
if menu == "🔍 สำหรับนักเรียน (ค้นหาคะแนน)":
    st.markdown(clean_html('<h2 class="sub-header">🔍 ค้นหาผลการเรียน</h2>'), unsafe_allow_html=True)
    
    search_name = st.text_input("พิมพ์ชื่อ หรือนามสกุล ของนักเรียน (เช่น สมชาย)", placeholder="กรอกชื่อเพื่อค้นหา...").strip()
    
    if search_name:
        found = False
        for sheet_name, df in all_data.items():
            if 'ชื่อ - นามสกุล' in df.columns:
                student_data = df[df['ชื่อ - นามสกุล'].astype(str).str.contains(search_name, na=False, case=False)]
                if not student_data.empty:
                    found = True
                    subj_cols = all_subject_cols.get(sheet_name, [])
                    total_students = len(df)
                    
                    for _, student in student_data.iterrows():
                        st.markdown(render_porpor6(student, sheet_name, subj_cols, total_students), unsafe_allow_html=True)
                        st.markdown("<br><hr><br>", unsafe_allow_html=True)
                        
        if not found:
            st.warning("⚠️ ไม่พบรายชื่อนี้ในระบบ กรุณาตรวจสอบการสะกดคำอีกครั้ง")

# ==========================================
# 2. หน้า แดชบอร์ดภาพรวม
# ==========================================
elif menu == "📊 แดชบอร์ดสรุปภาพรวม":
    st.markdown(clean_html('<h2 class="sub-header">📊 แดชบอร์ดสรุปผลการเรียน</h2>'), unsafe_allow_html=True)
    
    st.markdown("### 🏆 นักเรียนที่ได้เกรดเฉลี่ยสูงสุด 5 อันดับแรก")
    tabs = st.tabs([f"ระดับชั้น {sheet}" for sheet in SHEET_NAMES])
    for i, sheet in enumerate(SHEET_NAMES):
        with tabs[i]:
            if sheet in all_data:
                df = all_data[sheet]
                top5_df = df.sort_values('เกรดเฉลี่ย', ascending=False).head(5)
                display_top5 = top5_df[['ลำดับที่', 'เลขที่', 'ชื่อ - นามสกุล', 'เกรดเฉลี่ย']].copy()
                display_top5.columns = ['อันดับในห้อง', 'เลขที่', 'ชื่อ - นามสกุล', 'เกรดเฉลี่ย (GPA)']
                st.dataframe(display_top5, use_container_width=True, hide_index=True)
                
    st.markdown("---")
    st.markdown("### 📋 ข้อมูลเกรดเฉลี่ยทั้งระดับชั้น")
    selected_dash_sheet = st.selectbox("เลือกชั้นเรียนที่ต้องการดูรายละเอียด:", SHEET_NAMES)
    if selected_dash_sheet in all_data:
        df = all_data[selected_dash_sheet]
        subj_cols = all_subject_cols.get(selected_dash_sheet, [])
        st.markdown(render_dashboard_table(df, subj_cols), unsafe_allow_html=True)

# ==========================================
# 3. หน้า สำหรับครู
# ==========================================
elif menu == "📝 สำหรับครู (จัดการคะแนน)":
    st.markdown(clean_html('<h2 class="sub-header">📝 ระบบจัดการคะแนน</h2>'), unsafe_allow_html=True)
    password = st.text_input("🔑 รหัสผ่านสำหรับคุณครู", type="password")
    
    if password == "1234":
        st.success("🔓 ยืนยันตัวตนสำเร็จ")
        st.markdown(f"👉 **[คลิกที่นี่เพื่อเปิด Google Sheet แก้ไขคะแนน]({GSHEET_URL})**")
        selected_sheet = st.selectbox("📌 เลือกดูตารางคะแนนล่าสุด", SHEET_NAMES)
        if selected_sheet in all_data:
            st.dataframe(all_data[selected_sheet], use_container_width=True, hide_index=True)
    elif password != "":
        st.error("❌ รหัสผ่านไม่ถูกต้อง!")
