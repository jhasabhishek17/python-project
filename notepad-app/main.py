import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font
from tkinter.scrolledtext import ScrolledText
from datetime import datetime
import webbrowser


class NotepadApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Notepad - Untitled")
        self.root.geometry("800x550")
        self.root.minsize(400, 300)

        # File state tracking
        self.current_filepath = None
        self.word_wrap_var = tk.BooleanVar(value=True)

        # Current font settings
        self.current_font_family = "Courier New"
        self.current_font_size = 11
        self.current_font_style = "normal"

        self.try_set_icon()
        self.setup_ui()
        self.setup_events()

    def try_set_icon(self):
        try:
            if os.path.exists("notepad.ico"):
                self.root.iconbitmap("notepad.ico")
        except Exception:
            pass  # Ignore icon load errors on systems where iconbitmap isn't supported

    def setup_ui(self):
        # Menu Bar
        self.menubar = tk.Menu(self.root)

        # File Menu
        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        self.file_menu.add_command(label="New", accelerator="Ctrl+N", command=self.new_file)
        self.file_menu.add_command(label="New Window", command=self.new_window)
        self.file_menu.add_command(label="Open...", accelerator="Ctrl+O", command=self.open_file)
        self.file_menu.add_command(label="Save", accelerator="Ctrl+S", command=self.save_file)
        self.file_menu.add_command(label="Save As...", accelerator="Ctrl+Shift+S", command=self.save_file_as)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.exit_app)
        self.menubar.add_cascade(label="File", menu=self.file_menu)

        # Edit Menu
        self.edit_menu = tk.Menu(self.menubar, tearoff=0)
        self.edit_menu.add_command(label="Undo", accelerator="Ctrl+Z", command=self.undo_action)
        self.edit_menu.add_command(label="Redo", accelerator="Ctrl+Y", command=self.redo_action)
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Cut", accelerator="Ctrl+X", command=self.cut_text)
        self.edit_menu.add_command(label="Copy", accelerator="Ctrl+C", command=self.copy_text)
        self.edit_menu.add_command(label="Paste", accelerator="Ctrl+V", command=self.paste_text)
        self.edit_menu.add_command(label="Delete", accelerator="Del", command=self.delete_text)
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Select All", accelerator="Ctrl+A", command=self.select_all)
        self.edit_menu.add_command(label="Time/Date", accelerator="F5", command=self.insert_datetime)
        self.menubar.add_cascade(label="Edit", menu=self.edit_menu)

        # Format Menu
        self.format_menu = tk.Menu(self.menubar, tearoff=0)
        self.format_menu.add_checkbutton(
            label="Word Wrap",
            variable=self.word_wrap_var,
            command=self.toggle_word_wrap
        )
        self.format_menu.add_command(label="Font...", command=self.open_font_dialog)
        self.menubar.add_cascade(label="Format", menu=self.format_menu)

        # Help Menu
        self.help_menu = tk.Menu(self.menubar, tearoff=0)
        self.help_menu.add_command(label="View Help", command=self.view_help)
        self.help_menu.add_command(label="Send Feedback", command=self.send_feedback)
        self.help_menu.add_separator()
        self.help_menu.add_command(label="About Notepad", command=self.about_dialog)
        self.menubar.add_cascade(label="Help", menu=self.help_menu)

        self.root.config(menu=self.menubar)

        # Status Bar
        self.status_bar = tk.Label(
            self.root,
            text=" Lines: 1 | Words: 0 | Chars: 0 ",
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.E,
            font=("Segoe UI", 9),
            bg="#f1f5f9",
            fg="#475569"
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Main Text Widget
        self.text_area = ScrolledText(
            self.root,
            undo=True,
            wrap=tk.WORD if self.word_wrap_var.get() else tk.NONE,
            font=(self.current_font_family, self.current_font_size, self.current_font_style)
        )
        self.text_area.pack(fill=tk.BOTH, expand=True)

        # Context Menu (Right Click)
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Undo", command=self.undo_action)
        self.context_menu.add_command(label="Redo", command=self.redo_action)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Cut", command=self.cut_text)
        self.context_menu.add_command(label="Copy", command=self.copy_text)
        self.context_menu.add_command(label="Paste", command=self.paste_text)
        self.context_menu.add_command(label="Delete", command=self.delete_text)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Select All", command=self.select_all)

    def setup_events(self):
        # Keyboard shortcuts
        self.root.bind("<Control-n>", lambda event: self.new_file())
        self.root.bind("<Control-o>", lambda event: self.open_file())
        self.root.bind("<Control-s>", lambda event: self.save_file())
        self.root.bind("<Control-S>", lambda event: self.save_file_as())
        self.root.bind("<F5>", lambda event: self.insert_datetime())
        
        # On macOS, support Command key bindings as well
        self.root.bind("<Command-n>", lambda event: self.new_file())
        self.root.bind("<Command-o>", lambda event: self.open_file())
        self.root.bind("<Command-s>", lambda event: self.save_file())
        self.root.bind("<Command-S>", lambda event: self.save_file_as())

        # Update status bar on typing or click
        self.text_area.bind("<KeyRelease>", self.update_status_bar)
        self.text_area.bind("<ButtonRelease-1>", self.update_status_bar)

        # Context menu binding
        self.root.bind("<Button-3>", self.show_context_menu)
        # On macOS touchpad right click:
        self.root.bind("<Button-2>", self.show_context_menu)

        # Window closing protocol
        self.root.protocol("WM_DELETE_WINDOW", self.exit_app)

    def update_status_bar(self, event=None):
        content = self.text_area.get("1.0", tk.END)
        lines = int(self.text_area.index("end-1c").split(".")[0])
        chars = len(content) - 1
        words = len(content.split())
        
        cursor_index = self.text_area.index(tk.INSERT)
        curr_line, curr_col = cursor_index.split(".")

        status_text = f" Line {curr_line}, Col {curr_col} | Total Lines: {lines} | Words: {words} | Chars: {chars} "
        self.status_bar.config(text=status_text)

    def show_context_menu(self, event):
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    # --- File Operations ---

    def new_file(self):
        self.text_area.delete("1.0", tk.END)
        self.current_filepath = None
        self.root.title("Notepad - Untitled")
        self.update_status_bar()

    def new_window(self):
        new_root = tk.Tk()
        NotepadApp(new_root)
        new_root.mainloop()

    def open_file(self):
        filepath = filedialog.askopenfilename(
            title="Open File",
            filetypes=[("Text Documents (*.txt)", "*.txt"), ("All Files (*.*)", "*.*")]
        )
        if filepath:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                self.text_area.delete("1.0", tk.END)
                self.text_area.insert("1.0", content)
                self.current_filepath = filepath
                self.root.title(f"Notepad - {os.path.basename(filepath)}")
                self.update_status_bar()
            except Exception as e:
                messagebox.showerror("Error", f"Could not open file:\n{e}")

    def save_file(self):
        if self.current_filepath:
            try:
                content = self.text_area.get("1.0", "end-1c")
                with open(self.current_filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                self.root.title(f"Notepad - {os.path.basename(self.current_filepath)}")
                messagebox.showinfo("Saved", "File saved successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Could not save file:\n{e}")
        else:
            self.save_file_as()

    def save_file_as(self):
        filepath = filedialog.asksaveasfilename(
            title="Save As",
            defaultextension=".txt",
            filetypes=[("Text Documents (*.txt)", "*.txt"), ("All Files (*.*)", "*.*")]
        )
        if filepath:
            try:
                content = self.text_area.get("1.0", "end-1c")
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                self.current_filepath = filepath
                self.root.title(f"Notepad - {os.path.basename(filepath)}")
                messagebox.showinfo("Saved", "File saved successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Could not save file:\n{e}")

    def exit_app(self):
        content = self.text_area.get("1.0", "end-1c")
        if content.strip():
            res = messagebox.askyesnocancel("Exit", "Do you want to save changes before exiting?")
            if res is True:
                self.save_file()
                self.root.destroy()
            elif res is False:
                self.root.destroy()
        else:
            self.root.destroy()

    # --- Edit Actions ---

    def undo_action(self):
        try:
            self.text_area.edit_undo()
        except tk.TclError:
            pass

    def redo_action(self):
        try:
            self.text_area.edit_redo()
        except tk.TclError:
            pass

    def cut_text(self):
        self.text_area.event_generate("<<Cut>>")

    def copy_text(self):
        self.text_area.event_generate("<<Copy>>")

    def paste_text(self):
        self.text_area.event_generate("<<Paste>>")

    def delete_text(self):
        try:
            self.text_area.delete(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            pass

    def select_all(self):
        self.text_area.tag_add(tk.SEL, "1.0", tk.END)
        self.text_area.mark_set(tk.INSERT, "1.0")
        self.text_area.see(tk.INSERT)
        return "break"

    def insert_datetime(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.text_area.insert(tk.INSERT, now)
        self.update_status_bar()

    # --- Format Actions ---

    def toggle_word_wrap(self):
        wrap_mode = tk.WORD if self.word_wrap_var.get() else tk.NONE
        self.text_area.config(wrap=wrap_mode)

    def open_font_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Font Selection")
        dialog.geometry("420x350")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text="Font:").place(x=15, y=15)
        font_var = tk.StringVar(value=self.current_font_family)
        font_cb = ttk.Combobox(
            dialog,
            textvariable=font_var,
            values=sorted(list(font.families())),
            state="readonly",
            width=20
        )
        font_cb.place(x=15, y=35)

        tk.Label(dialog, text="Style:").place(x=185, y=15)
        style_var = tk.StringVar(value="Normal")
        style_cb = ttk.Combobox(
            dialog,
            textvariable=style_var,
            values=["Normal", "Bold", "Italic", "Bold Italic"],
            state="readonly",
            width=12
        )
        style_cb.place(x=185, y=35)

        tk.Label(dialog, text="Size:").place(x=315, y=15)
        size_var = tk.IntVar(value=self.current_font_size)
        size_cb = ttk.Combobox(
            dialog,
            textvariable=size_var,
            values=[8, 9, 10, 11, 12, 14, 16, 18, 20, 24, 28, 36, 48, 72],
            state="readonly",
            width=6
        )
        size_cb.place(x=315, y=35)

        # Preview Frame
        preview_frame = tk.LabelFrame(dialog, text="Sample Preview", width=385, height=140)
        preview_frame.place(x=15, y=85)
        preview_frame.pack_propagate(False)

        preview_label = tk.Label(
            preview_frame,
            text="AaBbYyZz 123",
            font=(font_var.get(), size_var.get(), "normal")
        )
        preview_label.pack(expand=True)

        def update_preview(*args):
            s_val = style_var.get().lower()
            if s_val == "normal":
                s_str = "normal"
            elif s_val == "bold":
                s_str = "bold"
            elif s_val == "italic":
                s_str = "italic"
            else:
                s_str = "bold italic"

            try:
                preview_label.config(font=(font_var.get(), size_var.get(), s_str))
            except Exception:
                pass

        font_cb.bind("<<ComboboxSelected>>", update_preview)
        style_cb.bind("<<ComboboxSelected>>", update_preview)
        size_cb.bind("<<ComboboxSelected>>", update_preview)

        def apply_font():
            self.current_font_family = font_var.get()
            self.current_font_size = size_var.get()
            s_val = style_var.get().lower()
            if s_val == "normal":
                self.current_font_style = "normal"
            elif s_val == "bold":
                self.current_font_style = "bold"
            elif s_val == "italic":
                self.current_font_style = "italic"
            else:
                self.current_font_style = "bold italic"

            self.text_area.config(
                font=(self.current_font_family, self.current_font_size, self.current_font_style)
            )
            dialog.destroy()

        btn_ok = tk.Button(dialog, text="OK", width=10, command=apply_font)
        btn_ok.place(x=200, y=295)

        btn_cancel = tk.Button(dialog, text="Cancel", width=10, command=dialog.destroy)
        btn_cancel.place(x=300, y=295)

    # --- Help & About ---

    def view_help(self):
        messagebox.showinfo("Help", "Notepad Shortcuts:\n- Ctrl+N : New File\n- Ctrl+O : Open File\n- Ctrl+S : Save\n- F5 : Insert Date & Time")

    def send_feedback(self):
        webbrowser.open("https://github.com/jhasabhishek17/python-project/issues")

    def about_dialog(self):
        messagebox.showinfo("About Notepad", "Standard Desktop Notepad Application\nBuilt with Python & Tkinter\nVersion 2.0")


def main():
    root = tk.Tk()
    app = NotepadApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
