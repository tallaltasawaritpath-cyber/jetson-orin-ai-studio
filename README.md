# ⚡ Jetson Orin Nano AI Studio & Autonomous Agent

A fast, edge-optimized, local AI coding & execution studio powered by an **NVIDIA Jetson Orin Nano** connected over Wi-Fi (`TOPSEVEN_EW`), equipped with **Autonomous Windows Tool Calling** and a **Graft Codebase Knowledge Graph**.

---

## 🚀 Key Features

- **Edge Intelligence on NVIDIA Jetson:**
  - Running `qwen2.5-coder:1.5b` locally on Jetson Ampere GPU.
  - Zero power brownouts, low thermal footprint (~1GB VRAM), and 35+ tok/s response speed.
- **Autonomous Tool Calling & Windows Execution:**
  - Auto-executes shell/PowerShell commands, launches native Windows desktop apps and dialogs (e.g. WPF popups, Python Tkinter GUIs).
  - Non-blocking execution engine keeps desktop windows alive while returning instant process telemetry.
- **🕸️ Graft Knowledge Graph (`@nanonets/graft`):**
  - Full codebase knowledge graph indexing all symbols, call hierarchies, classes, and methods.
  - Integrated with **Model Context Protocol (MCP)** for coding agents (Antigravity, Claude Code, Cursor, Codex).
  - Standalone interactive 3D visual graph (`viz_export/index.html`) that anyone can open in any browser without extra dependencies.

---

## 🕸️ Interactive Knowledge Graph

You can view and explore the interactive codebase graph in two ways:

1. **In the Web Studio:** Click **"🕸️ Code Knowledge Graph"** on the top navigation bar at `http://localhost:5050` (or visit `http://localhost:5050/graph`).
2. **Standalone Browser Graph:** Open `viz_export/index.html` directly in any web browser.
3. **Live Graft Server:** Run `graft viz` in the repository directory to serve the real-time visualizer on port `4400`.

---

## 🛠️ Quick Start

### 1. Launch the Studio
Double-click `Open_Jetson_Browser_Chat.bat` on your Desktop, or run:
```powershell
python server.py
```
Open **`http://localhost:5050`** in your browser.

### 2. Graft CLI Commands
```powershell
# Rebuild the codebase context graph
graft build

# Launch the interactive graph server
graft viz

# Export a standalone visual graph for sharing
graft viz --export ./viz_export

# Query the codebase graph
graft ask "how does the tool execution endpoint work?"
```

---

## 🤖 Supported AI Agents (MCP)
Graft provides automatic MCP and context hooks for:
- **Google Antigravity**
- **Claude Code**
- **Cursor IDE**
- **GitHub Copilot**
- **OpenCode & Codex**

---
*Created by [Tallal Tasawar](https://github.com/tallaltasawaritpath-cyber)*
