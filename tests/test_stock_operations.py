from __future__ import annotations

from uuid import uuid4

import db
import pytest


@pytest.fixture()
def isolated_db(monkeypatch: pytest.MonkeyPatch, tmp_path):
    db_path = tmp_path / "test_inventory.db"
    monkeypatch.setattr(db, "DATABASE_PATH", db_path)
    db.init_db()
    return db_path


def _seed_user_and_product() -> tuple[int, int, int, int, str]:
    email = f"user_{uuid4().hex[:8]}@example.com"
    success, _ = db.create_user(
        "Test User", email, "secret123", "Inventory Manager")
    assert success

    user = db.authenticate_user(email, "secret123")
    assert user is not None

    sku = f"SKU-{uuid4().hex[:8].upper()}"
    success, _ = db.create_product(
        name="Test Product",
        sku=sku,
        category_id=None,
        unit_of_measure="count",
        reorder_level=2,
        initial_stock=0,
        initial_location_id=None,
    )
    assert success

    product = db.list_products(search_query=sku)[0]
    locations = db.list_locations()
    return user["id"], product["id"], locations[0]["id"], locations[1]["id"], sku


def test_create_product_rejects_invalid_unit(isolated_db) -> None:
    success, message = db.create_product(
        name="Invalid Unit Product",
        sku=f"BAD-{uuid4().hex[:6].upper()}",
        category_id=None,
        unit_of_measure="boxes",
        reorder_level=0,
        initial_stock=0,
        initial_location_id=None,
    )

    assert not success
    assert "Unit must be one of" in message


def test_receipt_increases_stock_and_creates_ledger_entry(isolated_db) -> None:
    user_id, product_id, source_location_id, _, sku = _seed_user_and_product()

    success, _ = db.post_receipt(
        product_id=product_id,
        destination_location_id=source_location_id,
        quantity=12,
        partner_name="Supplier",
        notes="",
        created_by_user_id=user_id,
    )

    assert success
    assert db.get_current_stock(product_id, source_location_id) == 12.0

    rows = db.list_ledger(search_sku=sku)
    assert len(rows) == 1
    assert rows[0]["operation"] == "Receipt"
    assert float(rows[0]["qty_change"]) == 12.0


def test_delivery_blocks_when_stock_is_insufficient(isolated_db) -> None:
    user_id, product_id, source_location_id, _, _ = _seed_user_and_product()

    db.post_receipt(
        product_id=product_id,
        destination_location_id=source_location_id,
        quantity=3,
        partner_name="Supplier",
        notes="",
        created_by_user_id=user_id,
    )

    success, message = db.post_delivery(
        product_id=product_id,
        source_location_id=source_location_id,
        quantity=5,
        partner_name="Customer",
        notes="",
        created_by_user_id=user_id,
    )

    assert not success
    assert "Not enough stock" in message
    assert db.get_current_stock(product_id, source_location_id) == 3.0


def test_transfer_moves_stock_without_changing_total(isolated_db) -> None:
    user_id, product_id, source_location_id, destination_location_id, sku = _seed_user_and_product()

    db.post_receipt(
        product_id=product_id,
        destination_location_id=source_location_id,
        quantity=10,
        partner_name="Supplier",
        notes="",
        created_by_user_id=user_id,
    )

    success, _ = db.post_transfer(
        product_id=product_id,
        source_location_id=source_location_id,
        destination_location_id=destination_location_id,
        quantity=4,
        notes="",
        created_by_user_id=user_id,
    )

    assert success
    source_stock = db.get_current_stock(product_id, source_location_id)
    destination_stock = db.get_current_stock(
        product_id, destination_location_id)
    assert source_stock == 6.0
    assert destination_stock == 4.0
    assert source_stock + destination_stock == 10.0

    transfer_entries = [
        row
        for row in db.list_ledger(search_sku=sku)
        if row["operation"] == "Internal Transfer"
    ]
    assert len(transfer_entries) == 2


def test_adjustment_requires_reason_and_sets_counted_quantity(isolated_db) -> None:
    user_id, product_id, source_location_id, _, _ = _seed_user_and_product()

    db.post_receipt(
        product_id=product_id,
        destination_location_id=source_location_id,
        quantity=9,
        partner_name="Supplier",
        notes="",
        created_by_user_id=user_id,
    )

    success, message = db.post_adjustment(
        product_id=product_id,
        location_id=source_location_id,
        counted_quantity=7,
        reason="   ",
        created_by_user_id=user_id,
    )
    assert not success
    assert "reason" in message.lower()

    success, _ = db.post_adjustment(
        product_id=product_id,
        location_id=source_location_id,
        counted_quantity=7,
        reason="Cycle count",
        created_by_user_id=user_id,
    )
    assert success
    assert db.get_current_stock(product_id, source_location_id) == 7.0
