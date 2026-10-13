import csv
import os
from datetime import datetime
import streamlit as st
import pandas as pd
from zk import ZK

# --- CONFIGURATION ---
st.set_page_config(page_title="Control F Solutions - Device Management", layout="wide")

NEW_USERNAME = "controlf"      
NEW_PASSWORD = "Tjno@1980"  

# --- SESSION STATE INITIALIZATION ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "devices" not in st.session_state:
    st.session_state.devices = [
        {"Select": False, "Device Name": "Office_Main", "Connection Type": "Tcp/IP", "IP Address": "192.168.1.51", "Port": 4370, "Device Type": "Attendance", "Location": "Main Gate", "Last Date": "-", "Last Time": "-", "Status": "Ready"},
        {"Select": False, "Device Name": "Server_Room", "Connection Type": "Tcp/IP", "IP Address": "192.168.1.52", "Port": 4370, "Device Type": "Access Control", "Location": "Server Rm", "Last Date": "-", "Last Time": "-", "Status": "Ready"}
    ]

# --- LOGIN SCREEN ---
def show_login():
    st.markdown(
        """
        <div style="background-color:#3b71ca; padding:15px; border-radius:5px; margin-bottom:20px;">
            <h2 style="color:white; margin:0; font-family:Arial;">Control F Solutions</h2>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    with st.form("login_form"):
        username = st.text_input("Login Name:")
        password = st.text_input("Password:", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            if username.strip() == NEW_USERNAME and password.strip() == NEW_PASSWORD:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Galat Login Name ya Password!")

# --- MAIN APP INTERFACE ---
def show_dashboard():
    st.title("Control F Solutions - Device Management (Python)")
    
    # --- Top Options & Date Filter ---
    st.subheader("Options & Date Filter")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        check_parallel = st.checkbox("Parallel Download", value=True)
    with col2:
        check_clear = st.checkbox("Auto Clear Logs after Download", value=False)
    with col3:
        from_date = st.date_input("From Date", datetime.now().date())
    with col4:
        to_date = st.date_input("To Date", datetime.now().date())
        
    st.divider()

    # --- Connected Devices Table ---
    st.subheader("Connected Devices")
    st.info("डिवाइस को सिलेक्ट करने या डेटा एडिट करने के लिए नीचे दी गई टेबल में 'Select' कॉलम को टिक करें।")
    
    # Converting device list to Dataframe for Streamlit Data Editor
    df_devices = pd.DataFrame(st.session_state.devices)
    
    # Data editor allows user to check boxes directly
    edited_df = st.data_editor(
        df_devices, 
        use_container_width=True, 
        disabled=["Device Name", "Connection Type", "IP Address", "Port", "Device Type", "Location", "Last Date", "Last Time", "Status"]
    )
    
    # Sync status back to session state
    st.session_state.devices = edited_df.to_dict('records')

    # --- Action Buttons ---
    btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 6])
    
    # 1. PING DEVICE BUTTON
    if btn_col2.button("Ping Device", use_container_width=True):
        st.write("### Pinging Devices...")
        for i, d in enumerate(st.session_state.devices):
            st.session_state.devices[i]["Status"] = "Checking..."
            ip = d["IP Address"]
            
            # Cross-platform ping check
            rep = os.system(f"ping -n 1 {ip}" if os.name == 'nt' else f"ping -c 1 {ip}")
            if rep == 0:
                st.session_state.devices[i]["Status"] = "Ready"
                st.success(f"{d['Device Name']} ({ip}) is Online!")
            else:
                st.session_state.devices[i]["Status"] = "Offline"
                st.error(f"{d['Device Name']} ({ip}) is Offline!")
        st.rerun()

    # 2. DOWNLOAD LOGS BUTTON
    if btn_col1.button("Download Logs", use_container_width=True):
        sel_devs = [d for d in st.session_state.devices if d["Select"] == True]
        
        if not sel_devs:
            st.warning("कृपया कम से कम एक डिवाइस सिलेक्ट करें।")
        else:
            all_logs = []
            
            for d in sel_devs:
                # Update status visually
                st.info(f"Connecting to {d['Device Name']} ({d['IP Address']})...")
                zk = ZK(d["IP Address"], port=d["Port"], timeout=5)
                conn = None
                
                try:
                    conn = zk.connect()
                    st.info(f"Downloading logs from {d['Device Name']}...")
                    
                    u_map = {}
                    try:
                        for u in conn.get_users():
                            u_map[str(u.user_id).strip()] = u.name if u.name else f"Emp {u.user_id}"
                    except:
                        pass

                    grouped = {}
                    for log in conn.get_attendance():
                        l_date = log.timestamp.date()
                        if from_date <= l_date <= to_date:
                            k = (str(log.user_id).strip(), log.timestamp.strftime('%Y-%m-%d'))
                            if k not in grouped:
                                grouped[k] = []
                            grouped[k].append(log.timestamp)

                    logs = []
                    for (uid, dt), t_list in grouped.items():
                        t_list.sort()
                        in_t = t_list[0].strftime('%H:%M:%S')
                        out_t = t_list[-1].strftime('%H:%M:%S') if len(t_list) > 1 else "-"
                        logs.append([uid, u_map.get(uid, f"Emp {uid}"), dt, in_t, out_t, d["Device Name"]])

                    if logs:
                        all_logs.extend(logs)
                        
                        # Find matching index to update status and timestamps
                        for idx, dev in enumerate(st.session_state.devices):
                            if dev["IP Address"] == d["IP Address"]:
                                if check_clear:
                                    conn.clear_attendance()
                                    st.session_state.devices[idx]["Status"] = "Logs Cleared"
                                else:
                                    st.session_state.devices[idx]["Status"] = "Success"
                                
                                st.session_state.devices[idx]["Last Date"] = logs[-1][2]
                                st.session_state.devices[idx]["Last Time"] = logs[-1][4] if logs[-1][4] != "-" else logs[-1][3]
                        
                        st.success(f"{d['Device Name']} से डेटा सफलतापूर्वक निकाल लिया गया है!")
                    else:
                        for idx, dev in enumerate(st.session_state.devices):
                            if dev["IP Address"] == d["IP Address"]:
                                st.session_state.devices[idx]["Status"] = "No Data"
                        st.warning(f"{d['Device Name']} में चुनी गई तारीखों का कोई डेटा नहीं मिला।")
                        
                except Exception as e:
                    for idx, dev in enumerate(st.session_state.devices):
                        if dev["IP Address"] == d["IP Address"]:
                            st.session_state.devices[idx]["Status"] = "Failed"
                    st.error(f"{d['Device Name']} Error: {str(e)}")
                finally:
                    if conn:
                        conn.disconnect()

            # If data is fetched, provide a browser download button
            if all_logs:
                df_logs = pd.DataFrame(all_logs, columns=["User ID", "Employee Name", "Date", "In Time", "Out Time", "Device Name"])
                csv_data = df_logs.to_csv(index=False, encoding='utf-8')
                
                filename = f"attendance_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                
                st.markdown("### 📥 अपना डेटा यहाँ से डाउनलोड करें:")
                st.download_button(
                    label="Download Attendance CSV File",
                    data=csv_data,
                    file_name=filename,
                    mime='text/csv'
                )
                
            # Rerun to update the status in the main table layout
            st.rerun()

# --- MAIN RUN LOGIC ---
if __name__ == "__main__":
    if not st.session_state.logged_in:
        show_login()
    else:
        show_dashboard()
