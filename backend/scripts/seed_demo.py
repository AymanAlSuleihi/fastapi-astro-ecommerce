#!/usr/bin/env python3
"""Demo data seeder — run manually to populate all tables with sample data.

Usage:
    python scripts/seed_demo.py
    docker compose exec backend python scripts/seed_demo.py
"""

import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select

from src.auth.utils import hash_password
from src.config import settings
from src.constants import OrderStatus, PaymentStatus
from src.customers.models import Address, Customer
from src.database import SessionFactory
from src.images.models import Image
from src.orders.models import Order, OrderItem
from src.payments.models import Payment
from src.products.models import AttributeTemplate, Category, Product, ProductVariant
from src.shipping.models import ShippingRate, ShippingZone
from src.store_config.models import StoreSetting


async def run() -> None:
    """Idempotent: skips if products already exist."""
    async with SessionFactory() as db:
        count = await db.scalar(select(func.count(Product.id)))
        if count and count > 0:
            print(f"[demo] Already seeded ({count} products), skipping.")
            return

        print("[demo] Populating demo data…")
        now = datetime.now(UTC)
        pw = hash_password(settings.SUPERUSER_PASSWORD)

        # ── Attribute templates ─────────────────────
        ring_attrs = AttributeTemplate(
            name="Ring Size & Material",
            attributes={
                "size": {"type": "select", "values": ["5", "6", "7", "8", "9"]},
                "material": {
                    "type": "select",
                    "values": ["925 Silver", "14K Gold", "18K Gold", "Rose Gold"],
                },
            },
        )
        necklace_attrs = AttributeTemplate(
            name="Necklace Length & Material",
            attributes={
                "length": {"type": "select", "values": ['16"', '18"', '20"', '24"']},
                "material": {
                    "type": "select",
                    "values": ["925 Silver", "14K Gold", "Stainless Steel"],
                },
            },
        )
        bracelet_attrs = AttributeTemplate(
            name="Bracelet Size & Material",
            attributes={
                "size": {"type": "select", "values": ['6.5"', '7"', '7.5"', '8"']},
                "material": {
                    "type": "select",
                    "values": ["925 Silver", "14K Gold", "Leather", "Beaded"],
                },
            },
        )
        earring_attrs = AttributeTemplate(
            name="Earring Style & Material",
            attributes={
                "style": {"type": "select", "values": ["Stud", "Hoop", "Drop", "Huggie"]},
                "material": {
                    "type": "select",
                    "values": ["925 Silver", "14K Gold", "18K Gold", "Rose Gold"],
                },
            },
        )
        db.add_all([ring_attrs, necklace_attrs, bracelet_attrs, earring_attrs])
        await db.flush()

        # ── Categories ──────────────────────────────
        rings = Category(name="Rings", slug="rings")
        necklaces = Category(name="Necklaces", slug="necklaces")
        bracelets = Category(name="Bracelets", slug="bracelets")
        earrings = Category(name="Earrings", slug="earrings")
        db.add_all([rings, necklaces, bracelets, earrings])
        await db.flush()

        db.add_all(
            [
                Category(name="Engagement", slug="engagement-rings", parent_id=rings.id),
                Category(name="Wedding Bands", slug="wedding-bands", parent_id=rings.id),
                Category(name="Pendants", slug="pendants", parent_id=necklaces.id),
                Category(name="Chains", slug="chains", parent_id=necklaces.id),
                Category(name="Tennis", slug="tennis-bracelets", parent_id=bracelets.id),
                Category(name="Cuffs", slug="cuffs", parent_id=bracelets.id),
            ]
        )
        await db.flush()

        # ── Products ────────────────────────────────
        products_data: list[dict[str, Any]] = [
            # Rings
            {
                "name": "Classic Solitaire Ring",
                "slug": "classic-solitaire-ring",
                "description": (
                    "A timeless solitaire ring featuring a brilliant-cut center stone"
                    " set in a sleek band."
                ),
                "price": 1299.00,
                "category_id": rings.id,
                "attribute_template_id": ring_attrs.id,
                "variants": [
                    ("RNG-SOL-5-SLV", "5", "925 Silver", None, 12),
                    ("RNG-SOL-6-SLV", "6", "925 Silver", None, 8),
                    ("RNG-SOL-7-14K", "7", "14K Gold", 1599.00, 5),
                    ("RNG-SOL-8-14K", "8", "14K Gold", 1599.00, 6),
                    ("RNG-SOL-7-18K", "7", "18K Gold", 2199.00, 3),
                ],
            },
            {
                "name": "Eternity Band",
                "slug": "eternity-band",
                "description": "A full circle of pavé-set stones symbolizing never-ending love.",
                "price": 899.00,
                "category_id": rings.id,
                "attribute_template_id": ring_attrs.id,
                "variants": [
                    ("RNG-ETN-6-14K", "6", "14K Gold", None, 10),
                    ("RNG-ETN-7-14K", "7", "14K Gold", None, 7),
                    ("RNG-ETN-7-RSG", "7", "Rose Gold", 999.00, 4),
                    ("RNG-ETN-8-RSG", "8", "Rose Gold", 999.00, 3),
                ],
            },
            {
                "name": "Vintage Halo Ring",
                "slug": "vintage-halo-ring",
                "description": (
                    "An intricate halo design with milgrain detailing for a vintage-inspired look."
                ),
                "price": 1599.00,
                "category_id": rings.id,
                "attribute_template_id": ring_attrs.id,
                "variants": [
                    ("RNG-HAL-6-SLV", "6", "925 Silver", None, 4),
                    ("RNG-HAL-7-14K", "7", "14K Gold", 1899.00, 3),
                    ("RNG-HAL-8-18K", "8", "18K Gold", 2599.00, 2),
                ],
            },
            # Necklaces
            {
                "name": "Pearl Drop Pendant",
                "slug": "pearl-drop-pendant",
                "description": (
                    "A lustrous freshwater pearl suspended from a delicate chain."
                    " Elegant and understated."
                ),
                "price": 349.00,
                "category_id": necklaces.id,
                "attribute_template_id": necklace_attrs.id,
                "variants": [
                    ("NCK-PRL-18-SLV", '18"', "925 Silver", None, 15),
                    ("NCK-PRL-20-SLV", '20"', "925 Silver", None, 10),
                    ("NCK-PRL-18-14K", '18"', "14K Gold", 499.00, 6),
                    ("NCK-PRL-20-14K", '20"', "14K Gold", 499.00, 4),
                ],
            },
            {
                "name": "Diamond Heart Necklace",
                "slug": "diamond-heart-necklace",
                "description": (
                    "A heart-shaped pendant encrusted with tiny diamonds, perfect for a loved one."
                ),
                "price": 799.00,
                "category_id": necklaces.id,
                "attribute_template_id": necklace_attrs.id,
                "variants": [
                    ("NCK-HRT-16-SLV", '16"', "925 Silver", None, 8),
                    ("NCK-HRT-18-14K", '18"', "14K Gold", 999.00, 5),
                    ("NCK-HRT-20-14K", '20"', "14K Gold", 999.00, 3),
                ],
            },
            {
                "name": "Gold Chain Necklace",
                "slug": "gold-chain-necklace",
                "description": (
                    "A classic Figaro chain crafted from polished 14K gold."
                    " Wear it alone or layer it."
                ),
                "price": 449.00,
                "category_id": necklaces.id,
                "attribute_template_id": necklace_attrs.id,
                "variants": [
                    ("NCK-CHN-18-14K", '18"', "14K Gold", None, 12),
                    ("NCK-CHN-20-14K", '20"', "14K Gold", None, 8),
                    ("NCK-CHN-24-14K", '24"', "14K Gold", 549.00, 5),
                    ("NCK-CHN-20-SS", '20"', "Stainless Steel", 149.00, 20),
                ],
            },
            # Bracelets
            {
                "name": "Tennis Bracelet",
                "slug": "tennis-bracelet",
                "description": (
                    "A continuous line of brilliant stones set in a flexible band."
                    " The ultimate statement piece."
                ),
                "price": 1199.00,
                "category_id": bracelets.id,
                "attribute_template_id": bracelet_attrs.id,
                "variants": [
                    ("BRC-TEN-7-SLV", '7"', "925 Silver", None, 6),
                    ("BRC-TEN-7-14K", '7"', "14K Gold", 1499.00, 4),
                    ("BRC-TEN-7.5-14K", '7.5"', "14K Gold", 1499.00, 3),
                ],
            },
            {
                "name": "Leather Wrap Bracelet",
                "slug": "leather-wrap-bracelet",
                "description": (
                    "Hand-braided genuine leather with a magnetic clasp."
                    " Casual elegance for everyday wear."
                ),
                "price": 79.00,
                "category_id": bracelets.id,
                "attribute_template_id": bracelet_attrs.id,
                "variants": [
                    ("BRC-WRP-7-LTH", '7"', "Leather", None, 25),
                    ("BRC-WRP-8-LTH", '8"', "Leather", None, 18),
                    ("BRC-WRP-7-BD", '7"', "Beaded", 59.00, 15),
                ],
            },
            # Earrings
            {
                "name": "Diamond Stud Earrings",
                "slug": "diamond-stud-earrings",
                "description": (
                    "Classic round-cut diamond studs set in four-prong baskets."
                    " A must-have for every jewelry box."
                ),
                "price": 599.00,
                "category_id": earrings.id,
                "attribute_template_id": earring_attrs.id,
                "variants": [
                    ("ERR-STD-SLV", "Stud", "925 Silver", None, 12),
                    ("ERR-STD-14K", "Stud", "14K Gold", 799.00, 8),
                    ("ERR-STD-18K", "Stud", "18K Gold", 1199.00, 4),
                    ("ERR-STD-RSG", "Stud", "Rose Gold", 699.00, 10),
                ],
            },
            {
                "name": "Gold Hoop Earrings",
                "slug": "gold-hoop-earrings",
                "description": (
                    "Lightweight hollow hoops with a high-polish finish. Day-to-night versatility."
                ),
                "price": 199.00,
                "category_id": earrings.id,
                "attribute_template_id": earring_attrs.id,
                "variants": [
                    ("ERR-HOP-14K", "Hoop", "14K Gold", 249.00, 15),
                    ("ERR-HOP-SLV", "Hoop", "925 Silver", None, 20),
                    ("ERR-HOP-RSG", "Hoop", "Rose Gold", 229.00, 10),
                ],
            },
            {
                "name": "Crystal Drop Earrings",
                "slug": "crystal-drop-earrings",
                "description": (
                    "Teardrop crystals that catch the light with every movement."
                    " Perfect for special occasions."
                ),
                "price": 129.00,
                "category_id": earrings.id,
                "attribute_template_id": earring_attrs.id,
                "variants": [
                    ("ERR-DRP-SLV", "Drop", "925 Silver", None, 14),
                    ("ERR-DRP-14K", "Drop", "14K Gold", 179.00, 8),
                ],
            },
        ]

        _attr_key = {
            ring_attrs.id: "size",
            necklace_attrs.id: "length",
            bracelet_attrs.id: "size",
            earring_attrs.id: "style",
        }

        products = []
        variants: list[ProductVariant] = []
        for pdata in products_data:
            p = Product(
                name=pdata["name"],
                slug=pdata["slug"],
                description=pdata["description"],
                price=pdata["price"],
                category_id=pdata["category_id"],
                attribute_template_id=pdata["attribute_template_id"],
                is_active=True,
            )
            db.add(p)
            await db.flush()
            products.append(p)
            attr1_key = _attr_key[pdata["attribute_template_id"]]
            for sku, attr1_val, attr2_val, price_override, stock in pdata["variants"]:
                v = ProductVariant(
                    product_id=p.id,
                    sku=sku,
                    price_override=price_override,
                    stock_quantity=stock,
                    attributes={attr1_key: attr1_val, "material": attr2_val},
                    is_default=(stock >= 8),
                )
                db.add(v)
                variants.append(v)
        await db.flush()

        # ── Product images ──────────────────────────
        for p in products:
            db.add(
                Image(
                    entity_type="product",
                    entity_id=p.id,
                    url=f"https://picsum.photos/seed/{p.slug}/600/600",
                    storage_key=f"demo/{p.slug}.jpg",
                    alt_text=p.name,
                    sort_order=0,
                )
            )
        await db.flush()

        # ── Demo customers ──────────────────────────
        c1 = Customer(
            email="alice@example.com",
            hashed_password=pw,
            first_name="Alice",
            last_name="Johnson",
            is_active=True,
        )
        c2 = Customer(
            email="bob@example.com",
            hashed_password=pw,
            first_name="Bob",
            last_name="Smith",
            is_active=True,
        )
        c3 = Customer(
            email="carol@example.com",
            hashed_password=pw,
            first_name="Carol",
            last_name="Williams",
            is_active=True,
        )
        db.add_all([c1, c2, c3])
        await db.flush()

        # ── Addresses ───────────────────────────────
        addr1 = Address(
            customer_id=c1.id,
            label="Home",
            address_line1="742 Evergreen Terrace",
            city="Springfield",
            state="IL",
            postal_code="62701",
            country="US",
            phone="+1-555-0101",
            is_default=True,
        )
        addr2 = Address(
            customer_id=c2.id,
            label="Home",
            address_line1="221B Baker Street",
            city="London",
            postal_code="NW1 6XE",
            country="GB",
            phone="+44-20-7946-0958",
            is_default=True,
        )
        addr3 = Address(
            customer_id=c2.id,
            label="Office",
            address_line1="10 Downing Street",
            city="London",
            postal_code="SW1A 2AA",
            country="GB",
            is_default=False,
        )
        addr4 = Address(
            customer_id=c3.id,
            label="Home",
            address_line1="12 Rue de Rivoli",
            city="Paris",
            postal_code="75004",
            country="FR",
            phone="+33-1-42-96-12-34",
            is_default=True,
        )
        db.add_all([addr1, addr2, addr3, addr4])
        await db.flush()

        # ── Shipping zones & rates ──────────────────
        domestic = ShippingZone(name="United States", countries=["US"], is_active=True)
        international = ShippingZone(
            name="International",
            countries=["GB", "FR", "CA", "AU", "DE"],
            is_active=True,
        )
        db.add_all([domestic, international])
        await db.flush()

        db.add_all(
            [
                ShippingRate(
                    zone_id=domestic.id,
                    name="Standard (5-7 days)",
                    description="USPS First Class",
                    base_cost=4.99,
                    free_above=75.00,
                    min_days=5,
                    max_days=7,
                    priority=10,
                ),
                ShippingRate(
                    zone_id=domestic.id,
                    name="Express (1-2 days)",
                    description="USPS Priority Express",
                    base_cost=19.99,
                    free_above=250.00,
                    min_days=1,
                    max_days=2,
                    priority=20,
                ),
                ShippingRate(
                    zone_id=international.id,
                    name="International Standard (7-14 days)",
                    description="DHL eCommerce",
                    base_cost=14.99,
                    free_above=200.00,
                    min_days=7,
                    max_days=14,
                    priority=10,
                ),
                ShippingRate(
                    zone_id=international.id,
                    name="International Express (3-5 days)",
                    description="DHL Express",
                    base_cost=34.99,
                    min_days=3,
                    max_days=5,
                    priority=20,
                ),
            ]
        )
        await db.flush()

        # ── Orders & items ──────────────────────────
        orders_data: list[dict[str, Any]] = [
            {
                "customer": c1,
                "address": addr1,
                "status": OrderStatus.DELIVERED,
                "days_ago": 30,
                "items": [
                    (variants[0], 1, 1299.00),
                    (variants[26], 1, 79.00),
                ],
            },
            {
                "customer": c1,
                "address": addr1,
                "status": OrderStatus.SHIPPED,
                "days_ago": 3,
                "items": [(variants[5], 2, 899.00)],
            },
            {
                "customer": c2,
                "address": addr2,
                "status": OrderStatus.DELIVERED,
                "days_ago": 60,
                "items": [
                    (variants[29], 1, 599.00),
                    (variants[16], 1, 799.00),
                ],
            },
            {
                "customer": c2,
                "address": addr2,
                "status": OrderStatus.DELIVERED,
                "days_ago": 14,
                "items": [
                    (variants[8], 1, 999.00),
                    (variants[33], 1, 199.00),
                ],
            },
            {
                "customer": c2,
                "address": addr3,
                "status": OrderStatus.CONFIRMED,
                "days_ago": 1,
                "items": [(variants[19], 1, 449.00)],
            },
            {
                "customer": c3,
                "address": addr4,
                "status": OrderStatus.PENDING,
                "days_ago": 0,
                "items": [
                    (variants[23], 1, 1199.00),
                    (variants[30], 1, 799.00),
                ],
            },
        ]

        for od in orders_data:
            created = now - timedelta(days=od["days_ago"])
            subtotal = sum(Decimal(str(qty)) * Decimal(str(price)) for _, qty, price in od["items"])
            shipping = Decimal("4.99") if od["address"].country == "US" else Decimal("14.99")
            tax = round(subtotal * Decimal("0.08"), 2)
            total = subtotal + shipping + tax

            order = Order(
                customer_id=od["customer"].id,
                status=od["status"],
                currency="USD",
                total_amount=total,
                subtotal=subtotal,
                tax_amount=tax,
                shipping_cost=shipping,
                shipping_address={
                    "name": f"{od['customer'].first_name} {od['customer'].last_name}",
                    "line1": od["address"].address_line1,
                    "city": od["address"].city,
                    "state": od["address"].state,
                    "postal_code": od["address"].postal_code,
                    "country": od["address"].country,
                },
                created_at=created,
                updated_at=created,
            )
            db.add(order)
            await db.flush()

            for variant, qty, price in od["items"]:
                db.add(
                    OrderItem(
                        order_id=order.id,
                        product_id=variant.product_id,
                        variant_id=variant.id,
                        variant_sku=variant.sku,
                        product_name=variant.product.name,
                        product_price=Decimal(str(price)),
                        line_total=Decimal(str(qty)) * Decimal(str(price)),
                        quantity=qty,
                        currency="USD",
                    )
                )
            await db.flush()

            if od["status"] != OrderStatus.PENDING:
                db.add(
                    Payment(
                        order_id=order.id,
                        amount=total,
                        status=PaymentStatus.COMPLETED,
                        provider="stripe",
                        provider_payment_id=f"pi_demo_{order.display_id}",
                        created_at=created,
                        updated_at=created,
                    )
                )
        await db.flush()

        # ── Store settings ─────────────────────────
        if not await db.scalar(select(func.count(StoreSetting.id))):
            db.add_all(
                [
                    StoreSetting(
                        key="store_name",
                        value={"text": "Example Store"},
                        description="Public store name",
                        is_public=True,
                        section="general",
                    ),
                    StoreSetting(
                        key="store_email",
                        value={"email": "hello@example.com"},
                        description="Customer-facing contact email",
                        is_public=True,
                        section="general",
                    ),
                    StoreSetting(
                        key="tax_rate",
                        value={"rate": 0.08, "label": "Sales Tax"},
                        description="Default tax rate applied to orders",
                        section="pricing",
                    ),
                    StoreSetting(
                        key="currency",
                        value={"code": "USD", "symbol": "$", "label": "US Dollar"},
                        description="Default store currency",
                        is_public=True,
                        section="pricing",
                    ),
                    StoreSetting(
                        key="free_shipping_threshold",
                        value={"amount": 75.00},
                        description="Order subtotal above which domestic shipping is free",
                        section="shipping",
                    ),
                ]
            )

        await db.commit()
        print("[demo] Done — demo data populated.")


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
