from .database import Base, SessionLocal, engine
from .models import Activity, Asset

SAMPLE_ASSETS = [
    dict(name="Customer Churn Features", asset_type="Dataset", description="Curated customer activity and billing features for churn analysis.", owner="Maya Chen", team="Customer Analytics", status="Available", location="s3://ai-data/customer/churn-features", license="Internal", tags="customer, churn, tabular", version="2.1"),
    dict(name="Retail Demand Forecast", asset_type="Model", description="Gradient boosting model for weekly SKU demand forecasts.", owner="Jordan Lee", team="Applied ML", status="In Use", location="mlflow:/models/retail-demand/12", license="Internal", tags="forecasting, retail, production", version="1.4.0"),
    dict(name="Support Ticket Embeddings", asset_type="Dataset", description="Vectorized support conversations with PII removed.", owner="Aisha Patel", team="Data Platform", status="Needs Review", location="s3://ai-data/support/embeddings", license="Internal", tags="embeddings, support, pii-reviewed", version="3.0"),
    dict(name="Document RAG Starter", asset_type="Code", description="Reusable ingestion and retrieval pipeline for internal knowledge bases.", owner="Noah Williams", team="AI Enablement", status="Available", location="https://github.com/example/document-rag-starter", license="Apache-2.0", tags="rag, retrieval, starter", version="0.8.2"),
    dict(name="Product Taxonomy Classifier", asset_type="Model", description="Text classifier that maps product descriptions to the company taxonomy.", owner="Maya Chen", team="Applied ML", status="In Use", location="mlflow:/models/product-taxonomy/7", license="Internal", tags="classification, nlp, catalog", version="2.0.1"),
    dict(name="Public Weather History", asset_type="Dataset", description="Daily weather observations used by logistics and demand experiments.", owner="Ethan Brooks", team="Data Science", status="Available", location="https://example.com/data/weather-history", license="CC BY 4.0", tags="weather, time-series, public", version="2025-10"),
    dict(name="GPU Training Cost Explorer", asset_type="Tool", description="Notebook utility for comparing training runs, GPU hours, and estimated cost.", owner="Priya Nair", team="AI Enablement", status="Available", location="https://github.com/example/gpu-cost-explorer", license="MIT", tags="gpu, cost, notebook", version="1.2"),
    dict(name="Customer 360 Data Dictionary", asset_type="Report", description="Definitions, source systems, and refresh expectations for customer features.", owner="Jordan Lee", team="Customer Analytics", status="Needs Review", location="https://example.com/docs/customer-360", license="Internal", tags="documentation, customer, governance", version="4.3"),
    dict(name="Invoice OCR Benchmark", asset_type="Dataset", description="Labeled invoice pages for evaluating extraction quality across vendors.", owner="Aisha Patel", team="Applied ML", status="Archived", location="s3://ai-data/benchmarks/invoice-ocr", license="Research Use", tags="ocr, benchmark, documents", version="1.0"),
    dict(name="Feature Drift Monitor", asset_type="Code", description="Scheduled checks for changes in production feature distributions.", owner="Ethan Brooks", team="Data Platform", status="In Use", location="https://github.com/example/feature-drift-monitor", license="Internal", tags="monitoring, drift, quality", version="1.6.3"),
]

def initialize_inventory():
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if db.query(Asset).count() == 0:
            assets = [Asset(**values) for values in SAMPLE_ASSETS]
            db.add_all(assets)
            db.flush()
            db.add_all([Activity(asset_id=item.id, action="Added sample data", detail=f"{item.name} added to the starter catalog") for item in assets])
            db.commit()
