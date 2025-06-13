import tkinter as tk
from tkinter import ttk, messagebox
import requests
import io
from PIL import Image, ImageTk

SERVER_URL = "http://localhost:60070"

class LaegeDashboard:
    def __init__(self, master):
        self.master = master
        self.master.title("Læge Dashboard – Fjernmonitorering")
        self.master.geometry("900x700")

        tk.Label(master, text="🩺 Lægedashboard", font=("Arial", 16, "bold")).pack(pady=10)

        # Konsultationsvisning
        self.konsultation_box = tk.Text(master, height=15, width=100)
        self.konsultation_box.pack()
        tk.Button(master, text="🔄 Opdater konsultationer", command=self.hent_konsultationer).pack(pady=5)

        # Feedback
        tk.Label(master, text="📝 Feedback til patient:").pack(pady=(10, 0))
        self.feedback_entry = tk.Text(master, height=4, width=100)
        self.feedback_entry.pack()
        tk.Button(master, text="📤 Send feedback", command=self.send_feedback).pack(pady=5)

        # Tidspunktvalg
        tk.Label(master, text="📅 Foreslå nyt konsultationstidspunkt:").pack()
        self.dato_entry = ttk.Entry(master)
        self.dato_entry.insert(0, "2025-06-15")
        self.dato_entry.pack()
        self.tid_entry = ttk.Entry(master)
        self.tid_entry.insert(0, "10:00")
        self.tid_entry.pack()
        tk.Button(master, text="📆 Send tidspunkt", command=self.send_tidspunkt).pack(pady=5)

        # Billedevisning
        tk.Label(master, text="🖼 Seneste billede fra patient:").pack(pady=(10, 0))
        self.billede_label = tk.Label(master)
        self.billede_label.pack()

        self.hent_konsultationer()

    def hent_konsultationer(self):
        try:
            res = requests.get(f"{SERVER_URL}/api/konsultationer")
            if res.status_code == 200:
                data = res.json()
                self.konsultation_box.delete("1.0", tk.END)
                if data:
                    for k in data:
                        self.konsultation_box.insert(tk.END, f"ID: {k['id']} | Symptomer: {k['symptomer']}\nTidspunkt: {k['oprettet_tidspunkt']}\n---\n")
                    billede_url = data[0].get("billede_url")
                    if billede_url:
                        img_res = requests.get(billede_url)
                        if img_res.status_code == 200:
                            img = Image.open(io.BytesIO(img_res.content))
                            img = img.resize((200, 200))
                            tk_img = ImageTk.PhotoImage(img)
                            self.billede_label.configure(image=tk_img)
                            self.billede_label.image = tk_img
                else:
                    self.konsultation_box.insert(tk.END, "Ingen data.")
        except Exception as e:
            messagebox.showerror("Fejl", str(e))

    def send_feedback(self):
        besked = self.feedback_entry.get("1.0", tk.END).strip()
        if besked:
            res = requests.post(f"{SERVER_URL}/api/send-feedback", json={"besked": besked})
            if res.status_code == 200:
                messagebox.showinfo("OK", "Feedback sendt.")
                self.feedback_entry.delete("1.0", tk.END)
            else:
                messagebox.showerror("Fejl", "Feedback kunne ikke sendes.")

    def send_tidspunkt(self):
        dato = self.dato_entry.get()
        tid = self.tid_entry.get()
        res = requests.post(f"{SERVER_URL}/api/send-tidspunkt", json={"dato": dato, "tid": tid})
        if res.status_code == 200:
            messagebox.showinfo("Sendt", "Tidspunkt sendt.")
        else:
            messagebox.showerror("Fejl", "Kunne ikke sende tidspunkt.")

if __name__ == "__main__":
    root = tk.Tk()
    app = LaegeDashboard(root)
    root.mainloop()
