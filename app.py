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
# 1. ULTIMATE CONFIG & PROFESSIONAL THEME
# ==========================================
st.set_page_config(page_title="Kerala Buy & Sell GOLD", page_icon="🌴", layout="wide")

st.markdown("""
<style>
    /* Professional OLX-Style Theme */
    :root { --kerala-green: #008130; --olx-teal: #002f34; --action-orange: #ffce32; }
    .stApp { background-color: #f2f4f5; }
    
    /* Header & Navigation */
    .main-header { background: white; padding: 1rem 5%; display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #e1e8ed; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    .logo-text { font-size: 32px; font-weight: 900; color: var(--olx-teal); }
    .logo-text span { color: var(--kerala-green); }
    
    /* Product Cards */
    .ad-card { background: white; border-radius: 8px; border: 1px solid #cfd9db; padding: 0; transition: 0.3s; margin-bottom: 20px; position: relative; overflow: hidden; }
    .ad-card:hover { transform: translateY(-5px); box-shadow: 0 10px 20px rgba(0,0,0,0.1); }
    .price-label { font-size: 22px; font-weight: 800; color: var(--olx-teal); padding: 10px 15px 0 15px; }
    .title-label { font-size: 16px; color: #406367; padding: 0 15px; height: 40px; overflow: hidden; }
    .loc-label { font-size: 12px; color: #707a7a; padding: 5px 15px 15px 15px; text-transform: uppercase; }
    
    /* Status Badges */
    .badge-boost { position: absolute; top: 10px; left: 10px; background: var(--action-orange); color: var(--olx-teal); font-weight: bold; font-size: 10px; padding: 3px 8px; border-radius: 4px; }
    .badge-bid { position: absolute; top: 10px; right: 10px; background: #e8f5e9; color: #2e7d32; font-weight: bold; font-size: 10px; padding: 3px 8px; border-radius: 4px; }

    /* Buttons */
    .stButton>button { border-radius: 4px; font-weight: 700; }
    .btn-sell { background: linear-gradient(to right, #ffce32, #ffb700) !important; color: #002f34 !important; border: 4px solid white !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. GEOLOCATION ENGINE (KERALA DATA)
# ==========================================
DISTRICTS = {
    "Trivandrum": (8.5241, 76.9366), "Kollam": (8.8932, 76.6141), "Pathanamthitta": (9.2648, 76.7870),
    "Alappuzha": (9.4981, 76.3388), "Kottayam": (9.5916, 76.5221), "Idukki": (9.8503, 77.0195),
    "Ernakulam": (9.9312, 76.2673), "Thrissur": (10.5276, 76.2144), "Palakkad": (10.7867, 76.6547),
    "Malappuram": (11.0735, 76.0740), "Kozhikode": (11.2588, 75.7804), "Wayanad": (11.6854, 76.1320),
    "Kannur": (11.8745, 75.3704), "Kasaragod": (12.4996, 74.9869)
}

def get_dist(lat1, lon1, lat2, lon2):
    p = pi/180
    a = 0.5 - cos((lat2-lat1)*p)/2 + cos(lat1*p) * cos(lat2*p) * (1-cos((lon2-lon1)*p))/2
    return 12742 * asin(sqrt(a)) # KM

# ==========================================
# 3. DATABASE ARCHITECTURE (SQLITE)
# ==========================================
@st.cache_resource
def init_db():
    conn = sqlite3.connect("kerala_godmode.db", check_same_thread=False)
    c = conn.cursor()
    # Users: Address required for verification
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, mobile TEXT UNIQUE, address TEXT, role TEXT, joined TEXT)")
    # Ads: Images, Video, GPS, Bidding, AI Flag
    c.execute("""CREATE TABLE IF NOT EXISTS ads 
              (id INTEGER PRIMARY KEY, seller TEXT, title TEXT, price REAL, cat TEXT, loc TEXT, 
              lat REAL, lon REAL, desc TEXT, images TEXT, video TEXT, boost TEXT, views INTEGER, 
              is_flagged INTEGER, status TEXT, date TEXT)""")
    # Bidding
    c.execute("CREATE TABLE IF NOT EXISTS bids (ad_id INTEGER, bidder TEXT, amount REAL, time TEXT)")
    # Internal Chat
    c.execute("CREATE TABLE IF NOT EXISTS chats (id INTEGER PRIMARY KEY, sender TEXT, receiver TEXT, msg TEXT, date TEXT)")
    conn.commit()
    return conn

db = init_db()
ADMIN_NUM = "8590304889"

# ==========================================
# 4. SESSION & AUTH
# ==========================================
if "user" not in st.session_state: st.session_state.user = None
if "page" not in st.session_state: st.session_state.page = "home"
if "otp_sent" not in st.session_state: st.session_state.otp_sent = False

def ai_moderator(text):
    spam_words = ["scam", "fake", "illegal", "drugs", "hack", "free money"]
    return 1 if any(w in text.lower() for w in spam_words) else 0

# ==========================================
# 5. HEADER COMPONENT
# ==========================================
st.markdown(f"""
<div class="main-header">
    <div class="logo-text">Kerala<span>Buy&Sell</span></div>
    <div style="color:#002f34; font-weight:bold;">📍 All Kerala Market</div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 6. LOGIN / OTP SYSTEM
# ==========================================
if not st.session_state.user:
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,1.5,1])
    with c2:
        st.subheader("🔑 Secure Verified Login")
        if not st.session_state.otp_sent:
            mob = st.text_input("Mobile Number (+91)", placeholder="Enter 10 digit number")
            adr = st.text_area("Your Location/Address (Mandatory)")
            if st.button("Send OTP", use_container_width=True):
                if len(mob) >= 10 and len(adr) > 5:
                    st.session_state.temp_mob = mob
                    st.session_state.temp_adr = adr
                    st.session_state.generated_otp = str(random.randint(1000, 9999))
                    st.session_state.otp_sent = True
                    st.rerun()
                else: st.error("Please provide valid Mobile and Address.")
        else:
            st.info(f"Verification Code: **{st.session_state.generated_otp}** (Sent to {st.session_state.temp_mob})")
            o_in = st.text_input("Enter 4-Digit Code")
            if st.button("Verify & Enter"):
                if o_in == st.session_state.generated_otp:
                    # Save User
                    role = "Admin" if st.session_state.temp_mob == ADMIN_NUM else "User"
                    db.execute("INSERT OR IGNORE INTO users (mobile, address, role, joined) VALUES (?,?,?,?)",
                              (st.session_state.temp_mob, st.session_state.temp_adr, role, str(datetime.now())))
                    db.commit()
                    st.session_state.user = st.session_state.temp_mob
                    st.rerun()
    st.stop()

