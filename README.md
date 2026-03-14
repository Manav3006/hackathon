# CoreInventory Starter

This repository now contains the first project files for your hackathon Inventory Management System.

## Current Structure

- app.py: Streamlit entry point and sidebar navigation shell
- db.py: SQLite database path, schema creation, and starter reference data
- app_pages/: page modules for auth, dashboard, products, operations, history, settings, and profile
- requirements.txt: Python packages needed to run the app

## What Works Right Now

- The app starts with Streamlit.
- The SQLite database file is created automatically on first run.
- The database schema skeleton is created automatically on startup.
- Authentication now works (signup, login, local demo OTP reset, logout).
- Business pages (dashboard/products/operations/history/settings) are scaffolded and ready to be connected to real CRUD queries.

## How To Run

1. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

2. Start the app:

```bash
streamlit run app.py
```

3. Open the Streamlit preview on port 8501.

## What Comes Next

The next coding step is to connect the Authentication page to the users table and then build real product create/list actions.