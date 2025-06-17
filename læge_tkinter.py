import tkinter as tk
from tkinter import ttk, messagebox
import requests
import io
from PIL import Image, ImageTk
import functools

SERVER_URL = "http://80.198.171.108:60070"

class LaegeDashboard:
    def __init__(self, master):
        self.master = master
        self.master.title("🏥 Læge Dashboard – Fjernmonitorering")
        self.master.geometry("1050x900")
        self.master.configure(bg="#f2f2f2")

        title = tk.Label(master, text="Lægedashboard", font=("Arial", 20, "bold"), bg="#f2f2f2")
        title.pack(pady=15)

        # Patientvalg med søg
        patient_frame = tk.Frame(master, bg="#f2f2f2")
        patient_frame.pack(pady=5)
        tk.Label(patient_frame, text="Søg eller vælg patient:", bg="#f2f2f2").pack(side=tk.LEFT)
        self.sog_entry = ttk.Entry(patient_frame, width=30)
        self.sog_entry.pack(side=tk.LEFT, padx=5)
        self.sog_entry.bind("<KeyRelease>", self.opdater_dropdown)

        self.patient_valg = ttk.Combobox(patient_frame, state="readonly", width=40)
        self.patient_valg.pack(side=tk.LEFT, padx=5)
        self.patient_valg.bind("<<ComboboxSelected>>", self.vis_konsultation)
        self.patient_map = {}
        self.hent_patientliste()

        # Scrollbart område til billeder og data
        scroll_container = tk.Frame(master, bg="#f2f2f2")
        scroll_container.pack(fill="both", expand=True)

        canvas = tk.Canvas(scroll_container, bg="#f2f2f2")
        scrollbar = tk.Scrollbar(scroll_container, orient="vertical", command=canvas.yview)
        self.billed_frame = tk.Frame(canvas, bg="#f2f2f2")

        self.billed_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.billed_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Feedback
        feedback_frame = tk.LabelFrame(master, text="Send feedback", bg="#f2f2f2", padx=10, pady=10)
        feedback_frame.pack(pady=10)
        self.feedback_entry = tk.Text(feedback_frame, height=4, width=80)
        self.feedback_entry.pack()
        tk.Button(feedback_frame, text="📤 Send feedback", command=self.send_feedback).pack(pady=5)

        # Tidspunktvalg
        tidspunkt_frame = tk.LabelFrame(master, text="Foreslå ny e-konsultation", bg="#f2f2f2", padx=10, pady=10)
        tidspunkt_frame.pack(pady=10)
        tk.Label(tidspunkt_frame, text="Dato (YYYY-MM-DD):", bg="#f2f2f2").pack()
        self.dato_entry = ttk.Entry(tidspunkt_frame, width=30)
        self.dato_entry.insert(0, "2025-06-16")
        self.dato_entry.pack()

        tk.Label(tidspunkt_frame, text="Tidspunkt (HH:MM):", bg="#f2f2f2").pack()
        self.tid_entry = ttk.Entry(tidspunkt_frame, width=30)
        self.tid_entry.insert(0, "10:00")
        self.tid_entry.pack()

        tk.Button(tidspunkt_frame, text="🗓 Send tidspunkt", command=self.send_tidspunkt).pack(pady=5)

    def hent_patientliste(self):
        try:
            res = requests.get(f"{SERVER_URL}/api/patienter")
            if res.status_code == 200:
                data = res.json()
                self.alle_patienter = []
                for p in data:
                    label = f"{p['id']} – {p['cpr_nummer']}"
                    self.patient_map[label] = p["id"]
                    self.alle_patienter.append(label)
                self.patient_valg["values"] = self.alle_patienter
        except Exception as e:
            messagebox.showerror("Fejl", str(e))

    def opdater_dropdown(self, event=None):
        soeg = self.sog_entry.get().lower()
        filtreret = [p for p in self.alle_patienter if soeg in p.lower()]
        self.patient_valg["values"] = filtreret

    def vis_konsultation(self, event=None):
        valg = self.patient_valg.get()
        patient_id = self.patient_map.get(valg)
        if not patient_id:
            return

        self.valgt_patient_id = patient_id
        try:
            res = requests.get(f"{SERVER_URL}/api/konsultationer/{patient_id}")
            if res.status_code == 200:
                data = res.json()

                for widget in self.billed_frame.winfo_children():
                    widget.destroy()

                self.billeder = []
                if not data:
                    lbl = tk.Label(self.billed_frame, text="Ingen konsultationer fundet.", bg="#f2f2f2", font=("Arial", 12))
                    lbl.pack()
                    return

                for idx, k in enumerate(data):
                    besvaret = k.get("besvaret")
                    status_text = "✅ Besvaret" if besvaret else "⏳ Ikke besvaret"
                    status_color = "#28a745" if besvaret else "#dc3545"

                    card = tk.Frame(self.billed_frame, bg="#ffffff", bd=1, relief="solid", padx=10, pady=10)
                    card.pack(padx=10, pady=10, fill="x")

                    # Kun vis billede og svar, hvis den er besvaret
                    if besvaret:
                        billede_url = k.get("billede_url")
                        if billede_url and billede_url.strip():
                            try:
                                img_res = requests.get(f"{SERVER_URL}{billede_url}")
                                if img_res.status_code == 200:
                                    img = Image.open(io.BytesIO(img_res.content)).resize((200, 200))
                                    tk_img = ImageTk.PhotoImage(img)

                                    img_label = tk.Label(card, image=tk_img, bg="#ffffff", cursor="hand2")
                                    img_label.image = tk_img
                                    img_label.pack(side=tk.LEFT, padx=10)

                                    img_label.bind("<Button-1>", functools.partial(self.vis_stort_billede, img.copy()))
                            except Exception as e:
                                print(f"Billedfejl: {e}")
                    else:
                        # Hvis ikke besvaret, vis en tom pladsholder
                        img_label = tk.Label(card, text="(Ingen billede)", bg="#ffffff", width=25, height=12, fg="gray")
                        img_label.pack(side=tk.LEFT, padx=10)

                    # Tekstbeskrivelse uanset status
                    tekst = (
                        f"Konsultation #{idx+1}\n"
                        f"Tidspunkt: {k['oprettet_tidspunkt']}\n"
                        f"Status: {k['status']}\n"
                        f"Symptomer: {k['symptomer'] if besvaret else '(ikke besvaret)'}\n"
                        f"Medicin: {k['medicin'] if besvaret else '(ikke besvaret)'}\n"
                        f"Bivirkninger: {k['bivirkninger'] if besvaret else '(ikke besvaret)'}\n"
                        f"Gener: {k['gener']}/10\n" if besvaret else "Gener: (ikke angivet)\n"
                    )
                    tekst_label = tk.Label(card, text=tekst, justify="left", anchor="w", bg="#ffffff", font=("Arial", 10))
                    tekst_label.pack(side=tk.LEFT, padx=10)

                    status_label = tk.Label(card, text=status_text, fg="white", bg=status_color, font=("Arial", 10, "bold"), padx=10, pady=2)
                    status_label.place(relx=1.0, x=-10, y=10, anchor="ne")

        except Exception as e:
            messagebox.showerror("Fejl", str(e))
    
    def vis_stort_billede(self, pil_image, event=None):
        top = tk.Toplevel(self.master)
        top.title("Forstørret billede")
        top.geometry("600x600")

        resized = pil_image.resize((550, 550))
        tk_img = ImageTk.PhotoImage(resized)

        label = tk.Label(top, image=tk_img)
        label.image = tk_img
        label.pack(padx=10, pady=10)


    def send_feedback(self):
        besked = self.feedback_entry.get("1.0", tk.END).strip()
        if not hasattr(self, "valgt_patient_id"):
            messagebox.showerror("Fejl", "Vælg en patient først.")
            return
        if besked:
            res = requests.post(f"{SERVER_URL}/api/send-feedback", json={
                "besked": besked,
                "patient_id": self.valgt_patient_id
            })
            if res.status_code == 200:
                messagebox.showinfo("OK", "Feedback sendt.")
                self.feedback_entry.delete("1.0", tk.END)
            else:
                messagebox.showerror("Fejl", "Feedback kunne ikke sendes.")

    def send_tidspunkt(self):
        dato = self.dato_entry.get()
        tid = self.tid_entry.get()
        if not hasattr(self, "valgt_patient_id"):
            messagebox.showerror("Fejl", "Vælg en patient først.")
            return

        res = requests.post(f"{SERVER_URL}/api/send-tidspunkt", json={
            "dato": dato,
            "tid": tid,
            "patient_id": self.valgt_patient_id
        })

        if res.status_code == 200:
            messagebox.showinfo("Sendt", "Tidspunkt sendt til patient.")
        else:
            messagebox.showerror("Fejl", "Kunne ikke sende tidspunkt.")

if __name__ == "__main__":
    root = tk.Tk()
    app = LaegeDashboard(root)
    root.mainloop()
