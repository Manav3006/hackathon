# StockFlow

StockFlow is a beginner-friendly Inventory Management System built with Python, Streamlit, and SQLite.

## MVP Features

- Authentication: signup, login, logout, and local demo OTP reset
- Product management: create and update products with SKU, category, unit, reorder level, and optional initial stock
- Unit of measure options: `litres`, `kgs`, `count`
- Inventory operations:
	- Receipts increase stock
	- Deliveries decrease stock
	- Internal transfers move stock between locations
	- Adjustments correct stock using counted quantity and reason
- Move history ledger for all stock-changing actions
- Dashboard KPI cards and top-products stock chart
- Settings for warehouses and locations
- Profile page for current user info and logout

## Project Structure

- app.py: Streamlit app entry point, global UI theme, navigation, auth gate
- db.py: SQLite schema, data helpers, auth logic, stock posting engine
- app_pages/: UI pages (`auth`, `dashboard`, `products`, `operations`, `history`, `settings`, `profile`)
- requirements.txt: Python dependencies

## Run Locally

1. Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

2. Start the app:

```bash
streamlit run app.py
```

3. Open the app on port `8501`.

## Quick Verification Flow

1. Sign up and login.
2. In Settings, confirm at least one warehouse and two locations.
3. In Products, create a product using one of the unit options.
4. Run one receipt, one delivery, one transfer, and one adjustment in Operations.
5. Verify dashboard KPIs and history ledger update accordingly.

## Demo Smoke Test

Use the full pre-demo checklist in [DEMO_SMOKE_TEST.md](DEMO_SMOKE_TEST.md).
