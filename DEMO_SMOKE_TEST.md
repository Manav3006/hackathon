# StockFlow Demo Smoke Test

Use this short checklist before demos to quickly confirm that core flows still work.

## 1. Authentication

1. Open the app.
2. Create a new user in Authentication.
3. Log in with the new account.

Expected result:
- Login succeeds and Dashboard opens.
- Sidebar navigation shows business pages.

## 2. Warehouse and Locations

1. Open Settings.
2. Ensure one warehouse exists.
3. Ensure at least two locations exist in the same warehouse.

Expected result:
- Warehouse and locations are visible in their lists.

## 3. Product Creation

1. Open Products.
2. Create a product with SKU, category, unit, and reorder level.
3. Use one of the allowed units: litres, kgs, count.

Expected result:
- Product saves successfully.
- Product appears in Product List.

## 4. Operations End-to-End

1. Open Operations.
2. Post a Receipt for the product.
3. Post a Delivery for the same product.
4. Post an Internal Transfer between two locations.
5. Post an Adjustment with a reason.

Expected result:
- Every action returns a success message.
- No operation requires double-submit or page refresh.

## 5. Dashboard and History

1. Open Dashboard.
2. Confirm KPI cards update.
3. Open Move History.
4. Filter by SKU and verify recent operations are listed.

Expected result:
- KPI values reflect latest stock movements.
- History contains Receipt, Delivery, Transfer, and Adjustment records.

## 6. Profile and Logout

1. Open My Profile.
2. Click Logout.

Expected result:
- Session ends and app returns to Authentication page.
