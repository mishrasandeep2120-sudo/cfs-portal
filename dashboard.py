import csv
import os
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime
from tkcalendar import DateEntry
from zk import ZK

# --- YAHAN APNA USERNAME AUR PASSWORD LIKHEIN ---
NEW_USERNAME = "controlf"      # Jaise: "controlf"
NEW_PASSWORD = "Tjno@1980"  # Jaise: "Tjno@1980"
# ----------------------------------------------------

class LoginWindow:
    def __init__(self, root, on_success):
        self.root = root
        self.on_success = on_success
        
        # Window ka upar ka Title
        self.root.title("Control F Solutions") 
        self.root.geometry("450x300")
        self.root.resizable(False, False)
        self.root.configure(bg="#f0f4f9")
        
        # Top Blue Header Banner
        header = tk.Frame(self.root, bg="#3b71ca", height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="Control F Solutions", font=("Arial", 18, "bold"), fg="white", bg="#3b71ca").pack(pady=12, padx=15, anchor="w")

        # Form Layout
        form = tk.Frame(self.root, bg="#f0f4f9")
        form.pack(fill="both", expand=True, padx=30, pady=10)

        tk.Label(form, text="Login Name:", font=("Arial", 10), bg="#f0f4f9").grid(row=0, column=0, sticky="e", pady=15, padx=5)
        self.user_txt = ttk.Entry(form, width=28, font=("Arial", 10))
        self.user_txt.grid(row=0, column=1, pady=15, padx=5)
        self.user_txt.focus()

        tk.Label(form, text="Password:", font=("Arial", 10), bg="#f0f4f9").grid(row=1, column=0, sticky="e", pady=10, padx=5)
        self.pass_txt = ttk.Entry(form, width=28, font=("Arial", 10), show="*")
        self.pass_txt.grid(row=1, column=1, pady=10, padx=5)

        # Buttons
        btn_frame = tk.Frame(form, bg="#f0f4f9")
        btn_frame.grid(row=2, column=1, sticky="w", pady=20)
        ttk.Button(btn_frame, text="Login", width=10, command=self.check_login).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Close", width=10, command=self.root.quit).pack(side="left", padx=5)

    def check_login(self):
        if self.user_txt.get().strip() == NEW_USERNAME and self.pass_txt.get().strip() == NEW_PASSWORD:
            self.on_success()
        else:
            messagebox.showerror("Login Failed", "Galat Login Name ya Password!")