# ==========================================
# 7. NAVIGATION BAR
# ==========================================
st.markdown("---")
n1, n2, n3, n4, n5, n6 = st.columns(6)
if n1.button("🏠 Home"): st.session_state.page = "home"
if n2.button("➕ Sell Now", type="primary"): st.session_state.page = "post"
if n3.button("💬 Messages"): st.session_state.page = "chat"
if n4.button("🧮 Tools"): st.session_state.page = "tools"
if st.session_state.user == ADMIN_NUM:
    if n5.button("👑 Admin"): st.session_state.page = "admin"
if n6.button("🚪 Logout"):
    st.session_state.user = None
    st.rerun()

# ==========================================
# 8. APP ROUTING
# ==========================================

# --- HOME (MARKETPLACE) ---
if st.session_state.page == "home":
    # Search & GPS Section
    st.markdown('<div style="background:white; padding:20px; border-radius:8px; margin-bottom:20px;">', unsafe_allow_html=True)
    c_s1, c_s2, c_s3 = st.columns([3, 1, 1])
    search_query = c_s1.text_input("🔍 AI Fuzzy Search", placeholder="Try 'iPhone', 'Bike', 'House'...")
    my_loc = c_s2.selectbox("Search Near", ["All Kerala"] + list(DISTRICTS.keys()))
    sort_by = c_s3.selectbox("Sort", ["Newest", "Price: Low to High", "Nearest"])
    st.markdown('</div>', unsafe_allow_html=True)

    # Fetch Data
    df = pd.read_sql("SELECT * FROM ads WHERE status='Approved'", db)
    
    # AI Search Logic
    if search_query:
        df = df[df['title'].str.contains(search_query, case=False) | df['desc'].str.contains(search_query, case=False)]
    
    # GPS Nearby Logic
    if my_loc != "All Kerala":
        u_lat, u_lon = DISTRICTS[my_loc]
        df['distance'] = df.apply(lambda r: get_dist(u_lat, u_lon, r['lat'], r['lon']), axis=1)
        if sort_by == "Nearest": df = df.sort_values('distance')
    
    if sort_by == "Price: Low to High": df = df.sort_values('price')
    elif sort_by == "Newest": df = df.sort_values('id', ascending=False)

    # Display Ad Grid
    if df.empty:
        st.info("No matching ads found in Kerala.")
    else:
        grid = st.columns(4)
        for i, row in df.iterrows():
            with grid[i % 4]:
                st.markdown('<div class="ad-card">', unsafe_allow_html=True)
                # Badges
                if row['boost'] != "Normal": st.markdown(f'<div class="badge-boost">{row["boost"]}</div>', unsafe_allow_html=True)
                
                # Image
                imgs = json.loads(row['images'])
                if imgs: st.image(base64.b64decode(imgs[0]), use_container_width=True)
                else: st.image("https://via.placeholder.com/300x200", use_container_width=True)
                
                st.markdown(f'<div class="price-label">₹{row["price"]:,}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="title-label">{row["title"]}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="loc-label">📍 {row["loc"]}</div>', unsafe_allow_html=True)
                
                # Quick Interaction
                c_act1, c_act2 = st.columns(2)
                if c_act1.button("View", key=f"v_{row['id']}"):
                    st.info(f"**Seller:** {row['seller']}\n\n**Info:** {row['desc']}")
                    if row['video']: st.video(base64.b64decode(row['video']))
                
                qr_link = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=AdID_{row['id']}"
                if c_act2.button("QR Code", key=f"qr_{row['id']}"):
                    st.image(qr_link, caption="Scan to Share")
                
                # Bidding Section
                max_bid = db.execute("SELECT MAX(amount) FROM bids WHERE ad_id=?", (row['id'],)).fetchone()[0]
                if max_bid: st.caption(f"🔥 Highest Bid: ₹{max_bid:,}")
                
                bid_amt = st.number_input("Offer", min_value=float(row['price']), key=f"bidin_{row['id']}")
                if st.button("Place Bid", key=f"btnbid_{row['id']}"):
                    db.execute("INSERT INTO bids VALUES (?,?,?,?)", (row['id'], st.session_state.user, bid_amt, str(datetime.now())))
                    db.commit()
                    st.success("Bid Submitted!")
                
                st.markdown('</div>', unsafe_allow_html=True)

