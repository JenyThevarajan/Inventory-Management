import pandas as pd
import streamlit as st
from sqlalchemy import func, or_
from app.database import SessionLocal
from app.models import Activity, Asset
from app.seed import initialize_inventory

initialize_inventory()
st.set_page_config(page_title="AI & Data Inventory", page_icon="◈", layout="wide")
st.markdown("""<style>
.stApp{background:#f5f7fb}.block-container{padding-top:2rem;max-width:1400px}
[data-testid="stMetric"]{background:white;border:1px solid #e6eaf0;padding:18px;border-radius:14px}
</style>""", unsafe_allow_html=True)
st.title("◈  AI & Data Inventory")
st.caption("A shared catalog for datasets, models, code, and the tools that power your team.")

with SessionLocal() as db:
    total = db.query(func.count(Asset.id)).scalar() or 0
    by_type = dict(db.query(Asset.asset_type, func.count(Asset.id)).group_by(Asset.asset_type).all())
    by_status = dict(db.query(Asset.status, func.count(Asset.id)).group_by(Asset.status).all())
    recent_activity = db.query(Activity).order_by(Activity.created_at.desc()).limit(20).all()

c1,c2,c3,c4=st.columns(4)
c1.metric("Total assets", total)
c2.metric("Datasets", by_type.get("Dataset",0))
c3.metric("Models", by_type.get("Model",0))
c4.metric("Needs review", by_status.get("Needs Review",0))

with st.sidebar:
    st.header("Find assets")
    search=st.text_input("Search", placeholder="Name, owner, tags…")
    type_filter=st.selectbox("Type",["All","Dataset","Model","Code","Tool","Report","Other"])
    status_filter=st.selectbox("Status",["All","Available","In Use","Needs Review","Archived"])
    if st.button("＋ Add asset", type="primary", use_container_width=True): 
        st.session_state.show_form=True

if st.session_state.get("show_form"):
    with st.expander("Add an asset to the catalog", expanded=True):
        with st.form("new_asset", clear_on_submit=True):
            name=st.text_input("Asset name *")
            typ=st.selectbox("Type",["Dataset","Model","Code","Tool","Report","Other"])
            desc=st.text_area("Description")
            a,b=st.columns(2)
            owner=a.text_input("Owner")
            team=b.text_input("Team")
            c,d=st.columns(2)
            status=c.selectbox("Status",["Available","In Use","Needs Review","Archived"]) 
            version=d.text_input("Version", "1.0")
            license=st.text_input("License", "Unknown")
            location=st.text_input("Link or location")
            tags=st.text_input("Tags", placeholder="forecasting, customer-360")
            submitted=st.form_submit_button("Save asset", type="primary")
            if submitted:
                if not name.strip(): 
                    st.error("Asset name is required.")
                else:
                    with SessionLocal() as db:
                        asset=Asset(name=name.strip(),asset_type=typ,description=desc,owner=owner,team=team,status=status,version=version,license=license,location=location,tags=tags)
                        db.add(asset)
                        db.flush()
                        db.add(Activity(asset_id=asset.id,action="Created",detail=asset.name))
                        db.commit()
                    st.success("Asset added.")
                    st.session_state.show_form=False
                    st.rerun()

with SessionLocal() as db:
    query=db.query(Asset)
    if search.strip():
        term=f"%{search.strip()}%"
        query=query.filter(or_(Asset.name.ilike(term),Asset.description.ilike(term),Asset.tags.ilike(term),Asset.owner.ilike(term)))
    if type_filter!="All": query=query.filter(Asset.asset_type==type_filter)
    if status_filter!="All": query=query.filter(Asset.status==status_filter)
    rows=query.order_by(Asset.updated_at.desc()).all()
    filtered=[{"id":x.id,"name":x.name,"asset_type":x.asset_type,"team":x.team,"owner":x.owner,"status":x.status,"version":x.version,"license":x.license,"tags":x.tags,"description":x.description,"location":x.location} for x in rows]
left,right=st.columns([2,1],gap="large")
with left:
    st.subheader("Asset catalog")
    if filtered:
        df=pd.DataFrame(filtered)[["name","asset_type","team","owner","status","version","license","tags"]]
        df.columns=["Name","Type","Team","Owner","Status","Version","License","Tags"]
        st.dataframe(df,use_container_width=True,hide_index=True)
        with st.expander("Asset details and actions"):
            options={f"{x['name']} · {x['asset_type']} (#{x['id']})":x for x in filtered}
            selected=st.selectbox("Select an asset",list(options))
            item=options[selected]
            st.write(item.get("description") or "No description provided.")
            if item.get("location"): 
                st.markdown(f"[Open asset location]({item['location']})")
            if st.button("Delete selected asset", key=f"delete-{item['id']}"):
                with SessionLocal() as db:
                    db.add(Activity(asset_id=item["id"],action="Deleted",detail=item["name"]))
                    asset=db.get(Asset,item["id"])
                    if asset: db.delete(asset)
                    db.commit()
                st.rerun()
    else: 
        st.info("No assets match these filters. Add your first asset from the sidebar.")
with right:
    st.subheader("By type")
    if by_type: 
        st.bar_chart(pd.Series(by_type,name="Assets"))
    st.subheader("Recent activity")
    if recent_activity:
        for event in recent_activity[:8]: 
            st.markdown(f"**{event.action}** · {event.detail}")
    else: 
        st.caption("Activity will appear as your team adds assets.")
