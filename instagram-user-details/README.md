# Instagram User Details App

A modern Desktop Application built with Python and Tkinter for fetching and displaying public Instagram profile statistics and details in real-time.

![Instagram User Fetcher UI Preview](assets/preview.jpg)

---

## 📸 How It Looks & Works

1. **Enter Username**: Type any public handle (e.g. `@alexrivera_`) into the search bar.
2. **Fetch Data**: Click **Fetch Details** (or press Enter) to query metrics asynchronously without freezing the app window.
3. **Inspect Profile Card**:
   - High-resolution circular profile picture / avatar.
   - Verification badge indicator icon.
   - Post Count, Follower Count, and Following Count stat boxes.
   - Quick action buttons to view full-resolution avatar or open full profile on Instagram.

---

## Features

- **Profile Stats**: Retrieve follower count, following count, and post count.
- **Account Metadata**: View full name, bio, external bio URL, verification status, private status, and business account details.
- **Profile Picture Viewer**: Direct button link to open full-resolution profile picture in your browser.
- **Asynchronous GUI**: Non-blocking search with multi-threading so the application stays responsive.
- **Modern Dark UI**: Polished interface with color indicators and clean text typography.

## Installation

1. Navigate to this directory:
   ```bash
   cd instagram-user-details
   ```
2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the main application:
```bash
python main.py
```
Or run from root directory:
```bash
python instauserdetails.py
```

1. Type any public Instagram username into the search bar (e.g. `instagram` or `nasa`).
2. Click **Search** (or press `Enter`).
3. View the detailed profile statistics, bio, and click **View Profile Picture** to inspect the avatar image.

## Dependencies

- `instaloader`
- `requests`
- `pillow`
- `tkinter` (Standard Python Library)
