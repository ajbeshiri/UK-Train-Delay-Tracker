# UK Train Delay Tracker
A simple, lightweight Python application built with [FastAPI](https://fastapi.tiangolo.com/) that fetches real-time train delay data using the [TransportAPI](https://www.transportapi.com/) service. Search across 2000 stations over the UK and view the relevant details in an easy-to-read table.
# Features

 - **Station Search**: Search for a station by name or select one from the available station list.
 - **Service information**: Information obtained from TransportAPI is populated into a clear, easy-to-read table and displayed to the user.
 - **Caching**: Information from TransportAPI is cached inside an SQLite3 database for up to 10 minutes, unique to each station.
# Requirements
 - Python.
 - A TransportAPI account with an App ID and App Key.
# Installation & Setup
1. Clone the repository:
```
git clone https://github.com/ajbeshiri/UK-Train-Delay-Tracker.git
cd UK-Train-Delay-Tracker
```
2. Copy **.env.example** to **.env** and add your App ID and App Key. Do not share your **.env** file with anyone.
3. Create and activate a virtual environment:
```
python -m venv .venv
.venv\Scripts\activate
```
4. Install all dependencies: `pip install -r requirements.txt`
5. From the project root directory, run `fastapi run app.py`. Open **http://127.0.0.1:8000** in your browser once the application startup is complete.
# Usage
1. Search for a station by name using the search bar, or scroll until you find the station of your choice.
2. Select the station and press '**Get details**'.
3. View the information in the now populated table.