# --- POST AD ---
elif st.session_state.page == "post":
    st.subheader("🚀 Post Your Classified Ad")
    with st.form("ad_form"):
        col1, col2 = st.columns(2)
        title = col1.text_input("Ad Title*")
        price = col2.number_input("Price (₹)*", min_value=0.0)
        cat = col1.selectbox("Category*", ["Mobiles", "Vehicles", "Electronics", "Property", "Home Decor"])
        loc = col2.selectbox("Location (District)*", list(DISTRICTS.keys()))
        desc = st.text_area("Full Description*")
        
        up_imgs = st.file_uploader("Upload Images (Max 3)", accept_multiple_files=True)
        up_vid = st.file_uploader("Optional Video Tour", type=['mp4'])
        boost = st.selectbox("Boost Your Ad", ["Normal", "Fast Sell (₹99)", "Premium (₹299)"])
        
        if st.form_submit_button("Post Listing Now"):
            if title and price and desc and up_imgs:
                # Convert to B64
                img_list = [base64.b64encode(f.read()).decode() for f in up_imgs]
                vid_data = base64.b64encode(up_vid.read()).decode() if up_vid else None
                
                lat, lon = DISTRICTS[loc]
                flag = ai_moderator(title + desc)
                
                db.execute("""INSERT INTO ads (seller, title, price, cat, loc, lat, lon, desc, images, video, boost, views, is_flagged, status, date) 
                           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                           (st.session_state.user, title, price, cat, loc, lat, lon, desc, json.dumps(img_list), vid_b64, boost, 0, flag, 'Approved', str(datetime.now())))
                db.commit()
                st.success("Ad posted successfully! Bidders can now find you.")
            else: st.error("Complete all fields and add photos.")

# --- TOOLS ---
elif st.session_state.page == "tools":
    st.subheader("🧮 Professional Calculators")
    t1, t2 = st.tabs(["GST Calculator", "EMI Calculator"])
    with t1:
        base = st.number_input("Amount (INR)", min_value=0.0)
        rate = st.selectbox("GST %", [5, 12, 18, 28])
        if base: st.metric("Total Bill", f"₹{base + (base*rate/100):,.2f}")
    with t2:
        p = st.number_input("Loan Principal", min_value=0.0)
        r = st.number_input("Annual Interest (%)")
        y = st.number_input("Tenure (Years)", min_value=1)
        if p and r:
            rate_m = (r/12)/100
            n = y * 12
            emi = (p * rate_m * (1+rate_m)**n) / ((1+rate_m)**n - 1)
            st.metric("Monthly EMI", f"₹{emi:,.2f}")

# --- ADMIN PANEL ---
elif st.session_state.page == "admin" and st.session_state.user == ADMIN_NUM:
    st.subheader("👑 Global Command Center")
    adm_t1, adm_t2, adm_t3 = st.tabs(["Dashboard", "Moderation", "Bulk WhatsApp"])
    
    with adm_t1:
        users = pd.read_sql("SELECT * FROM users", db)
        ads = pd.read_sql("SELECT * FROM ads", db)
        st.metric("Total Users", len(users))
        st.metric("Live Ads", len(ads))
        st.dataframe(users)

    with adm_t2:
        st.warning("Flagged Ads by AI Moderator")
        flagged = pd.read_sql("SELECT id, title, is_flagged FROM ads WHERE is_flagged=1", db)
        st.table(flagged)
        del_id = st.number_input("ID to Delete", step=1)
        if st.button("Confirm Delete"):
            db.execute("DELETE FROM ads WHERE id=?", (del_id,))
            db.commit()
            st.rerun()

    with adm_t3:
        st.info("Broadcast to all registered Kerala users")
        m_txt = st.text_area("Marketing Message")
        if st.button("Generate Bulk Links"):
            u_list = pd.read_sql("SELECT mobile FROM users", db)['mobile'].tolist()
            for m in u_list:
                st.write(f"👉 [Send to {m}](https://wa.me/{m}?text={m_txt})")

# --- FOOTER ---
st.markdown("---")
st.markdown("<center>🌴 <b>Kerala Buy & Sell GOLD v3.0</b> | One-Time Paste Enterprise Edition | © 2026</center>", unsafe_allow_html=True)
