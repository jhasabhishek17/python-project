import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import requests
import re
import threading

try:
    import instaloader
    INSTALOADER_AVAILABLE = True
except ImportError:
    INSTALOADER_AVAILABLE = False


class InstagramUserDetailsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Instagram User Details")
        self.root.geometry("520x620")
        self.root.resizable(False, False)
        self.root.configure(bg="#0f172a")

        self.current_profile_pic = None

        self.setup_ui()

    def setup_ui(self):
        # Header Banner
        header = tk.Frame(self.root, bg="#1e293b", height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        title_label = tk.Label(
            header,
            text="Instagram User Fetcher",
            font=("Segoe UI", 18, "bold"),
            fg="#f8fafc",
            bg="#1e293b"
        )
        title_label.pack(pady=12)

        subtitle_label = tk.Label(
            header,
            text="Lookup profile statistics & details instantly",
            font=("Segoe UI", 10),
            fg="#94a3b8",
            bg="#1e293b"
        )
        subtitle_label.pack()

        # Search Bar Area
        search_frame = tk.Frame(self.root, bg="#0f172a", pady=15)
        search_frame.pack(fill=tk.X, padx=20)

        tk.Label(
            search_frame,
            text="Username:",
            font=("Segoe UI", 11, "bold"),
            fg="#e2e8f0",
            bg="#0f172a"
        ).pack(side=tk.LEFT, padx=(0, 8))

        self.user_entry = tk.Entry(
            search_frame,
            font=("Segoe UI", 11),
            bg="#1e293b",
            fg="#ffffff",
            insertbackground="#ffffff",
            relief=tk.FLAT,
            bd=5
        )
        self.user_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 10))
        self.user_entry.bind("<Return>", lambda event: self.start_search())

        self.search_btn = tk.Button(
            search_frame,
            text="Search",
            font=("Segoe UI", 10, "bold"),
            bg="#2563eb",
            fg="#ffffff",
            activebackground="#1d4ed8",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=15,
            pady=4,
            cursor="hand2",
            command=self.start_search
        )
        self.search_btn.pack(side=tk.RIGHT)

        # Status indicator
        self.status_label = tk.Label(
            self.root,
            text="Enter an Instagram username and click Search.",
            font=("Segoe UI", 9, "italic"),
            fg="#94a3b8",
            bg="#0f172a"
        )
        self.status_label.pack(pady=(0, 10))

        # Details Card Container
        card = tk.Frame(self.root, bg="#1e293b", bd=1, relief=tk.SOLID)
        card.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        # Details Text Output Box
        self.details_text = tk.Text(
            card,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg="#0f172a",
            fg="#38bdf8",
            insertbackground="#ffffff",
            relief=tk.FLAT,
            padx=12,
            pady=12,
            state=tk.DISABLED
        )
        self.details_text.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Action Buttons Frame
        action_frame = tk.Frame(card, bg="#1e293b")
        action_frame.pack(fill=tk.X, padx=15, pady=(0, 15))

        self.pic_btn = tk.Button(
            action_frame,
            text="🖼 View Profile Picture",
            font=("Segoe UI", 10, "bold"),
            bg="#059669",
            fg="#ffffff",
            activebackground="#047857",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=12,
            pady=6,
            state=tk.DISABLED,
            cursor="hand2",
            command=self.open_profile_pic
        )
        self.pic_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.open_web_btn = tk.Button(
            action_frame,
            text="🌐 Open Profile in Browser",
            font=("Segoe UI", 10, "bold"),
            bg="#4f46e5",
            fg="#ffffff",
            activebackground="#4338ca",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=12,
            pady=6,
            state=tk.DISABLED,
            cursor="hand2",
            command=self.open_profile_web
        )
        self.open_web_btn.pack(side=tk.LEFT)

    def start_search(self):
        username = self.user_entry.get().strip()
        if not username:
            messagebox.showwarning("Warning", "Please enter a valid Instagram username.")
            return

        self.search_btn.config(state=tk.DISABLED, text="Fetching...")
        self.status_label.config(text=f"Fetching details for @{username}...", fg="#38bdf8")
        self.pic_btn.config(state=tk.DISABLED)
        self.open_web_btn.config(state=tk.DISABLED)

        # Run fetch in background thread so UI doesn't freeze
        threading.Thread(target=self.fetch_details, args=(username,), daemon=True).start()

    def fetch_details(self, username):
        data = None
        error_msg = None

        if INSTALOADER_AVAILABLE:
            try:
                L = instaloader.Instaloader()
                profile = instaloader.Profile.from_username(L.context, username)
                data = {
                    "username": profile.username,
                    "full_name": profile.full_name,
                    "followers": f"{profile.followers:,}",
                    "following": f"{profile.followees:,}",
                    "posts": f"{profile.mediacount:,}",
                    "bio": profile.biography or "N/A",
                    "bio_url": profile.external_url or "N/A",
                    "is_private": "Yes" if profile.is_private else "No",
                    "is_verified": "Yes" if profile.is_verified else "No",
                    "is_business": "Yes" if profile.is_business_account else "No",
                    "category": profile.business_category_name or "N/A",
                    "profile_pic_url": profile.profile_pic_url
                }
            except Exception as e:
                error_msg = str(e)

        if not data:
            # Fallback web metadata extraction
            try:
                url = f"https://www.instagram.com/{username}/"
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                resp = requests.get(url, headers=headers, timeout=5)
                if resp.status_code == 200:
                    meta_desc = re.search(r'<meta property="og:description" content="([^"]+)"', resp.text)
                    meta_title = re.search(r'<meta property="og:title" content="([^"]+)"', resp.text)
                    meta_image = re.search(r'<meta property="og:image" content="([^"]+)"', resp.text)

                    desc_text = meta_desc.group(1) if meta_desc else ""
                    # e.g., "10M Followers, 500 Following, 1,200 Posts - ..."
                    followers = re.search(r'([\d\.\,KkMm]+)\s+Followers', desc_text)
                    following = re.search(r'([\d\.\,KkMm]+)\s+Following', desc_text)
                    posts = re.search(r'([\d\.\,KkMm]+)\s+Posts', desc_text)

                    data = {
                        "username": username,
                        "full_name": meta_title.group(1).split("(")[0].strip() if meta_title else username,
                        "followers": followers.group(1) if followers else "N/A",
                        "following": following.group(1) if following else "N/A",
                        "posts": posts.group(1) if posts else "N/A",
                        "bio": "N/A (Web preview mode)",
                        "bio_url": "N/A",
                        "is_private": "Unknown",
                        "is_verified": "Unknown",
                        "is_business": "Unknown",
                        "category": "N/A",
                        "profile_pic_url": meta_image.group(1) if meta_image else ""
                    }
            except Exception as err:
                error_msg = f"Failed to fetch user. {err}"

        self.root.after(0, self.display_result, data, error_msg, username)

    def display_result(self, data, error_msg, username):
        self.search_btn.config(state=tk.NORMAL, text="Search")

        self.details_text.config(state=tk.NORMAL)
        self.details_text.delete("1.0", tk.END)

        if data:
            self.current_profile_pic = data.get("profile_pic_url")
            self.current_username = username

            info_str = (
                f"👤 Username       : {data['username']}\n"
                f"🏷 Full Name       : {data['full_name']}\n"
                f"--------------------------------------------------\n"
                f"📊 Followers       : {data['followers']}\n"
                f"👥 Following       : {data['following']}\n"
                f"📸 Total Posts     : {data['posts']}\n"
                f"--------------------------------------------------\n"
                f"🔒 Private Account : {data['is_private']}\n"
                f"✔ Verified        : {data['is_verified']}\n"
                f"💼 Business        : {data['is_business']} ({data['category']})\n"
                f"🔗 Bio Link        : {data['bio_url']}\n"
                f"--------------------------------------------------\n"
                f"📝 Bio:\n{data['bio']}\n"
            )
            self.details_text.insert(tk.END, info_str)
            self.status_label.config(text=f"Details loaded for @{username}", fg="#10b981")
            
            if self.current_profile_pic:
                self.pic_btn.config(state=tk.NORMAL)
            self.open_web_btn.config(state=tk.NORMAL)
        else:
            err_text = f"Could not retrieve details for '@{username}'.\n\nReason: {error_msg or 'Profile not found or Instagram blocked request.'}"
            self.details_text.insert(tk.END, err_text)
            self.status_label.config(text="Error fetching user details", fg="#ef4444")

        self.details_text.config(state=tk.DISABLED)

    def open_profile_pic(self):
        if self.current_profile_pic:
            webbrowser.open(self.current_profile_pic)

    def open_profile_web(self):
        if hasattr(self, 'current_username') and self.current_username:
            webbrowser.open(f"https://www.instagram.com/{self.current_username}/")


def main():
    root = tk.Tk()
    app = InstagramUserDetailsApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
