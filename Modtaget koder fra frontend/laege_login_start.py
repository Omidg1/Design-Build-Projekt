import requests
import subprocess

def login_og_start_gui():
    url = "http://localhost:60070/login"
    data = {
        "cpr-nummer": "04",
        "adgangskode": "dtu"
    }

    with requests.Session() as s:
        response = s.post(url, data=data)
        if "menu" in response.url:  # Hvis lægen logges ind og Flask sender videre
            print("✅ Læge login lykkedes. Åbner dashboard...")
            subprocess.Popen(["python", "laege_dashboard_tkinter.py"])
        else:
            print("❌ Login mislykkedes.")

if __name__ == "__main__":
    login_og_start_gui()
