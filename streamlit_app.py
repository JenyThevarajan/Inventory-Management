import os
import pandas as pd
import requests
import streamlit as st

API = os.getenv("API_URL", "http://localhost:8000")
st.set_page_config(page_title="AI & Data Inventory", page_icon="◈", layout="wide")
st.markdown("""<style>
.stApp{background:#f5f7fb}.block-container{padding-top:2rem;max-width:1400px}
[data-testid="stMetric"]{background:white;border:1px solid #e6eaf0;padding:18px;border-radius:14px}
</style>""", unsafe_allow_html=True)
st.title("◈  AI & Data Inventory")
st.caption("A shared catalog for datasets, models, code, and the tools that power your team.")

try:
    stats = requests.get(f"{API}/stats", timeout=3).json()
    assets = requests.get(f"{API}/assets", timeout=3).json()
    activity = requests.get(f"{API}/activity", timeout=3).json()
except requests.RequestException:
    st.error("Can't reach the API. Start it with `uvicorn app.main:app --reload`.")
    st.stop()

c1,c2,c3,c4=st.columns(4)
c1.metric("Total assets", stats["total"])
c2.metric("Datasets", stats["by_type"].get("Dataset",0))
c3.metric("Models", stats["by_type"].get("Model",0))
c4.metric("Needs review", stats["by_status"].get("Needs Review",0))

with st.sidebar:
    st.header("Find assets")
    search=st.text_input("Search", placeholder="Name, owner, tags…")
    type_filter=st.selectbox("Type",["All","Dataset","Model","Code","Tool","Report","Other"])
    status_filter=st.selectbox("Status",["All","Available","In Use","Needs Review","Archived"])
    if st.button("＋ Add asset", type="primary", use_container_width=True): st.session_state.show_form=True

if st.session_state.get("show_form"):
    with st.expander("Add an asset to the catalog", expanded=True):
        with st.form("new_asset", clear_on_submit=True):
            name=st.text_input("Asset name *")
            typ=st.selectbox("Type",["Dataset","Model","Code","Tool","Report","Other"])
            desc=st.text_area("Description")
            a,b=st.columns(2)
            owner=a.text_input("Owner"); team=b.text_input("Team")
            c,d=st.columns(2)
            status=c.selectbox("Status",["Available","In Use","Needs Review","Archived"]); version=d.text_input("Version", "1.0")
            license=st.text_input("License", "Unknown")
            location=st.text_input("Link or location")
            tags=st.text_input("Tags", placeholder="forecasting, customer-360")
            submitted=st.form_submit_button("Save asset", type="primary")
            if submitted:
                if not name.strip(): st.error("Asset name is required.")
                else:
                    response=requests.post(f"{API}/assets",json={"name":name,"asset_type":typ,"description":desc,"owner":owner,"team":team,"status":status,"version":version,"license":license,"location":location,"tags":tags},timeout=5)
                    if response.ok: st.success("Asset added."); st.session_state.show_form=False; st.rerun()
                    else: st.error(response.text)

filtered=requests.get(f"{API}/assets",params={"q":search,"asset_type":type_filter,"status":status_filter},timeout=5).json()
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
            if item.get("location"): st.markdown(f"[Open asset location]({item['location']})")
            if st.button("Delete selected asset", key=f"delete-{item['id']}"):
                requests.delete(f"{API}/assets/{item['id']}",timeout=5); st.rerun()
    else: st.info("No assets match these filters. Add your first asset from the sidebar.")
with right:
    st.subheader("By type")
    if stats["by_type"]: st.bar_chart(pd.Series(stats["by_type"],name="Assets"))
    st.subheader("Recent activity")
    if activity:
        for event in activity[:8]: st.markdown(f"**{event['action']}** · {event['detail']}")
    else: st.caption("Activity will appear as your team adds assets.")
