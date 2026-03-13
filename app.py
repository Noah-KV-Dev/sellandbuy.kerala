import streamlit as st
import sqlite3
import pandas as pd
import json
import base64
import random
import time
from datetime import datetime
from math import cos, asin, sqrt, pi

# ==========================================
# 1. THE TITAN UI & THEME (MOBILE OPTIMIZED)
# ==========================================
st.set_page_config(page_title="Kerala Buy & Sell TITAN", page_icon="🌴", layout="wide")

st.markdown("""
<style>
    :root { --k-green: #008130; --k-teal: #002f34; --k-yellow: #ffce32; }
    .stApp { background-color: #f2f4f5; }
    
    /* Header & Navigation */
    .header { background: white; padding: 15px; border-bottom: 3px solid var(--k-green); position: sticky; top: 0; z-index: 1000; display: flex; justify-content: space-between; }
    .logo { font-size: 24px; font-weight: 900; color: var(--k-teal); }
    .logo span { color: var(--k-green); }

    /* OLX Style Card */
    .card { background: white; border-radius: 8px; border: 1px solid #ced4da; margin-bottom: 15px; overflow: hidden; position: relative; transition: 0.3s; }
    .card:hover { transform: translateY(-3px); box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
    .price-tag { font-size: 20px; font-weight: 800; color: var(--k-teal); padding: 10px 15px 0 15px; }
    .verified-tick { color: #1d9bf0; font-size: 14px; font-weight: bold; }
    .dist-tag { font-size: 12px; color: #707a7a; padding: 0 15px 10px 15px; }

    /* Sticky Bottom Nav */
    .bot-nav { position: fixed; bottom: 0; left: 0; right: 0; background: white; display: flex; justify-content: space-around; padding: 10px; border-top: 1px solid #ddd; z-index: 1000; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CORE ENGINES (DATABASE & GPS)
# ==========================================
DISTRICTS = {
    "Ernakulam": (9.9312, 76.2673), "Trivandrum": (8.5241, 76.9366), "Kozhikode": (11.2588, 75.7804),
    "Thrissur": (10.5276, 76.2144), "Malappuram": (11.0735, 76.0740), "Kannur": (11.8745, 75.3704),
    "Kollam": (8.8932, 76.6141), "Kottayam": (9.5916, 76.5221), "Palakkad": (10.7867, 76.6547),
    "Alappuzha": (9.4981, 76.3388), "Idukki": (9.8503, 77.0195), "Pathanamthitta": (9.2648, 76.7870),
    "Wayanad": (11.6854, 76.1320), "Kasaragod": (12.4996, 74.9869)
}

def get_distance(p1, p2):
    p = pi/180
    a = 0.5 - cos((p2[0]-p1[0])*p)/2 + cos(p1[0]*p) * cos(p2[0]*p) * (1-cos((p2[1]-p1[1])*p))/2
    return 12742 * asin(sqrt(a))

@st.cache_resource
def startup_database():
    conn = sqlite3.connect("kerala_ultra_v3.db", check_same_thread=False)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (mobile TEXT PRIMARY KEY, addr TEXT, role TEXT, is_verified INT, joined TEXT)")
    c.execute("""CREATE TABLE IF NOT EXISTS ads 
              (id INTEGER PRIMARY KEY, seller TEXT, title TEXT, price REAL, cat TEXT, loc TEXT, 
              desc TEXT, boost TEXT, views INT, status TEXT, date TEXT)""")
    c.execute("CREATE TABLE IF NOT EXISTS bids (ad_id INT, bidder TEXT, amount REAL)")
    c.execute("CREATE TABLE IF NOT EXISTS revenue (amount REAL, plan TEXT, date TEXT)")
    conn.commit()
    return conn

db = startup_database()
ADMIN_MOBILE = "8590304889"

# ==========================================
# 3. AUTHENTICATION & HEADER
# ==========================================
if "user" not in st.session_state: st.session_state.user = None
if "page" not in st.session_state: st.session_state.page = "home"
if "my_loc" not in st.session_state: st.session_state.my_loc = "Ernakulam"

st.markdown(f"""
<div class="header">
    <div class="logo">Kerala<span>Buy&Sell</span></div>
    <div style="font-weight:bold; color:var(--k-green);">📍 {st.session_state.my_loc}</div>
</div>
""", unsafe_allow_html=True)

if not st.session_state.user:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col_a, col_b, col_c = st.columns([1,2,1])
    with col_b:
        st.subheader("Login to Kerala's Market")
        u_mob = st.text_input("Mobile Number", placeholder="91XXXXXXXXXX")
        u_adr = st.text_area("Your Town/District")
        if st.button("Enter Platform", use_container_width=True):
            if len(u_mob) >= 10:
                role = "Admin" if u_mob == ADMIN_MOBILE else "User"
                db.execute("INSERT OR IGNORE INTO users VALUES (?,?,?,?,?)", (u_mob, u_adr, role, 0, str(datetime.now())))
                db.commit()
                st.session_state.user = u_mob
                st.rerun()
    st.stop()

# ==========================================
# 4. APP NAVIGATION & PAGES
# ==========================================

# --- HOME PAGE ---
if st.session_state.page == "home":
    st.session_state.my_loc = st.sidebar.selectbox("Filter District", list(DISTRICTS.keys()), index=list(DISTRICTS.keys()).index(st.session_state.my_loc))
    search = st.text_input("🔍 Search 100,000+ items in Kerala...")
    
    ads_df = pd.read_sql("SELECT * FROM ads WHERE status='Approved'", db)
    
    # Logic: Proximity & Search
    if not ads_df.empty:
        u_lat, u_lon = DISTRICTS[st.session_state.my_loc]
        ads_df['km'] = ads_df.apply(lambda r: get_distance((u_lat, u_lon), DISTRICTS.get(r['loc'], (9.9, 76.2))), axis=1)
        ads_df = ads_df.sort_values(['boost', 'km'], ascending=[False, True])
        
        if search: ads_df = ads_df[ads_df['title'].str.contains(search, case=False)]

        grid = st.columns(2) # Mobile optimized 2-column grid
        for i, row in ads_df.iterrows():
            with grid[i % 2]:
                # Seller Verification Check
                is_v = db.execute("SELECT is_verified FROM users WHERE mobile=?", (row['seller'],)).fetchone()[0]
                badge = '<span class="verified-tick">✔</span>' if is_v else ''
                
                st.markdown(f"""
                <div class="card">
                    <img src="https://via.placeholder.com/200x150?text={row['cat']}" style="width:100%;">
                    <div class="price-tag">₹{row['price']:,} {badge}</div>
                    <div style="padding:0 15px; font-weight:bold; font-size:14px;">{row['title']}</div>
                    <div class="dist-tag">📍 {row['loc']} ({round(row['km'],1)} km)</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Action Buttons
                c1, c2 = st.columns(2)
                if c1.button("Chat", key=f"chat_{row['id']}"):
                    st.warning("⚠️ SAFETY: Never pay advance via UPI. Meet at a public mall or station.")
                    wa_url = f"https://wa.me/{row['seller']}?text=Hi, interest in {row['title']}"
                    st.markdown(f"[Open WhatsApp]({wa_url})")
                
                if c2.button("Share", key=f"sh_{row['id']}"):
                    share_text = f"Check this {row['title']} for ₹{row['price']} on Kerala Buy & Sell! Link: [YOUR_APP_URL]"
                    st.markdown(f'<a href="https://wa.me/?text={share_text}" target="_blank">Share to Status</a>', unsafe_allow_html=True)

# --- POST AD ---
elif st.session_state.page == "post":
    st.subheader("Sell Your Item")
    with st.form("post_form"):
        title = st.text_input("What are you selling?*")
        price = st.number_input("Price (₹)*", min_value=1.0)
        cat = st.selectbox("Category", ["Mobiles", "Vehicles", "Electronics", "Property"])
        loc = st.selectbox("Location (District)*", list(DISTRICTS.keys()))
        desc = st.text_area("Description*")
        plan = st.selectbox("Boost Plan", ["Normal (Free)", "Fast Sell (₹99)", "Spotlight (₹249)"])
        
        if st.form_submit_button("Launch Ad"):
            if title and desc:
                db.execute("INSERT INTO ads (seller, title, price, cat, loc, desc, boost, views, status, date) VALUES (?,?,?,?,?,?,?,?,?,?)",
                          (st.session_state.user, title, price, cat, loc, desc, plan, 0, 'Approved', str(datetime.now())))
                if plan != "Normal (Free)":
                    rev = 99 if "99" in plan else 249
                    db.execute("INSERT INTO revenue VALUES (?,?,?)", (rev, plan, str(datetime.now())))
                db.commit()
                st.success("Ad Published! Redirecting...")
                time.sleep(1)
                st.session_state.page = "home"
                st.rerun()

# --- ADMIN PANEL ---
elif st.session_state.page == "admin" and st.session_state.user == ADMIN_MOBILE:
    st.subheader("👑 Admin Command Center")
    total_rev = db.execute("SELECT SUM(amount) FROM revenue").fetchone()[0] or 0
    st.metric("Total App Revenue", f"₹{total_rev:,}")
    
    tab1, tab2 = st.tabs(["Manage Users", "Manage Ads"])
    with tab1:
        u_data = pd.read_sql("SELECT mobile, addr, is_verified FROM users", db)
        st.dataframe(u_data)
        target = st.text_input("Mobile to Verify/Unverify")
        if st.button("Toggle Verified Badge"):
            curr = db.execute("SELECT is_verified FROM users WHERE mobile=?", (target,)).fetchone()[0]
            db.execute("UPDATE users SET is_verified=? WHERE mobile=?", (1 if curr==0 else 0, target))
            db.commit()
            st.rerun()
    with tab2:
        ads_all = pd.read_sql("SELECT id, title, seller FROM ads", db)
        st.dataframe(ads_all)

# --- BOTTOM NAV ---
st.markdown("<br><br><br>", unsafe_allow_html=True)
b1, b2, b3, b4 = st.columns(4)
if b1.button("🏠 Home"): st.session_state.page = "home"; st.rerun()
if b2.button("➕ Sell"): st.session_state.page = "post"; st.rerun()
if b3.button("🧮 Tools"): st.session_state.page = "tools"; st.rerun()
if st.session_state.user == ADMIN_MOBILE:
    if b4.button("👑 Admin"): st.session_state.page = "admin"; st.rerun()
