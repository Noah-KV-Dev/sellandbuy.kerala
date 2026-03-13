import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random
import base64
import time

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="Kerala Buy & Sell", page_icon="🌴", layout="wide")

# ---------- CONSTANTS ----------
ADMIN_NUMBER = "8590304889"

# ---------- DATABASE SETUP ----------
@st.cache_resource
def init_db():
    conn = sqlite3.connect("marketplace.db", check_same_thread=False)
    cursor = conn.cursor()
    
    # Users Table (Added Address Column)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mobile TEXT UNIQUE,
        address TEXT,
        created_at TEXT
    )""")
    
    # Check if address column exists (for backward compatibility if DB already exists)
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN address TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass # Column already exists
    
    # Ads Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ads(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_mobile TEXT,
        title TEXT,
        price REAL,
        category TEXT,
        location TEXT,
        description TEXT,
        image_data TEXT,
        boost TEXT,
        views INTEGER,
        created_at TEXT
    )""")
    
    # Messages Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT,
        receiver TEXT,
        message TEXT,
        created_at TEXT
    )""")
    
    conn.commit()
    return conn

conn = init_db()
cursor = conn.cursor()

def execute_query(query, params=()):
    cursor.execute(query, params)
    conn.commit()

def get_base64_of_image(upload_file):
    if upload_file is not None:
        return base64.b64encode(upload_file.read()).decode()
    return ""

def send_silent_whatsapp(new_user_mobile, new_user_address):
    """
    To make this truly silent and hidden, you must use a service like Twilio or Meta Graph API.
    Streamlit runs on the server, so putting API requests here keeps it hidden from the user.
    """
    message = f"🚨 New User Registered!\nMobile: {new_user_mobile}\nAddress: {new_user_address}"
    # Example of what you would do with an API:
    # requests.post("https://api.twilio.com/.../Messages.json", auth=(SID, TOKEN), data={"To": ADMIN_NUMBER, "Body": message})
    
    # For now, we log it to the server console so the app doesn't break
    print(f"\n[BACKGROUND NOTIFICATION TO {ADMIN_NUMBER}]: {message}\n")

# ---------- SESSION STATE ----------
if "page" not in st.session_state:
    st.session_state.page = "home"
if "user" not in st.session_state:
    st.session_state.user = None
if "otp_sent" not in st.session_state:
    st.session_state.otp_sent = False
if "expected_otp" not in st.session_state:
    st.session_state.expected_otp = None

# ---------- GRASS THEME ----------
st.markdown("""
<style>
    /* Animated Grass Background */
    .stApp {
        background: linear-gradient(-45deg, #1e8e3e, #2ecc71, #27ae60, #16a085);
        background-size: 400% 400%;
        animation: grass 12s ease infinite;
    }
    
    @keyframes grass{
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* Make text readable over the background */
    h1, h2, h3, h4, p, label {
        color: white !important;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.5);
    }

    /* Sleek Header */
    .main-header {
        background: rgba(0, 0, 0, 0.4);
        padding: 20px;
        border-radius: 12px;
        color: white;
        text-align: center;
        font-size: 32px;
        font-weight: 800;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.3);
        margin-bottom: 25px;
        backdrop-filter: blur(5px);
    }
    
    /* Product Cards */
    .product-card {
        background: rgba(255, 255, 255, 0.95);
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.2);
        margin-bottom: 20px;
        border: 1px solid #e0e0e0;
    }
    
    .product-card h4, .product-card p {
        color: #333 !important;
        text-shadow: none;
    }
    
    .price-tag {
        color: #ff6a00;
        font-size: 24px;
        font-weight: 900;
        margin: 10px 0;
    }
    
    /* Category Badges */
    .category-badge {
        background: white;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
        color: #1e8e3e;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.markdown('<div class="main-header">🌴 Kerala Buy & Sell Marketplace</div>', unsafe_allow_html=True)

# ---------- OTP AUTHENTICATION FLOW ----------
if st.session_state.user is None:
    st.subheader("Secure OTP Login / Registration")
    
    with st.container(border=True):
        if not st.session_state.otp_sent:
            mobile = st.text_input("📱 Enter Mobile Number (10 digits)", max_chars=10, key="login_mobile")
            address = st.text_area("🏠 Enter Full Address (Required for new users)", key="login_address")
            
            if st.button("Send OTP", use_container_width=True):
                if len(mobile) == 10 and address.strip():
                    st.session_state.temp_mobile = mobile
                    st.session_state.temp_address = address
                    st.session_state.expected_otp = str(random.randint(1000, 9999))
                    st.session_state.otp_sent = True
                    st.rerun()
                else:
                    st.error("Please enter a valid 10-digit mobile number and your address.")
        else:
            st.info(f"OTP sent to {st.session_state.temp_mobile}. (For demo purposes, your OTP is: **{st.session_state.expected_otp}**)")
            entered_otp = st.text_input("Enter 4-digit OTP", max_chars=4)
            
            col1, col2 = st.columns(2)
            if col1.button("Verify & Login", use_container_width=True):
                if entered_otp == st.session_state.expected_otp:
                    mobile = st.session_state.temp_mobile
                    address = st.session_state.temp_address
                    
                    cursor.execute("SELECT * FROM users WHERE mobile=?", (mobile,))
                    user = cursor.fetchone()
                    
                    if not user:
                        # New User: Save to DB & Trigger Hidden WhatsApp
                        execute_query("INSERT INTO users(mobile, address, created_at) VALUES(?,?,?)", 
                                      (mobile, address, datetime.now()))
                        send_silent_whatsapp(mobile, address)
                        st.success("New account created! Admin notified silently.")
                        time.sleep(1)
                    
                    # Log them in
                    st.session_state.user = mobile
                    st.session_state.otp_sent = False
                    st.rerun()
                else:
                    st.error("Invalid OTP. Please try again.")
            
            if col2.button("Cancel / Back", use_container_width=True):
                st.session_state.otp_sent = False
                st.rerun()
                
    st.stop() # Stop rendering the rest of the app until logged in

# ---------- NAVIGATION ----------
st.markdown("---")

# Dynamically build menu based on role
nav_items = [("Home", "home"), ("Post Ad", "post"), ("My Ads", "myads"), ("Messages", "chat"), ("Tools", "tools")]

# HIDE ADMIN FROM NORMAL USERS
if st.session_state.user == ADMIN_NUMBER:
    nav_items.append(("Admin Dashboard", "admin"))

nav_items.append(("Logout", "logout"))

# Create dynamic columns based on menu length
nav_cols = st.columns(len(nav_items))

for col, (page_name, key) in zip(nav_cols, nav_items):
    if col.button(page_name, use_container_width=True):
        if key == "logout":
            st.session_state.user = None
            st.session_state.page = "home"
            st.session_state.otp_sent = False
            st.rerun()
        else:
            st.session_state.page = key
            st.rerun()
            
st.markdown("---")

# ================= PAGE ROUTING =================

# ---------- 1. HOME PAGE ----------
if st.session_state.page == "home":
    search = st.text_input("🔍 Search products, locations, or categories...")
    
    st.markdown("### Browse Categories")
    c_cols = st.columns(5)
    categories = ["Mobiles", "Electronics", "Vehicles", "Property", "Jobs"]
    for c_col, cat in zip(c_cols, categories):
        c_col.markdown(f'<div class="category-badge">{cat}</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 🔥 Latest Listings")
    
    query = "SELECT * FROM ads ORDER BY CASE boost WHEN 'Spotlight' THEN 1 WHEN 'Featured' THEN 2 WHEN 'Fast Sell' THEN 3 ELSE 4 END, id DESC"
    ads_df = pd.read_sql(query, conn)
    
    if search:
        search_term = search.lower()
        ads_df = ads_df[ads_df['title'].str.lower().str.contains(search_term) | 
                        ads_df['category'].str.lower().str.contains(search_term) | 
                        ads_df['location'].str.lower().str.contains(search_term)]
    
    if ads_df.empty:
        st.info("No listings found. Be the first to post!")
    else:
        for i, row in ads_df.iterrows():
            st.markdown('<div class="product-card">', unsafe_allow_html=True)
            img_col, info_col, action_col = st.columns([1.5, 3, 1])
            
            with img_col:
                if row["image_data"]:
                    st.image(base64.b64decode(row["image_data"]), use_container_width=True)
                else:
                    st.image("https://via.placeholder.com/300x200?text=No+Image", use_container_width=True)
            
            with info_col:
                boost_badge = f" ⭐ {row['boost']}" if row['boost'] != "Normal" else ""
                st.markdown(f"#### <span style='color:black;'>{row['title']}</span>{boost_badge}", unsafe_allow_html=True)
                st.markdown(f"<div class='price-tag'>₹{row['price']:,.2f}</div>", unsafe_allow_html=True)
                st.markdown(f"<p style='color:gray;'><b>Category:</b> {row['category']} | <b>📍 Location:</b> {row['location']}</p>", unsafe_allow_html=True)
                st.markdown(f"<p style='color:black;'>{row['description']}</p>", unsafe_allow_html=True)
            
            with action_col:
                whatsapp_link = f"https://wa.me/{row['user_mobile']}?text=Hi, I am interested in your ad: {row['title']}"
                st.markdown(f"<a href='{whatsapp_link}' target='_blank' style='background-color:#25D366; color:white; padding:8px 15px; border-radius:5px; text-decoration:none; display:inline-block; width:100%; text-align:center;'>💬 WhatsApp</a>", unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)

# ---------- 2. POST AD ----------
elif st.session_state.page == "post":
    st.subheader("📝 Create a New Listing")
    with st.form("post_ad_form"):
        col1, col2 = st.columns(2)
        title = col1.text_input("Ad Title*", required=True)
        price = col2.number_input("Price (₹)*", min_value=0.0, step=100.0)
        category = col1.selectbox("Category*", ["Mobiles", "Electronics", "Vehicles", "Property", "Jobs"])
        location = col2.text_input("Location*", required=True)
        desc = st.text_area("Detailed Description")
        uploaded_file = st.file_uploader("Upload Product Image", type=['jpg', 'jpeg', 'png'])
        boost = st.selectbox("Ad Visibility Package", ["Normal", "Fast Sell", "Featured", "Spotlight"])
        
        if st.form_submit_button("🚀 Publish Ad", use_container_width=True):
            if title and location:
                img_data = get_base64_of_image(uploaded_file)
                execute_query("INSERT INTO ads(user_mobile, title, price, category, location, description, image_data, boost, views, created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                              (st.session_state.user, title, price, category, location, desc, img_data, boost, 0, datetime.now()))
                st.success("🎉 Ad Posted Successfully!")
            else:
                st.error("Please fill in all mandatory fields (*)")

# ---------- 3. MY ADS ----------
elif st.session_state.page == "myads":
    st.subheader("📋 Manage My Ads")
    my_ads = pd.read_sql("SELECT * FROM ads WHERE user_mobile=?", conn, params=(st.session_state.user,))
    if my_ads.empty:
        st.info("You haven't posted any ads yet.")
    else:
        for i, row in my_ads.iterrows():
            with st.container(border=True):
                col1, col2 = st.columns([4, 1])
                col1.markdown(f"**{row['title']}** - ₹{row['price']}")
                if col2.button("❌ Delete", key=f"del_{row['id']}"):
                    execute_query("DELETE FROM ads WHERE id=?", (row['id'],))
                    st.success("Ad deleted.")
                    st.rerun()

# ---------- 4. MESSAGES ----------
elif st.session_state.page == "chat":
    st.subheader("💬 Message Center")
    tab1, tab2 = st.tabs(["📥 Inbox", "📤 Send Message"])
    with tab1:
        inbox = pd.read_sql("SELECT sender, message, created_at FROM messages WHERE receiver=? ORDER BY id DESC", conn, params=(st.session_state.user,))
        if inbox.empty:
            st.info("Your inbox is empty.")
        else:
            for i, row in inbox.iterrows():
                st.info(f"**From {row['sender']}** ({row['created_at'][:16]}):\n\n{row['message']}")
    with tab2:
        with st.form("send_msg_form"):
            receiver = st.text_input("Send to Mobile Number")
            msg = st.text_area("Type your message here...")
            if st.form_submit_button("Send Message"):
                if receiver and msg:
                    execute_query("INSERT INTO messages(sender, receiver, message, created_at) VALUES(?,?,?,?)",
                                  (st.session_state.user, receiver, msg, datetime.now()))
                    st.success("Message Sent Successfully!")

# ---------- 5. TOOLS ----------
elif st.session_state.page == "tools":
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("GST Calculator")
        with st.container(border=True):
            amount = st.number_input("Base Amount (₹)", min_value=0.0)
            rate = st.selectbox("GST Rate (%)", [5, 12, 18, 28])
            if amount > 0:
                st.metric("Total Bill (Amount + GST)", f"₹{(amount + (amount * rate / 100)):,.2f}")
    with col2:
        st.subheader("EMI Calculator")
        with st.container(border=True):
            loan = st.number_input("Loan Amount (₹)", min_value=0.0)
            int_rate = st.number_input("Annual Interest Rate (%)", min_value=0.0)
            years = st.number_input("Tenure (Years)", min_value=1)
            if loan > 0 and int_rate > 0:
                r = (int_rate / 12) / 100
                months = years * 12
                emi = loan * r * ((1 + r)**months) / (((1 + r)**months) - 1)
                st.metric("Estimated Monthly EMI", f"₹{emi:,.2f}")

# ---------- 6. ADMIN DASHBOARD (HIDDEN) ----------
elif st.session_state.page == "admin" and st.session_state.user == ADMIN_NUMBER:
    st.subheader("👑 Secret Admin Dashboard")
    users_df = pd.read_sql("SELECT * FROM users", conn)
    ads_df = pd.read_sql("SELECT * FROM ads", conn)
    
    m1, m2 = st.columns(2)
    m1.metric("Total Registered Users", len(users_df))
    m2.metric("Total Active Ads", len(ads_df))
    
    st.markdown("### User Database")
    st.dataframe(users_df, use_container_width=True)
    
    st.markdown("### Ads Database")
    st.dataframe(ads_df, use_container_width=True)
