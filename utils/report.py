from fpdf import FPDF
from datetime import datetime

class LabReportPDF(FPDF):
    def header(self):
        self.set_fill_color(26, 54, 93)
        self.rect(0, 0, 210, 40, 'F')
        
        self.set_font("Helvetica", "B", 18)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, "FOCIT LAB MANAGER CENTRAL REPORT", ln=True, align="C")
        
        self.set_font("Helvetica", "", 10)
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cell(0, 5, f"Generated: {current_time} | Scope: Main Computer Lab", ln=True, align="C")
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}} - Confidential IT Infrastructure Data", align="C")

def create_lab_report(data: dict):
    pdf = LabReportPDF(orientation="P", unit="mm", format="A4")
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # -------------------------------------------------------------------------
    # 1. EXECUTIVE SUMMARY SECTION
    # -------------------------------------------------------------------------
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(26, 54, 93)
    pdf.cell(0, 10, "1. Executive KPI Summary", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)
    
    pdf.set_fill_color(240, 244, 248)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 11)

    summary_text = (
        f"-> Total Monitored Workstations: {data["status"][0]} Active / {data["status"][1]} Offline\n"
        f"-> Critical Maintenance Flags: {data["critical"]} System critically low on primary / virtual storage capacity.\n"
        f"-> Security & Compliance: 100% Antivirus compliance. {data["security"]} System requires a reboot for patches."
    )
    pdf.multi_cell(0, 7, summary_text, border=1, fill=True)
    pdf.ln(8)

    # -------------------------------------------------------------------------
    # 2. DETAILED INVENTORY SECTION
    # -------------------------------------------------------------------------
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(26, 54, 93)
    pdf.cell(0, 10, "2. Expanded Asset Inventory", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    raw_devs = data.get("devices", {})
    devices = []
    for dev in raw_devs:
        device = {}
        device["status"] = dev.get("status", "N/A")
        device["host"] = dev.get("agent_id", "N/A")
        device["bench"] = dev.get("bench", "N/A")
        device["ip"] = dev.get("ip_on_lan", "N/A")
        device["mac"] = dev.get("mac_address", "N/A")
        device["cpu"] = f"{dev.get("cpu_name", "N/A")} ({dev.get("cores_physical", "?")} Cores / {dev.get("logical", "?")} Threads)"
        device["ram"] = f"{dev.get("ram_total_gb", "?")} GB ({dev.get("ram_used_percent", "?")}% Used)"
        device["storage"] = []
        for drive in dev.get("storage", []):
            device["storage"].append(f"{drive.get("total_gb", "?")} Total [{drive.get("free_gb", "?")} GB FREE - {drive.get("used_percent", "?")}% USED]")
        device["os"] = f"{dev.get("platform", "N/A")} {dev.get("release", "?")} (v{dev.get("version", "N/A")})"
        device["uptime"] = dev.get("uptime", "?")
        device["note"] = dev.get("note", [])
        if dev["status"] == "CRITICAL":
            device["color"] = (211, 47, 47)
        elif dev["status"] == "WARNING":
            device["color"] = (245, 124, 0)
        elif dev["status"] == "HEALTHY":
            device["color"] = (56, 142, 60)
        else: device["color"] = (67, 133, 133)
        devices.append(device)

    for dev in devices:
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_fill_color(*dev['color'])
        pdf.set_text_color(255, 255, 255)
        pdf.cell(40, 7, f" [{dev['status']}]", fill=True)
        
        pdf.set_fill_color(230, 235, 240)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(150, 7, f" Hostname: {dev['host']}    |    Location: {dev['bench']}", fill=True, ln=True)
        
        pdf.set_font("Helvetica", "", 10)
        pdf.set_x(15)
        
        details = (
            f"-> Network Setup : IP: {dev['ip']}   |   MAC: {dev['mac']}\n"
            f"-> Processor     : {dev['cpu']}\n"
            f"-> RAM Status    : {dev['ram']}\n"
            f"-> Disk Space    : {dev['storage'][0]}\n"
            f"-> Operating Sys : {dev['os']}  (Uptime: {dev['uptime']})\n"
            f"-> System Note   : {dev['note'][0]}"
        )
        pdf.multi_cell(0, 6, details, border='L')
        pdf.ln(6)

    from config import REPORT_DIR
    report_path = REPORT_DIR / "FOCIT_Lab_Report.pdf"
    pdf.output(str(report_path))
    print(f"[+] Professional PDF generated successfully as '{report_path}'!")

if __name__ == "__main__":
    # Default test data for running this module directly
    sample_data = {
        "status": [5, 2],
        "critical": 1,
        "security": 0,
        "devices": [
            {
                "status": "HEALTHY",
                "agent_id": "TEST-PC-01",
                "bench": "Bench A",
                "ip_on_lan": "192.168.1.10",
                "mac_address": "AA:BB:CC:DD:EE:FF",
                "cpu_name": "Intel i5",
                "cores_physical": 4,
                "logical": 8,
                "ram_total_gb": 16,
                "ram_used_percent": 45,
                "storage": [{"total_gb": 500, "free_gb": 250, "used_percent": 50}],
                "platform": "Windows",
                "release": "10",
                "version": "19045",
                "uptime": 86400,
                "note": ["All systems operational"]
            }
        ]
    }
    create_lab_report(sample_data)