class DeviceManagementApp:
    def __init__(self, root):
        self.root = root
        
        # ---> YAHAN SE MAIN PANEL KA TITLE BADLA GAYA HAI <---
        self.root.title("Control F Solutions - Device Management (Python)")
        
        self.root.geometry("980x580")
        self.devices = [
            {"select": "No", "name": "Office_Main", "type": "Tcp/IP", "ip": "192.168.1.51", "port": 4370, "dev_type": "Attendance", "location": "Main Gate", "last_date": "-", "last_time": "-", "status": "Ready"},
            {"select": "No", "name": "Server_Room", "type": "Tcp/IP", "ip": "192.168.1.52", "port": 4370, "dev_type": "Access Control", "location": "Server Rm", "last_date": "-", "last_time": "-", "status": "Ready"}
        ]
        self.create_widgets()
        self.load_devices()

    def create_widgets(self):
        top = ttk.LabelFrame(self.root, text=" Options & Date Filter ", padding=10)
        top.pack(fill="x", padx=10, pady=5)
        
        self.check_parallel = tk.BooleanVar(value=True)
        ttk.Checkbutton(top, text="Parallel Download", variable=self.check_parallel).pack(side="left", padx=10)
        self.check_clear = tk.BooleanVar(value=False)
        ttk.Checkbutton(top, text="Auto Clear Logs after Download", variable=self.check_clear).pack(side="left", padx=10)
        
        ttk.Label(top, text="From:").pack(side="left", padx=(20, 5))
        self.cal_from = DateEntry(top, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='dd-mm-yyyy')
        self.cal_from.pack(side="left", padx=5)
        
        ttk.Label(top, text="To:").pack(side="left", padx=(10, 5))
        self.cal_to = DateEntry(top, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='dd-mm-yyyy')
        self.cal_to.pack(side="left", padx=5)

        grid = ttk.LabelFrame(self.root, text=" Connected Devices ", padding=10)
        grid.pack(fill="both", expand=True, padx=10, pady=5)

        cols = ("select", "name", "type", "ip", "port", "dev_type", "location", "last_date", "last_time", "status")
        self.tree = ttk.Treeview(grid, columns=cols, show="headings", height=15)

        headers = {"select": "Select", "name": "Device Name", "type": "Connection Type", "ip": "IP Address", "port": "Port", "dev_type": "Device Type", "location": "Location", "last_date": "Last Date", "last_time": "Last Time", "status": "Status"}
        for c, t in headers.items():
            self.tree.heading(c, text=t)
            self.tree.column(c, width=90, anchor="center")
        
        self.tree.column("name", width=120)
        self.tree.column("ip", width=110)
        
        sb = ttk.Scrollbar(grid, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.tree.bind("<Double-1>", self.toggle_selection)

        btn_frame = ttk.Frame(self.root, padding=10)
        btn_frame.pack(fill="x", padx=10, pady=5)
        ttk.Button(btn_frame, text="Download Logs", command=self.start_download_thread).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Ping Device", command=self.start_ping_thread).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Exit", command=self.root.quit).pack(side="right", padx=5)

    def load_devices(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        for d in self.devices:
            self.tree.insert("", "end", values=(d["select"], d["name"], d["type"], d["ip"], d["port"], d["dev_type"], d["location"], d["last_date"], d["last_time"], d["status"]))

    def toggle_selection(self, event):
        item = self.tree.selection()
        if not item: return
        val = list(self.tree.item(item, "values"))
        new_sel = "Yes" if val[0] == "No" else "No"
        val[0] = new_sel
        self.tree.item(item, values=val)
        for d in self.devices:
            if d["ip"] == val[3]: d["select"] = new_sel

    def update_status(self, ip, status):
        for item in self.tree.get_children():
            val = list(self.tree.item(item, "values"))
            if val[3] == ip:
                val[9] = status
                self.tree.item(item, values=val)
                break

    def update_last_punch(self, ip, date, time):
        for item in self.tree.get_children():
            val = list(self.tree.item(item, "values"))
            if val[3] == ip:
                val[7] = date
                val[8] = time
                self.tree.item(item, values=val)
                break

    def start_download_thread(self):
        threading.Thread(target=self.download_logs, daemon=True).start()
    def download_logs(self):
        f_date, t_date = self.cal_from.get_date(), self.cal_to.get_date()
        sel_devs = [d for d in self.devices if d["select"] == "Yes"]
        if not sel_devs:
            messagebox.showwarning("Warning", "कृपया डिवाइस सिलेक्ट करें।")
            return

        for d in sel_devs:
            self.update_status(d["ip"], "Connecting...")
            zk = ZK(d["ip"], port=d["port"], timeout=5)
            conn = None
            try:
                conn = zk.connect()
                self.update_status(d["ip"], "Downloading...")
                
                u_map = {}
                try:
                    for u in conn.get_users(): 
                        u_map[str(u.user_id).strip()] = u.name if u.name else f"Emp {u.user_id}"
                except: pass

                grouped = dict()
                for log in conn.get_attendance():
                    l_date = log.timestamp.date()
                    if f_date <= l_date <= t_date:
                        k = (str(log.user_id).strip(), log.timestamp.strftime('%Y-%m-%d'))
                        if k not in grouped: 
                            grouped[k] = list()
                        grouped[k].append(log.timestamp)

                logs = list()
                for (uid, dt), t_list in grouped.items():
                    t_list.sort()
                    in_t = t_list[0].strftime('%H:%M:%S')
                    out_t = t_list[-1].strftime('%H:%M:%S') if len(t_list) > 1 else "-"
                    logs.append([uid, u_map.get(uid, f"Emp {uid}"), dt, in_t, out_t, d["name"]])

                if logs:
                    path = os.path.join(os.path.expanduser('~'), 'Documents', f"attendance_logs_{d['name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
                    with open(path, mode='w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow(["User ID", "Employee Name", "Date", "In Time", "Out Time", "Device Name"])
                        writer.writerows(logs)
                    
                    if self.check_clear.get(): 
                        conn.clear_attendance()
                        self.update_status(d["ip"], "Logs Cleared")
                    else: 
                        self.update_status(d["ip"], "Success")
                    
                    self.update_last_punch(d["ip"], logs[-1][2], logs[-1][4] if logs[-1][4] != "-" else logs[-1][3])
                    messagebox.showinfo("Success", f"डेटा सेव हो गया:\n{path}")
                else:
                    self.update_status(d["ip"], "No Data")
            except Exception as e:
                self.update_status(d["ip"], "Failed")
                messagebox.showerror("Error", f"Error: {str(e)}")
            finally:
                if conn: conn.disconnect()

    def start_ping_thread(self):
        threading.Thread(target=self.ping_devices, daemon=True).start()

    def ping_devices(self):
        for d in self.devices:
            self.update_status(d["ip"], "Checking...")
            rep = os.system(f"ping -n 1 {d['ip']}" if os.name == 'nt' else f"ping -c 1 {d['ip']}")
            self.update_status(d["ip"], "Ready" if rep == 0 else "Offline")

def run_main():
    login_root.destroy()
    m_root = tk.Tk()
    app = DeviceManagementApp(m_root)
    m_root.mainloop()

if __name__ == "__main__":
    login_root = tk.Tk()
    login_app = LoginWindow(login_root, run_main)
    login_root.mainloop()
