import streamlit as st
import pandas as pd
import numpy as np
import urllib.parse

# --- ตั้งค่าหน้าเว็บสำหรับมือถือและคอมพิวเตอร์ ---
st.set_page_config(
    page_title="ระบบรายงานผลการเรียนออนไลน์ - โรงเรียนบ้านสันถนน", 
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
    info_map = [
        ('อังกฤษเพิ่ม', 1.0, 'เพิ่มเติม'),
        ('คณิตเพิ่ม', 1.0, 'เพิ่มเติม'),
        ('ภาษาไทย', 1.5, 'พื้นฐาน'),
        ('คณิตศาสตร์', 1.5, 'พื้นฐาน'),
        ('วิทยาศาสตร์', 1.5, 'พื้นฐาน'),
        ('วิทยาการ', 1.0, 'พื้นฐาน'),
        ('ประวัติ', 0.5, 'พื้นฐาน'),
        ('สังคม', 1.5, 'พื้นฐาน'),
        ('อังกฤษ', 1.5, 'พื้นฐาน'),
        ('สุขพละ', 1.0, 'พื้นฐาน'),
        ('สุข', 1.0, 'พื้นฐาน'),
        ('พละ', 1.0, 'พื้นฐาน'),
        ('ทัศนศิลป์', 1.0, 'พื้นฐาน'),
        ('ดนตรี', 1.0, 'พื้นฐาน'),
        ('การงาน', 1.0, 'พื้นฐาน'),
        ('ออกแบบ', 1.0, 'เพิ่มเติม'),
        ('ทักษะอาชีพ', 0.5, 'เพิ่มเติม'),
        ('ต้านทุจริต', 0.5, 'เพิ่มเติม'),
    ]
    for key, cr, stype in info_map:
        if key in subj_name:
            return cr, stype
    return 1.0, 'พื้นฐาน'

# --- Custom CSS และ Bootstrap 5 Styling (ปรับปรุงส่วนหัวให้สวยงาม กระชับ) ---
st.markdown(clean_html("""
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Sarabun:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&display=swap');
        
        * {
            font-family: 'TH Sarabun PSK', 'TH Sarabun New', 'Sarabun', Thonburi, sans-serif !important;
            font-size: 22px !important;
        }
        
        body {
            background-color: #f8fafc;
        }
        
        .main-header { 
            font-size: 36px !important; 
            color: #0d6efd; 
            font-weight: 700; 
            text-align: center; 
            margin-bottom: 20px; 
        }
        .sub-header { 
            color: #0d6efd; 
            border-bottom: 3px solid #0d6efd; 
            padding-bottom: 6px; 
            margin-bottom: 20px; 
            font-size: 28px !important; 
            font-weight: bold;
        }
        
        /* สไตล์หน้ากระดาษ ปพ.6 */
        .pp6-paper {
            background-color: #ffffff;
            color: #212529;
            padding: 35px 45px;
            border-radius: 16px;
            box-shadow: 0 0.5rem 1.5rem rgba(0, 0, 0, 0.12);
            margin: 0 auto 30px auto;
            max-width: 950px;
            border: 1px solid #dee2e6;
        }
        
        /* สไตล์ส่วนหัวที่ปรับปรุงใหม่ (ชิดสวยงาม ไม่ห่าง) */
        .pp6-header {
            text-align: center;
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 3px double #cbd5e1;
        }
        .pp6-header h3 { 
            font-size: 30px !important; 
            font-weight: bold; 
            color: #0f172a; 
            margin: 0 0 2px 0 !important; 
            line-height: 1.25 !important;
        }
        .pp6-header h4 { 
            font-size: 26px !important; 
            font-weight: bold; 
            color: #0d6efd; 
            margin: 2px 0 2px 0 !important; 
            line-height: 1.25 !important;
        }
        .pp6-header p { 
            font-size: 22px !important; 
            color: #475569; 
            margin: 1px 0 1px 0 !important; 
            line-height: 1.25 !important;
        }
        
        .pp6-info-box {
            background-color: #f0f7ff;
            border-left: 6px solid #0d6efd;
            border-radius: 10px;
            padding: 10px 20px;
            font-size: 24px !important;
            margin-bottom: 18px;
        }
        
        .pp6-table {
            font-size: 24px !important;
            margin-bottom: 18px;
        }
        
        .pp6-table th {
            background-color: #e2e8f0 !important;
            color: #0f172a !important;
            font-size: 25px !important;
            font-weight: bold !important;
            text-align: center;
            vertical-align: middle;
            padding: 5px 8px !important;
        }
        
        .pp6-table td {
            vertical-align: middle;
            color: #1e293b !important;
            padding: 5px 8px !important;
            font-size: 24px !important;
        }
        
        .pp6-summary-box {
            background-color: #ffffff;
            border: 2px solid #cbd5e1;
            border-radius: 12px;
            padding: 16px 20px;
            margin-top: 10px;
        }
        
        .pp6-summary-table {
            font-size: 24px !important;
            width: 100%;
            margin-bottom: 0;
        }
        
        .pp6-summary-table td {
            padding: 5px 10px !important;
            border-bottom: 1px solid #e2e8f0;
            font-size: 24px !important;
        }
        
        /* สไตล์ตาราง Dashboard */
        .dash-table-container { width: 100%; overflow-x: auto; margin-top: 10px; margin-bottom: 20px; }
        .dash-table { width: 100%; border-collapse: collapse; font-size: 22px !important; }
        .dash-table th { border: 1px solid #cbd5e1; background-color: #f1f5f9; padding: 6px 4px; text-align: center; font-weight: 600; font-size: 23px !important; }
        .dash-table th.rotate-header { height: 120px; white-space: nowrap; }
        .dash-table th.rotate-header > div { writing-mode: vertical-rl; transform: rotate(180deg); margin: 0 auto; }
        .dash-table td { border: 1px solid #cbd5e1; padding: 5px 6px; text-align: center; font-size: 22px !important; }
        .dash-table td.missing-cell { background-color: #fef08a !important; color: #854d0e; font-weight: bold; font-size: 20px !important; }
        .dash-table td.name-cell { text-align: left; white-space: nowrap; font-weight: 600; padding-left: 10px; }
        
        .stTextInput input { font-size: 22px !important; padding: 8px 12px !important; }
        .stSelectbox div { font-size: 22px !important; }
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

# --- สร้างหน้ากระดาษ ปพ.6 สไตล์กระชับ สวยงาม ---
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
            grade_str = '<span class="badge bg-warning text-dark px-2 py-1" style="font-size: 18px !important;">ยังไม่ส่ง</span>'
        else:
            g_num = f"{val:.1f}".rstrip('0').rstrip('.') if isinstance(val, float) and val % 1 != 0 else str(int(val)) if isinstance(val, float) else str(val)
            grade_str = f'<span class="fw-bold" style="font-size: 24px !important;">{g_num}</span>'
            
        tbody_html += f"""
        <tr>
            <td class="text-center">{i}</td>
            <td class="text-start ps-3">{col}</td>
            <td class="text-center">{subj_type}</td>
            <td class="text-center">{credit:.1f}</td>
            <td class="text-center">{grade_str}</td>
        </tr>"""
        
    total_cr = total_basic_cr + total_add_cr

    raw_html = f"""
<div class="pp6-paper shadow-lg border rounded-4 p-4 my-3 bg-white">
    <div class="pp6-header">
        <h3>แบบรายงานผลพัฒนาคุณภาพผู้เรียนรายบุคคล</h3>
        <p>ปีการศึกษา {ACADEMIC_YEAR} ภาคเรียนที่ {SEMESTER}</p>
        <h4>{SCHOOL_NAME}</h4>
        <p>{SCHOOL_DISTRICT}</p>
    </div>
    
    <div class="pp6-info-box alert alert-primary border-0 border-start border-5 border-primary rounded-3 p-2 px-3 mb-3">
        <div class="row text-dark">
            <div class="col-md-3"><b>เลขที่:</b> {student_no}</div>
            <div class="col-md-6"><b>ชื่อ - นามสกุล:</b> {student_name}</div>
            <div class="col-md-3"><b>ชั้น:</b> {sheet_name}</div>
        </div>
    </div>
    
    <div class="table-responsive mb-3">
        <table class="table table-bordered table-striped table-hover align-middle pp6-table">
            <thead class="table-light">
                <tr>
                    <th width="8%" class="text-center">ลำดับ</th>
                    <th width="42%" class="text-center">ชื่อวิชา</th>
                    <th width="20%" class="text-center">ประเภท</th>
                    <th width="15%" class="text-center">จำนวนหน่วยกิต</th>
                    <th width="15%" class="text-center">ระดับผลการเรียน</th>
                </tr>
            </thead>
            <tbody>
                {tbody_html}
            </tbody>
        </table>
    </div>
    
    <div class="pp6-summary-box card border border-secondary-subtle rounded-3 p-3">
        <h5 class="card-title fw-bold text-dark mb-2" style="font-size: 24px !important;">📌 สรุปผลการประเมิน</h5>
        <div class="table-responsive">
            <table class="table table-borderless align-middle pp6-summary-table mb-0">
                <tbody>
                    <tr>
                        <td width="65%" class="text-secondary">จำนวนหน่วยกิต/น้ำหนักวิชาพื้นฐาน</td>
                        <td width="35%" class="fw-bold text-dark">{total_basic_cr:.2f}</td>
                    </tr>
                    <tr>
                        <td class="text-secondary">จำนวนหน่วยกิต/น้ำหนักวิชาเพิ่มเติม</td>
                        <td class="fw-bold text-dark">{total_add_cr:.2f}</td>
                    </tr>
                    <tr class="table-light">
                        <td class="fw-bold text-dark">รวมจำนวนหน่วยกิต/น้ำหนัก</td>
                        <td class="fw-bold text-dark">{total_cr:.2f}</td>
                    </tr>
                    <tr class="table-primary">
                        <td class="fw-bold text-primary">ระดับผลการเรียนเฉลี่ย (GPA)</td>
                        <td><span class="badge bg-primary text-white px-3 py-1" style="font-size: 24px !important;">{gpa}</span></td>
                    </tr>
                    <tr class="table-light">
                        <td class="fw-bold text-dark">อันดับที่ในห้องเรียน</td>
                        <td class="fw-bold text-dark">{rank} <span class="text-muted fw-normal" style="font-size: 22px !important;">(จากนักเรียนจำนวน {total_students} คน)</span></td>
                    </tr>
                </tbody>
            </table>
        </div>
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
            html += f'<th style="height: auto; padding: 6px 6px;">{col}</th>'
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
                        st.markdown("<br>", unsafe_allow_html=True)
                        
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
