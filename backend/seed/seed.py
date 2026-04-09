"""
seed.py — Populates the database with mock data and embeds vectors.
Run once: python seed/seed.py
Safe to re-run (upserts by name).
"""
from __future__ import annotations
import json, sys, os
from pathlib import Path

# Allow imports from backend root
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.connection import SessionLocal
from db.migrations import create_tables
from db.models import Company, Lead, ProductCatalogItem
from db.vector_store import embed_text

SEED_DIR = Path(__file__).parent


def load_json(filename: str) -> list:
    with open(SEED_DIR / filename) as f:
        return json.load(f)


def seed_companies(db, companies_data: list) -> dict[str, Company]:
    """Insert or update companies, return name→Company map."""
    print("🏢 Seeding companies...")
    company_map: dict[str, Company] = {}

    # Embed all company descriptions at once (batch is faster)
    texts = [
        f"{c['name']} {c['industry']} {c['description']} "
        + " ".join(c.get("pain_points", []))
        for c in companies_data
    ]
    print(f"   Embedding {len(texts)} company profiles...")
    embeddings = embed_text(texts)

    for data, emb in zip(companies_data, embeddings):
        existing = db.query(Company).filter_by(name=data["name"]).first()
        if existing:
            company_map[data["name"]] = existing
            print(f"   ↩  {data['name']} already exists — skipping")
            continue

        company = Company(
            name=data["name"],
            industry=data["industry"],
            size=data["size"],
            hq=data["hq"],
            description=data["description"],
            tech_stack=data["tech_stack"],
            pain_points=data["pain_points"],
            recent_signals=data["recent_signals"],
            hiring_trends=data["hiring_trends"],
            embedding=emb,
        )
        db.add(company)
        db.flush()  # get the id before commit
        company_map[data["name"]] = company
        print(f"   ✅ {data['name']}")

    db.commit()
    return company_map


def seed_leads(db, leads_data: list, company_map: dict):
    print("\n👤 Seeding leads...")
    for data in leads_data:
        company = company_map.get(data["company"])
        if not company:
            print(f"   ⚠️  Company '{data['company']}' not found — skipping lead {data['name']}")
            continue

        exists = db.query(Lead).filter_by(email=data["email"]).first()
        if exists:
            print(f"   ↩  {data['name']} already exists — skipping")
            continue

        lead = Lead(
            company_id=company.id,
            name=data["name"],
            title=data["title"],
            email=data["email"],
            linkedin_url=f"https://linkedin.com/in/{data['name'].lower().replace(' ', '-')}",
        )
        db.add(lead)
        print(f"   ✅ {data['name']} @ {data['company']}")

    db.commit()


def seed_product_catalog(db, catalog_data: list):
    print("\n📦 Seeding product catalog...")
    texts = [
        f"{p['name']} {p['category']} {p['description']} "
        + " ".join(p.get("pain_points_solved", []))
        for p in catalog_data
    ]
    print(f"   Embedding {len(texts)} catalog items...")
    embeddings = embed_text(texts)

    for data, emb in zip(catalog_data, embeddings):
        exists = db.query(ProductCatalogItem).filter_by(name=data["name"]).first()
        if exists:
            print(f"   ↩  {data['name']} already exists — skipping")
            continue

        item = ProductCatalogItem(
            name=data["name"],
            category=data["category"],
            description=data["description"],
            pain_points_solved=data["pain_points_solved"],
            ideal_customer=data["ideal_customer"],
            embedding=emb,
        )
        db.add(item)
        print(f"   ✅ {data['name']}")

    db.commit()


def main():
    print("═" * 50)
    print("  Sales CRM Intelligence — Seed Script")
    print("═" * 50)

    create_tables()
    print("✅ Tables ensured\n")

    db = SessionLocal()
    try:
        companies_data = load_json("mock_companies.json")
        leads_data     = load_json("mock_leads.json")
        catalog_data   = load_json("product_catalog.json")

        company_map = seed_companies(db, companies_data)
        seed_leads(db, leads_data, company_map)
        seed_product_catalog(db, catalog_data)

        print("\n═" * 50)
        print("✅ Seeding complete!")
        print(f"   Companies : {db.query(Company).count()}")
        print(f"   Leads     : {db.query(Lead).count()}")
        print(f"   Catalog   : {db.query(ProductCatalogItem).count()}")
        print("═" * 50)
    finally:
        db.close()


if __name__ == "__main__":
    main()