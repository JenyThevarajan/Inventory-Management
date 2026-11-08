from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import or_, func
from sqlalchemy.orm import Session
from .database import get_db
from .models import Asset, Activity
from .schemas import AssetCreate, AssetRead, ActivityRead
from .seed import initialize_inventory

app = FastAPI(title="AI & Data Inventory", description="Catalog and manage reusable AI and data assets.", version="1.0.0", on_startup=[initialize_inventory])

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
