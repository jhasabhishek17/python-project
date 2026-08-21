# Notepad Application

A clean, full-featured text editor application built with Python and Tkinter, featuring file operations, custom typography controls, live status statistics, and cross-platform keyboard shortcuts.

![Notepad App UI Preview](assets/preview.jpg)

---

## 📸 How It Looks & Works

1. **Text Editing Canvas**: Features line numbering on left margin, syntax highlighting, and smooth font rendering.
2. **Typography Controls**: Choose font families (Courier New, Consolas, Segoe UI), font sizes, and styles on the fly.
3. **Live Status Bar**: Shows current Line, Column position, word count, character count, and encoding format in real-time.
4. **Shortcut Operations**: Fast keyboard shortcuts for file saving, opening, undo/redo, and inserting timestamps (`F5`).

---

## Features

- **File Operations**: Create New Document, Open text files, Save, Save As, and launch multiple application windows.
- **Editing Tools**: Undo/Redo history, Cut, Copy, Paste, Delete, Select All, and Date/Time insertion (`F5`).
- **Typography & Formatting**: Live Font Selection Dialog (Font Family, Style, Size) with live sample preview, plus Word Wrap toggle.
- **Real-time Status Bar**: Tracks active cursor position (Line, Column), total lines, total words, and character count.
- **Cross-Platform Compatibility**: Fully compatible with macOS, Windows, and Linux.

## Installation

1. Navigate to the project directory:
   ```bash
   cd notepad-app
   ```
2. Run the application (no external dependencies required):
   ```bash
   python main.py
   ```

Or run from the repository root:
```bash
python notepad.py
```

## Keyboard Shortcuts

- `Ctrl+N` / `Cmd+N`: New Document
- `Ctrl+O` / `Cmd+O`: Open File
- `Ctrl+S` / `Cmd+S`: Save File
- `Ctrl+Shift+S` / `Cmd+Shift+S`: Save As
- `F5`: Insert current Date & Time
- `Ctrl+A` / `Cmd+A`: Select All
- `Ctrl+Z` / `Cmd+Z`: Undo
- `Ctrl+Y` / `Cmd+Y`: Redo

## Dependencies

- `tkinter` (Included in Standard Python Library)
