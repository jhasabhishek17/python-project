import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
import names


class NameGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Random Name Generator")
        self.root.geometry("480x520")
        self.root.resizable(False, False)
        self.root.configure(bg="#0f172a")

        self.setup_ui()

    def setup_ui(self):
        # Header Banner
        header = tk.Frame(self.root, bg="#1e293b", height=70)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        title = tk.Label(
            header,
            text="Random Name Generator",
            font=("Segoe UI", 16, "bold"),
            fg="#f8fafc",
            bg="#1e293b"
        )
        title.pack(pady=10)

        subtitle = tk.Label(
            header,
            text="Generate realistic first names, last names, and full names",
            font=("Segoe UI", 9),
            fg="#94a3b8",
            bg="#1e293b"
        )
        subtitle.pack()

        # Input Controls Card
        control_card = tk.Frame(self.root, bg="#1e293b", padx=15, pady=15, bd=1, relief=tk.SOLID)
        control_card.pack(fill=tk.X, padx=20, pady=15)

        # Gender Selection
        tk.Label(
            control_card,
            text="Gender:",
            font=("Segoe UI", 10, "bold"),
            fg="#e2e8f0",
            bg="#1e293b"
        ).grid(row=0, column=0, sticky=tk.W, pady=5)

        self.gender_var = tk.StringVar(value="Male")
        gender_cb = ttk.Combobox(
            control_card,
            textvariable=self.gender_var,
            values=["Male", "Female", "Random"],
            state="readonly",
            width=12,
            font=("Segoe UI", 10)
        )
        gender_cb.grid(row=0, column=1, padx=(5, 20), pady=5)

        # Type Selection
        tk.Label(
            control_card,
            text="Type:",
            font=("Segoe UI", 10, "bold"),
            fg="#e2e8f0",
            bg="#1e293b"
        ).grid(row=0, column=2, sticky=tk.W, pady=5)

        self.type_var = tk.StringVar(value="Full Name")
        type_cb = ttk.Combobox(
            control_card,
            textvariable=self.type_var,
            values=["Full Name", "First Name", "Last Name"],
            state="readonly",
            width=12,
            font=("Segoe UI", 10)
        )
        type_cb.grid(row=0, column=3, padx=(5, 0), pady=5)

        # Quantity Selector
        tk.Label(
            control_card,
            text="Count:",
            font=("Segoe UI", 10, "bold"),
            fg="#e2e8f0",
            bg="#1e293b"
        ).grid(row=1, column=0, sticky=tk.W, pady=10)

        self.count_var = tk.IntVar(value=1)
        count_spin = ttk.Spinbox(
            control_card,
            from_=1,
            to=50,
            textvariable=self.count_var,
            width=12,
            font=("Segoe UI", 10)
        )
        count_spin.grid(row=1, column=1, padx=(5, 20), pady=10)

        # Generate Button
        gen_btn = tk.Button(
            control_card,
            text="⚡ Generate Names",
            font=("Segoe UI", 10, "bold"),
            bg="#2563eb",
            fg="#ffffff",
            activebackground="#1d4ed8",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=12,
            pady=4,
            cursor="hand2",
            command=self.generate_names
        )
        gen_btn.grid(row=1, column=2, columnspan=2, sticky=tk.E, pady=10)

        # Output Card Container
        output_card = tk.Frame(self.root, bg="#1e293b", padx=15, pady=15, bd=1, relief=tk.SOLID)
        output_card.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        tk.Label(
            output_card,
            text="Generated Output:",
            font=("Segoe UI", 10, "bold"),
            fg="#e2e8f0",
            bg="#1e293b"
        ).pack(anchor=tk.W, pady=(0, 5))

        self.text_area = ScrolledText(
            output_card,
            font=("Consolas", 11),
            bg="#0f172a",
            fg="#38bdf8",
            insertbackground="#ffffff",
            relief=tk.FLAT,
            wrap=tk.WORD
        )
        self.text_area.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Bottom Button Bar
        btn_bar = tk.Frame(output_card, bg="#1e293b")
        btn_bar.pack(fill=tk.X)

        copy_btn = tk.Button(
            btn_bar,
            text="📋 Copy All to Clipboard",
            font=("Segoe UI", 9, "bold"),
            bg="#059669",
            fg="#ffffff",
            activebackground="#047857",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=10,
            pady=5,
            cursor="hand2",
            command=self.copy_to_clipboard
        )
        copy_btn.pack(side=tk.LEFT)

        clear_btn = tk.Button(
            btn_bar,
            text="🗑 Clear Output",
            font=("Segoe UI", 9, "bold"),
            bg="#dc2626",
            fg="#ffffff",
            activebackground="#b91c1c",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=10,
            pady=5,
            cursor="hand2",
            command=self.clear_output
        )
        clear_btn.pack(side=tk.RIGHT)

    def generate_names(self):
        gender = self.gender_var.get().lower()
        name_type = self.type_var.get()
        
        try:
            count = int(self.count_var.get())
            if count < 1:
                count = 1
        except ValueError:
            count = 1

        generated = []
        for _ in range(count):
            g_param = None if gender == "random" else gender

            if name_type == "Full Name":
                name = names.get_full_name(gender=g_param)
            elif name_type == "First Name":
                name = names.get_first_name(gender=g_param)
            elif name_type == "Last Name":
                name = names.get_last_name()
            else:
                name = names.get_full_name()
            generated.append(name)

        output_str = "\n".join(generated) + "\n"
        self.text_area.insert(tk.END, output_str)
        self.text_area.see(tk.END)

    def copy_to_clipboard(self):
        content = self.text_area.get("1.0", tk.END).strip()
        if content:
            self.root.clipboard_clear()
            self.root.clipboard_append(content)
            messagebox.showinfo("Success", "Generated names copied to clipboard!")
        else:
            messagebox.showwarning("Warning", "No content to copy.")

    def clear_output(self):
        self.text_area.delete("1.0", tk.END)


def main():
    root = tk.Tk()
    app = NameGeneratorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
