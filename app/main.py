from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import or_, func
from sqlalchemy.orm import Session
from .database import Base, SessionLocal, engine, get_db
from .models import Asset, Activity
from .schemas import AssetCreate, AssetRead, ActivityRead

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    # Populate a fresh local database so the dashboard is useful on first launch.
    # Existing inventories are left untouched.
    with SessionLocal() as db:
        if db.query(Asset).count() == 0:
            samples = [
                Asset(name="Customer Churn Features", asset_type="Dataset", description="Curated customer activity and billing features for churn analysis.", owner="Maya Chen", team="Customer Analytics", status="Available", location="s3://ai-data/customer/churn-features", license="Internal", tags="customer, churn, tabular", version="2.1"),
                Asset(name="Retail Demand Forecast", asset_type="Model", description="Gradient boosting model for weekly SKU demand forecasts.", owner="Jordan Lee", team="Applied ML", status="In Use", location="mlflow:/models/retail-demand/12", license="Internal", tags="forecasting, retail, production", version="1.4.0"),
                Asset(name="Support Ticket Embeddings", asset_type="Dataset", description="Vectorized support conversations with PII removed.", owner="Aisha Patel", team="Data Platform", status="Needs Review", location="s3://ai-data/support/embeddings", license="Internal", tags="embeddings, support, pii-reviewed", version="3.0"),
                Asset(name="Document RAG Starter", asset_type="Code", description="Reusable ingestion and retrieval pipeline for internal knowledge bases.", owner="Noah Williams", team="AI Enablement", status="Available", location="https://github.com/example/document-rag-starter", license="Apache-2.0", tags="rag, retrieval, starter", version="0.8.2"),
                Asset(name="Product Taxonomy Classifier", asset_type="Model", description="Text classifier that maps product descriptions to the company taxonomy.", owner="Maya Chen", team="Applied ML", status="In Use", location="mlflow:/models/product-taxonomy/7", license="Internal", tags="classification, nlp, catalog", version="2.0.1"),
                Asset(name="Public Weather History", asset_type="Dataset", description="Daily weather observations used by logistics and demand experiments.", owner="Ethan Brooks", team="Data Science", status="Available", location="https://example.com/data/weather-history", license="CC BY 4.0", tags="weather, time-series, public", version="2025-10"),
                Asset(name="GPU Training Cost Explorer", asset_type="Tool", description="Notebook utility for comparing training runs, GPU hours, and estimated cost.", owner="Priya Nair", team="AI Enablement", status="Available", location="https://github.com/example/gpu-cost-explorer", license="MIT", tags="gpu, cost, notebook", version="1.2"),
                Asset(name="Customer 360 Data Dictionary", asset_type="Report", description="Definitions, source systems, and refresh expectations for customer features.", owner="Jordan Lee", team="Customer Analytics", status="Needs Review", location="https://example.com/docs/customer-360", license="Internal", tags="documentation, customer, governance", version="4.3"),
                Asset(name="Invoice OCR Benchmark", asset_type="Dataset", description="Labeled invoice pages for evaluating extraction quality across vendors.", owner="Aisha Patel", team="Applied ML", status="Archived", location="s3://ai-data/benchmarks/invoice-ocr", license="Research Use", tags="ocr, benchmark, documents", version="1.0"),
                Asset(name="Feature Drift Monitor", asset_type="Code", description="Scheduled checks for changes in production feature distributions.", owner="Ethan Brooks", team="Data Platform", status="In Use", location="https://github.com/example/feature-drift-monitor", license="Internal", tags="monitoring, drift, quality", version="1.6.3"),
            ]
            db.add_all(samples)
            db.flush()
            db.add_all([Activity(asset_id=item.id, action="Added sample data", detail=f"{item.name} added to the starter catalog") for item in samples])
            db.commit()
    yield

app = FastAPI(title="AI & Data Inventory", description="Catalog and manage reusable AI and data assets.", version="1.0.0", lifespan=lifespan)

def record(db: Session, asset_id: int, action: str, detail: str):
    db.add(Activity(asset_id=asset_id, action=action, detail=detail))

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/assets", response_model=list[AssetRead])
def list_assets(q: str | None = None, asset_type: str | None = None, status: str | None = None, team: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Asset)
    if q:
        pattern = f"%{q}%"
        query = query.filter(or_(Asset.name.ilike(pattern), Asset.description.ilike(pattern), Asset.tags.ilike(pattern), Asset.owner.ilike(pattern)))
    if asset_type and asset_type != "All": query = query.filter(Asset.asset_type == asset_type)
    if status and status != "All": query = query.filter(Asset.status == status)
    if team and team != "All": query = query.filter(Asset.team == team)
    return query.order_by(Asset.updated_at.desc()).all()

@app.post("/assets", response_model=AssetRead, status_code=201)
def create_asset(payload: AssetCreate, db: Session = Depends(get_db)):
    asset = Asset(**payload.model_dump())
    db.add(asset); db.flush(); record(db, asset.id, "Created", asset.name); db.commit(); db.refresh(asset)
    return asset

@app.get("/assets/{asset_id}", response_model=AssetRead)
def get_asset(asset_id: int, db: Session = Depends(get_db)):
    asset = db.get(Asset, asset_id)
    if not asset: raise HTTPException(404, "Asset not found")
    return asset

@app.put("/assets/{asset_id}", response_model=AssetRead)
def update_asset(asset_id: int, payload: AssetCreate, db: Session = Depends(get_db)):
    asset = db.get(Asset, asset_id)
    if not asset: raise HTTPException(404, "Asset not found")
    before = asset.name
    for key, value in payload.model_dump().items(): setattr(asset, key, value)
    record(db, asset.id, "Updated", f"{before} updated"); db.commit(); db.refresh(asset)
    return asset

@app.delete("/assets/{asset_id}", status_code=204)
def delete_asset(asset_id: int, db: Session = Depends(get_db)):
    asset = db.get(Asset, asset_id)
    if not asset: raise HTTPException(404, "Asset not found")
    record(db, asset.id, "Deleted", asset.name); db.delete(asset); db.commit()

@app.get("/stats")
def stats(db: Session = Depends(get_db)):
    total = db.query(func.count(Asset.id)).scalar() or 0
    by_type = dict(db.query(Asset.asset_type, func.count(Asset.id)).group_by(Asset.asset_type).all())
    by_status = dict(db.query(Asset.status, func.count(Asset.id)).group_by(Asset.status).all())
    return {"total": total, "by_type": by_type, "by_status": by_status}

@app.get("/activity", response_model=list[ActivityRead])
def activity(limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    return db.query(Activity).order_by(Activity.created_at.desc()).limit(limit).all()
