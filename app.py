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

# --- Custom CSS และ Bootstrap 5 Styling ---
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

# --- ฟังก์ชันสร้างตาราง Top 5 สวยงาม ---
def render_top5_table(top5_df):
    tbody = ""
    medals = {1: "🥇 1", 2: "🥈 2", 3: "🥉 3", 4: "4", 5: "5"}
    
    for _, row in top5_df.iterrows():
        rank_val = int(row['ลำดับที่']) if pd.notna(row['ลำดับที่']) else "-"
        medal_str = medals.get(rank_val, str(rank_val))
        student_name = row['ชื่อ - นามสกุล']
        student_no = int(row['เลขที่']) if pd.notna(row['เลขที่']) else "-"
        gpa = f"{row['เกรดเฉลี่ย']:.2f}" if pd.notna(row['เกรดเฉลี่ย']) else "-"
        
        tbody += f"""
        <tr>
            <td class="text-center fw-bold">{medal_str}</td>
            <td class="text-center">{student_no}</td>
            <td class="text-start ps-3 fw-bold text-dark">{student_name}</td>
            <td class="text-center"><span class="badge bg-primary text-white px-3 py-1 fs-6">{gpa}</span></td>
        </tr>
        """
        
    html = f"""
    <div class="table-responsive my-2">
        <table class="table table-bordered table-hover align-middle shadow-sm rounded-3 overflow-hidden">
            <thead class="table-primary text-center">
                <tr>
                    <th width="15%">อันดับที่</th>
                    <th width="15%">เลขที่</th>
                    <th width="50%">ชื่อ - นามสกุล</th>
                    <th width="20%">เกรดเฉลี่ย (GPA)</th>
                </tr>
            </thead>
            <tbody>
                {tbody}
            </tbody>
        </table>
    </div>
    """
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
# 2. หน้า แดชบอร์ดภาพรวม (ปรับโฉมใหม่)
# ==========================================
elif menu == "📊 แดชบอร์ดสรุปภาพรวม":
    st.markdown(clean_html('<h2 class="sub-header">📊 แดชบอร์ดสรุปภาพรวมการกรอกคะแนน</h2>'), unsafe_allow_html=True)
    
    # --- คำนวณสถานะความคืบหน้าการกรอกข้อมูล ---
    total_expected_cells = 0
    total_filled_cells = 0
    class_progress = {}
    
    for sheet, df in all_data.items():
        subjs = all_subject_cols.get(sheet, [])
        if not df.empty and subjs:
            n_students = len(df)
            n_subjs = len(subjs)
            total_cells = n_students * n_subjs
            
            filled = 0
            for col in subjs:
                filled += df[col].apply(lambda val: 0 if (pd.isna(val) or str(val).strip() == '' or str(val).strip().lower() in ['nan', 'none']) else 1).sum()
                
            remaining = total_cells - filled
            pct = round((filled / total_cells) * 100, 1) if total_cells > 0 else 0
            
            class_progress[sheet] = {
                'total': total_cells,
                'filled': filled,
                'remaining': remaining,
                'pct': pct,
                'students': n_students,
                'subjects': n_subjs
            }
            total_expected_cells += total_cells
            total_filled_cells += filled
            
    total_remaining_cells = total_expected_cells - total_filled_cells
    overall_pct = round((total_filled_cells / total_expected_cells) * 100, 1) if total_expected_cells > 0 else 0
    
    # --- 1. สรุปความคืบหน้าการกรอกข้อมูล (Metrics & Progress) ---
    st.markdown("### 📈 ความคืบหน้าการบันทึกข้อมูลคะแนน")
    
    m1, m2, m3 = st.columns(3)
    m1.metric("ความคืบหน้ารวมทั้งหมด", f"{overall_pct}%")
    m2.metric("จำนวนช่องที่กรอกแล้ว", f"{total_filled_cells:,} ช่อง")
    m3.metric("คงเหลือยังไม่ได้กรอก", f"{total_remaining_cells:,} ช่อง")
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("##### 📌 สรุปเปอร์เซ็นต์การกรอกข้อมูลรายชั้นเรียน")
    
    p_cols = st.columns(len(SHEET_NAMES))
    for i, sheet in enumerate(SHEET_NAMES):
        with p_cols[i]:
            info = class_progress.get(sheet, {'pct': 0, 'filled': 0, 'remaining': 0, 'total': 0})
            st.markdown(f"**ระดับชั้น {sheet}** ({info['pct']}%)")
            st.progress(info['pct'] / 100)
            st.caption(f"✅ กรอกแล้ว: **{info['filled']}** ช่อง &nbsp;|&nbsp; ⏳ คงเหลือ: **{info['remaining']}** ช่อง")
            
    st.markdown("---")
    
    # --- 2. นักเรียนที่ได้เกรดเฉลี่ยสูงสุด 5 อันดับแรก ---
    st.markdown("### 🏆 นักเรียนที่ได้เกรดเฉลี่ยสูงสุด 5 อันดับแรก")
    
    top_tabs = st.tabs([f"ระดับชั้น {sheet}" for sheet in SHEET_NAMES])
    for i, sheet in enumerate(SHEET_NAMES):
        with top_tabs[i]:
            if sheet in all_data:
                df = all_data[sheet]
                top5_df = df.sort_values('เกรดเฉลี่ย', ascending=False).head(5)
                st.markdown(render_top5_table(top5_df), unsafe_allow_html=True)
            else:
                st.info("ไม่มีข้อมูลในชั้นเรียนนี้")
                
    st.markdown("---")
    
    # --- 3. สรุปรวมเกรดเฉลี่ยรายวิชาของแต่ละห้องเรียน ---
    st.markdown("### 📚 สรุปเกรดเฉลี่ยแยกตามรายวิชา")
    
    selected_dash_sheet = st.selectbox("📌 เลือกชั้นเรียนที่ต้องการดูสรุปรายวิชา:", SHEET_NAMES)
    
    if selected_dash_sheet in all_data:
        df = all_data[selected_dash_sheet]
        subjs = all_subject_cols.get(selected_dash_sheet, [])
        
        subj_avg_list = []
        for col in subjs:
            # คำนวณค่าเฉลี่ยเฉพาะตัวเลขเกรด
            numeric_vals = pd.to_numeric(df[col], errors='coerce').dropna()
            avg_val = round(numeric_vals.mean(), 2) if len(numeric_vals) > 0 else 0.0
            cr, stype = get_subject_info(col)
            subj_avg_list.append({
                'ชื่อวิชา': col,
                'ประเภท': stype,
                'หน่วยกิต': cr,
                'เกรดเฉลี่ยวิชา': avg_val
            })
            
        subj_avg_df = pd.DataFrame(subj_avg_list)
        
        # แสดงกราฟแท่งเกรดเฉลี่ยรายวิชา
        st.markdown(f"#### 📊 กราฟสรุปเกรดเฉลี่ยรายวิชา (ระดับชั้น {selected_dash_sheet})")
        chart_data = subj_avg_df.set_index('ชื่อวิชา')[['เกรดเฉลี่ยวิชา']]
        st.bar_chart(chart_data)
        
        # แสดงตารางสรุป
        with st.expander(f"📋 ดูตารางสรุปเกรดเฉลี่ยรายวิชาทั้งหมด (ระดับชั้น {selected_dash_sheet})", expanded=True):
            st.dataframe(
                subj_avg_df, 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "เกรดเฉลี่ยวิชา": st.column_config.ProgressColumn(
                        "เกรดเฉลี่ยวิชา (GPA)",
                        format="%.2f",
                        min_value=0.0,
                        max_value=4.0
                    )
                }
            )

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
