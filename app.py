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
            font-size: 2.2rem;
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
        .summary-card {
            background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
            color: white;
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        .summary-card h3 {
            color: #f8fafc;
            margin-bottom: 5px;
        }
        
        /* สไตล์ตารางนักเรียน */
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

# --- ฟังก์ชันอ่านและคำนวณข้อมูล (GPA & ลำดับที่) ---
def load_sheet_data(sheet_name):
    try:
        encoded_sheet = urllib.parse.quote(sheet_name)
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={encoded_sheet}"
        
        df_raw = pd.read_csv(url, header=None)
        
        # หาตำแหน่งแถวที่เป็นหัวตาราง
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
                
                # แยกคอลัมน์วิชาเรียน (ไม่รวม เลขที่ และ ชื่อ-นามสกุล)
                non_subj_keywords = ['เลขที่', 'ชื่อ - นามสกุล', 'เกรดเฉลี่ย', 'ลำดับที่', 'รวม', 'เฉลี่ย', 'ผลการเรียน']
                subject_cols = [c for c in df.columns if c not in ['เลขที่', 'ชื่อ - นามสกุล'] and not any(kw == c for kw in non_subj_keywords)]
                
                # คำนวณเกรดเฉลี่ย (GPA)
                def calc_gpa(row):
                    grades = []
                    for col in subject_cols:
                        val = row[col]
                        try:
                            v_float = float(val)
                            if not np.isnan(v_float):
                                grades.append(v_float)
                        except (ValueError, TypeError):
                            pass
                    return round(np.mean(grades), 2) if len(grades) > 0 else np.nan

                df['เกรดเฉลี่ย'] = df.apply(calc_gpa, axis=1)
                
                # จัดลำดับที่ในห้องเรียน
                df['ลำดับที่'] = df['เกรดเฉลี่ย'].rank(ascending=False, method='min').astype('Int64')
                
                return df, subject_cols
                
        return pd.DataFrame(), []
    except Exception as e:
        st.error(f"ไม่สามารถโหลดข้อมูลแผ่นงาน {sheet_name} ได้: {e}")
        return pd.DataFrame(), []

def load_all_data():
    all_data = {}
    all_subject_cols = {}
    for sheet in SHEET_NAMES:
        df, subjs = load_sheet_data(sheet)
        if not df.empty:
            all_data[sheet] = df
            all_subject_cols[sheet] = subjs
    return all_data, all_subject_cols

# --- ฟังก์ชันสร้างตาราง HTML สไตล์พิเศษสำหรับนักเรียน ---
def render_student_table_html(df, subject_cols):
    html = '<div class="student-table-container"><table class="student-table"><thead><tr>'
    normal_cols = ['เลขที่', 'ชื่อ - นามสกุล', 'เกรดเฉลี่ย', 'ลำดับที่', 'ผลการเรียน']
    
    # แสดงคอลัมน์ข้อมูลหลัก และคอลัมน์วิชาเรียน
    display_cols = [c for c in df.columns if c in normal_cols or c in subject_cols]
    
    for col in display_cols:
        if any(nc in str(col) for nc in normal_cols):
            html += f'<th style="height: auto; padding: 8px;">{col}</th>'
        else:
            html += f'<th class="rotate-header"><div>{col}</div></th>'
            
    html += '</tr></thead><tbody>'
    non_score_cols = ['เลขที่', 'ชื่อ - นามสกุล', 'ลำดับที่']
    
    for _, row in df.iterrows():
        html += '<tr>'
        for col in display_cols:
            val = row[col]
            is_missing = pd.isna(val) or val is None or str(val).strip() == '' or str(val).strip().lower() in ['nan', 'none']
            
            if col in non_score_cols:
                if col == 'ชื่อ - นามสกุล':
                    html += f'<td class="name-cell">{val if not is_missing else ""}</td>'
                else:
                    html += f'<td>{int(val) if not is_missing and isinstance(val, float) and val.is_integer() else (val if not is_missing else "-")}</td>'
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
st.markdown('<div class="main-header">🎓 ระบบรายงานผลการเรียนออนไลน์</div>', unsafe_allow_html=True)

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135810.png", width=80)
    st.markdown("## 📍 เมนูหลัก")
    menu = st.radio("เลือกหน้าต่างการทำงาน:", [
        "🔍 สำหรับนักเรียน (ค้นหาคะแนน)", 
        "📊 แดชบอร์ดสรุปภาพรวม", 
        "📝 สำหรับครู (จัดการคะแนน)"
    ])
    st.markdown("---")
    st.caption("📱 รองรับการใช้งานผ่านมือถือและคอมพิวเตอร์")

all_data, all_subject_cols = load_all_data()

# ==========================================
# 1. หน้า สำหรับนักเรียน (ค้นหาคะแนน)
# ==========================================
if menu == "🔍 สำหรับนักเรียน (ค้นหาคะแนน)":
    st.markdown('<h2 class="sub-header">🔍 ค้นหาผลการเรียน</h2>', unsafe_allow_html=True)
    
    search_name = st.text_input("พิมพ์ชื่อ หรือนามสกุล ของนักเรียน (เช่น สมชาย หรือ พชร)", placeholder="กรอกชื่อเพื่อค้นหา...").strip()
    
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
                        st.markdown(f"""
                        <div class="summary-card">
                            <h3>👤 {student['ชื่อ - นามสกุล']} (ระดับชั้น {sheet_name})</h3>
                            <p style="margin: 0; font-size: 1.1rem;">
                                🏆 <b>เกรดเฉลี่ย (GPA):</b> <span style="font-size: 1.4rem; color: #fde047;"><b>{student['เกรดเฉลี่ย']:.2f}</b></span> &nbsp;|&nbsp; 
                                📊 <b>อันดับที่ในห้องเรียน:</b> <span style="font-size: 1.3rem;"><b>{student['ลำดับที่']}</b></span> / {total_students} คน &nbsp;|&nbsp; 
                                📚 <b>วิชาที่เรียน:</b> {len(subj_cols)} วิชา
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        with st.expander(f"📖 ดูรายละเอียดคะแนนรายวิชาของ {student['ชื่อ - นามสกุล']}", expanded=True):
                            st.markdown(render_student_table_html(student_data, subj_cols), unsafe_allow_html=True)
                        
        if not found:
            st.warning("⚠️ ไม่พบรายชื่อนี้ในระบบ กรุณาตรวจสอบการสะกดคำอีกครั้ง")

# ==========================================
# 2. หน้า แดชบอร์ดสรุปภาพรวม
# ==========================================
elif menu == "📊 แดชบอร์ดสรุปภาพรวม":
    st.markdown('<h2 class="sub-header">📊 แดชบอร์ดสรุปผลการเรียน</h2>', unsafe_allow_html=True)
    
    # --- ส่วนที่ 1: สรุป Top 5 เกรดเฉลี่ยสูงสุดของแต่ละชั้นเรียน ---
    st.markdown("### 🏆 นักเรียนที่ได้เกรดเฉลี่ยสูงสุด 5 อันดับแรก (แต่ละชั้นเรียน)")
    
    tabs = st.tabs([f"ระดับชั้น {sheet}" for sheet in SHEET_NAMES])
    
    for i, sheet in enumerate(SHEET_NAMES):
        with tabs[i]:
            if sheet in all_data:
                df = all_data[sheet]
                top5_df = df.sort_values('เกรดเฉลี่ย', ascending=False).head(5)
                
                display_top5 = top5_df[['ลำดับที่', 'เลขที่', 'ชื่อ - นามสกุล', 'เกรดเฉลี่ย']].copy()
                display_top5.columns = ['อันดับในห้อง', 'เลขที่', 'ชื่อ - นามสกุล', 'เกรดเฉลี่ย (GPA)']
                
                st.dataframe(
                    display_top5,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "เกรดเฉลี่ย (GPA)": st.column_config.ProgressColumn(
                            "เกรดเฉลี่ย (GPA)",
                            format="%.2f",
                            min_value=0.0,
                            max_value=4.0
                        )
                    }
                )
            else:
                st.info("ไม่มีข้อมูลในชั้นเรียนนี้")
                
    st.markdown("---")
    
    # --- ส่วนที่ 2: กราฟสรุปจำนวนเกรดของแต่ละวิชา ในแต่ละชั้น ---
    st.markdown("### 📈 กราฟแสดงรายละเอียดจำนวนเกรดของแต่ละวิชา")
    
    selected_level = st.selectbox("📌 เลือกระดับชั้นเรียน:", SHEET_NAMES)
    
    if selected_level in all_data:
        df_level = all_data[selected_level]
        subj_cols = all_subject_cols.get(selected_level, [])
        
        # ตัวเลือกรายวิชา (รวมตัวเลือก "ทุกวิชารวมกัน")
        selected_subject = st.selectbox("📚 เลือกวิชาที่ต้องการดูการแจกแจงเกรด:", ["ทุกวิชารวมกัน"] + subj_cols)
        
        # แปลงข้อมูลเป็นตารางคู่ (วิชา - เกรด)
        melted = df_level.melt(id_vars=['ชื่อ - นามสกุล'], value_vars=subj_cols, var_name='วิชา', value_name='เกรด')
        melted['เกรด'] = melted['เกรด'].apply(lambda x: 'ยังไม่ส่ง' if pd.isna(x) or str(x).strip() == '' or str(x).strip().lower() in ['nan', 'none'] else str(x))
        
        if selected_subject != "ทุกวิชารวมกัน":
            filtered_melted = melted[melted['วิชา'] == selected_subject]
        else:
            filtered_melted = melted
            
        grade_counts = filtered_melted['เกรด'].value_counts().reset_index()
        grade_counts.columns = ['ระดับเกรด', 'จำนวนนักเรียน (คน)']
        
        # แสดงกราฟแท่ง
        st.markdown(f"#### 📊 จำนวนนักเรียนในแต่ละระดับเกรด ({selected_subject} - ชั้น {selected_level})")
        st.bar_chart(grade_counts.set_index('ระดับเกรด'))
        
        # ตารางสรุปจำนวนเกรดแยกตามวิชา
        with st.expander("📋 ดูตารางสรุปจำนวนเกรดแยกตามรายวิชาทั้งหมด"):
            pivot_grade = melted.groupby(['วิชา', 'เกรด']).size().unstack(fill_value=0)
            st.dataframe(pivot_grade, use_container_width=True)

# ==========================================
# 3. หน้า สำหรับครู (จัดการคะแนน)
# ==========================================
elif menu == "📝 สำหรับครู (จัดการคะแนน)":
    st.markdown('<h2 class="sub-header">📝 ระบบจัดการคะแนน</h2>', unsafe_allow_html=True)
    
    password = st.text_input("🔑 รหัสผ่านสำหรับคุณครู", type="password")
    
    if password == "1234":
        st.success("🔓 ยืนยันตัวตนสำเร็จ")
        st.info("💡 คุณครูสามารถเข้าไปแก้ไขคะแนนโดยตรงได้ที่ Google Sheets ลิงก์ด้านล่าง ระบบจะอัปเดตคำนวณเกรดเฉลี่ยบนเว็บโดยอัตโนมัติทันที:")
        st.markdown(f"👉 **[คลิกที่นี่เพื่อเปิด Google Sheet แก้ไขคะแนน]({GSHEET_URL})**")
        
        selected_sheet = st.selectbox("📌 เลือกดูตารางคะแนนล่าสุด", SHEET_NAMES)
        if selected_sheet in all_data:
            st.dataframe(all_data[selected_sheet], use_container_width=True, hide_index=True)
            
    elif password != "":
        st.error("❌ รหัสผ่านไม่ถูกต้อง!")
