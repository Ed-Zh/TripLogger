# ✈️ TravelLog: Your Digital Passport

> [!NOTE]
> This project was primarily developed through pair-programming with AI, demonstrating the potential of agentic coding workflows.

**TravelLog** is a lightweight, privacy-focused web application designed to maintain a persistent history of international travel. Built with **Streamlit** and **Python**, it acts as a local "NoSQL" document store, keeping your travel data and associated documents (visas, tickets) securely on your own file system.

## 🌟 Key Features

- **📍 Travel History**: A chronological, expandable timeline of your journeys with high-level stats (Total Countries, Total Days).
- **📊 Interactive Analytics**: 
  - **Global Footprint**: A map visualization showing visit counts per country.
  - **Top Destinations**: Automatic "Leaderboard" of your most visited countries, featuring randomly selected photos from your trips.
- **📁 Document Management**: Attach visas, flight tickets, and photos directly to your trip records.
- **🔒 Privacy-First**: All data is stored locally in `trips_data/`. The project is pre-configured to ignore personal travel data for safe GitHub commits.
- **📅 Flexible Dates**: Log trips with specific days or just "Month Only" precision for older memories.
- **🚀 One-Click Launch**: Includes a macOS `.command` script to launch the app directly from your desktop.

## 🛠️ Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Launch the App
```bash
streamlit run app.py
```
*(Alternatively, double-click `Launch_TravelLog.command` on macOS).*

## 📂 Data Structure
The app organizes data into a clean, human-readable directory hierarchy:
```text
trips_data/
└── 2024-07_Tokyo_Japan/
    ├── metadata.json       # Trip details & tags
    ├── visa.pdf            # Attachments
    └── photo.jpg
```

---
*Created with ❤️ for organized travelers.*
