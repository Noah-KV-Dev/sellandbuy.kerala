import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import base64

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="Kerala Buy & Sell", page_icon="🛒", layout="wide")

# ---------- DATABASE SETUP ----------
@st.cache_resource
def init_db():
    conn = sqlite3.connect("marketplace.db", check_same_thread=False)
    cursor = conn.cursor()
    
    # Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mobile TEXT UNIQUE,
        created_at TEXT
    )""")
    
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

# ---------- HELPER FUNCTIONS ----------
def get_base64_of_image(upload_file):
    if upload_file is not None:
        return base64.b64encode(upload_file.read()).decode()
    return ""

def execute_query(query, params=()):
    cursor.execute(query, params)
    conn.commit()

# ---------- SESSION STATE ----------
if "page" not in st.session_state:
    st.session_state.page = "home"
if "user" not in st.session_state:
    st.session_state.user = None

# ---------- PROFESSIONAL CSS THEME ----------
st.markdown("""
<style>
    /* Modern Background & Typography */
    .stApp { background-color: #f4f7f6; }
    
    /* Sleek Header */
    .main-header {
        background: linear-gradient(135deg, #0f9b0f, #006b38);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        font-size: 32px;
        font-weight: 800;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.1);
        margin-bottom: 25px;
    }
    
    /* Product Cards */
    .product-card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        transition: transform 0.2s;
        border: 1px solid #e0e0e0;
    }
    .product-card:hover { transform: translateY(-3px); box-shadow: 0px 6px 15px rgba(0,0,0,0.1); }
    
    /* Price Tag */
    .price-tag {
        color: #e65100;
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
        color: #006b38;
        border: 2px solid #006b38;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.1);
    }
    
    /* Buttons */
    .btn-chat {
        background-color: #25D366;
        color: white !important;
        padding: 8px 15px;
        border-radius: 5px;
        text-decoration: none;
        font-weight: bold;
        display: inline-block;
        text-align: center;
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.markdown('<div class="main-header">🌴 Kerala Buy & Sell Marketplace</div>', unsafe_allow_html=True)

# ---------- AUTHENTICATION ----------
if st.session_state.user is None:
    st.subheader("Secure Login / Registration")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        mobile = st.text_input("📱 Enter Mobile Number (10 digits)", max_chars=10)
        consent = st.checkbox("Notify admin on WhatsApp when I sign up")
        
        if st.button("Login / Signup", use_container_width=True):
            if len(mobile) >= 10:
                cursor.execute("SELECT * FROM users WHERE mobile=?", (mobile,))
                user = cursor.fetchone()
                
                if not user:
                    execute_query("INSERT INTO users(mobile, created_at) VALUES(?,?)", (mobile, datetime.now()))
                    st.success("New account created successfully!")
                    
                    if consent:
                        msg = f"New user signup on Kerala Buy & Sell: {mobile}"
                        admin_link = f"https://wa.me/918590304889?text={msg}"
                        st.markdown(f"[🔔 Click here to notify Admin via WhatsApp]({admin_link})")
                
                st.session_state.user = mobile
                st.success("Login successful! Redirecting...")
                st.rerun()
            else:
                st.error("Please enter a valid 10-digit mobile number.")
    st.stop()

# ---------- NAVIGATION ----------
st.markdown("---")
nav_cols = st.columns(7)
pages = ["Home", "Post Ad", "My Ads", "Messages", "Tools", "Admin", "Logout"]
page_keys = ["home", "post", "myads", "chat", "tools", "admin", "logout"]

for col, page_name, key in zip(nav_cols, pages, page_keys):
    if col.button(page_name, use_container_width=True):
        if key == "logout":
            st.session_state.user = None
            st.rerun()
        else:
            st.session_state.page = key
st.markdown("---")

# ================= PAGE ROUTING =================

# ---------- 1. HOME PAGE ----------
if st.session_state.page == "home":
    # Search Bar
    search = st.text_input("🔍 Search products, locations, or categories...")
    
    # Categories
    st.markdown("### Browse Categories")
    c_cols = st.columns(5)
    categories = ["Mobiles", "Electronics", "Vehicles", "Property", "Jobs"]
    for c_col, cat in zip(c_cols, categories):
        c_col.markdown(f'<div class="category-badge">{cat}</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 🔥 Latest Listings")
    
    # Fetch and filter ads
    query = """
    SELECT * FROM ads 
    ORDER BY 
        CASE boost 
            WHEN 'Spotlight' THEN 1 
            WHEN 'Featured' THEN 2 
            WHEN 'Fast Sell' THEN 3 
            ELSE 4 
        END, 
        id DESC
    """
    ads_df = pd.read_sql(query, conn)
    
    if search:
        # Professional dynamic filtering
        search_term = search.lower()
        ads_df = ads_df[
            ads_df['title'].str.lower().str.contains(search_term) |
            ads_df['category'].str.lower().str.contains(search_term) |
            ads_df['location'].str.lower().str.contains(search_term)
        ]
    
    if ads_df.empty:
        st.info("No listings found. Be the first to post!")
    else:
        for i, row in ads_df.iterrows():
            st.markdown('<div class="product-card">', unsafe_allow_html=True)
            img_col, info_col, action_col = st.columns([1.5, 3, 1])
            
            # Display Image (Base64 or Fallback)
            with img_col:
                if row["image_data"]:
                    st.image(base64.b64decode(row["image_data"]), use_container_width=True)
                else:
                    st.image("https://via.placeholder.com/300x200?text=No+Image", use_container_width=True)
            
            # Info
            with info_col:
                boost_badge = f" ⭐ {row['boost']}" if row['boost'] != "Normal" else ""
                st.markdown(f"#### {row['title']}{boost_badge}")
                st.markdown(f"<div class='price'>₹{row['price']:,.2f}</div>", unsafe_allow_html=True)
                st.write(f"**Category:** {row['category']} | **📍 Location:** {row['location']}")
                st.caption(row['description'])
            
            # Actions
            with action_col:
                whatsapp_link = f"https://wa.me/{row['user_mobile']}?text=Hi, I am interested in your ad: {row['title']}"
                st.markdown(f"<a href='{whatsapp_link}' target='_blank' class='btn-chat'>💬 WhatsApp</a>", unsafe_allow_html=True)
                st.caption(f"Seller: {row['user_mobile']}")
            
            st.markdown("</div>", unsafe_allow_html=True)

    # Map Section (Only on Home)
    st.markdown("### 🗺️ Listings Map (Kerala)")
    map_data = pd.DataFrame({"lat": [11.2588, 9.9312, 8.5241], "lon": [75.7804, 76.2673, 76.9366]})
    st.map(map_data)

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
        
        # New Feature: Real Image Upload
        st.write("Upload Product Image")
        uploaded_file = st.file_uploader("Choose an image file", type=['jpg', 'jpeg', 'png'])
        
        boost = st.selectbox("Ad Visibility Package", ["Normal", "Fast Sell", "Featured", "Spotlight"])
        
        submitted = st.form_submit_button("🚀 Publish Ad", use_container_width=True)
        
        if submitted:
            if title and location:
                img_data = get_base64_of_image(uploaded_file)
                execute_query("""
                INSERT INTO ads(user_mobile, title, price, category, location, description, image_data, boost, views, created_at)
                VALUES(?,?,?,?,?,?,?,?,?,?)
                """, (st.session_state.user, title, price, category, location, desc, img_data, boost, 0, datetime.now()))
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
            with st.container():
                st.markdown(f"**{row['title']}** - ₹{row['price']}")
                col1, col2 = st.columns([1, 5])
                if col1.button("❌ Delete", key=f"del_{row['id']}"):
                    execute_query("DELETE FROM ads WHERE id=?", (row['id'],))
                    st.success("Ad deleted. Please refresh.")
                    st.rerun()
                st.markdown("---")

# ---------- 4. MESSAGES (INBOX & SEND) ----------
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
                else:
                    st.error("Please fill out both fields.")

# ---------- 5. TOOLS (GST & EMI) ----------
elif st.session_state.page == "tools":
    st.subheader("🧮 Financial Tools")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### GST Calculator")
        with st.container(border=True):
            amount = st.number_input("Base Amount (₹)", min_value=0.0)
            rate = st.selectbox("GST Rate (%)", [5, 12, 18, 28])
            if amount > 0:
                gst = amount * rate / 100
                st.metric("Total GST Amount", f"₹{gst:,.2f}")
                st.metric("Total Bill (Amount + GST)", f"₹{(amount + gst):,.2f}")

    with col2:
        st.markdown("#### EMI Calculator")
        with st.container(border=True):
            loan = st.number_input("Loan Amount (₹)", min_value=0.0)
            int_rate = st.number_input("Annual Interest Rate (%)", min_value=0.0)
            years = st.number_input("Tenure (Years)", min_value=1)
            
            if loan > 0 and int_rate > 0:
                r = (int_rate / 12) / 100
                months = years * 12
                emi = loan * r * ((1 + r)**months) / (((1 + r)**months) - 1)
                st.metric("Estimated Monthly EMI", f"₹{emi:,.2f}")
                st.metric("Total Interest Payable", f"₹{(emi*months - loan):,.2f}")

# ---------- 6. ADMIN DASHBOARD ----------
elif st.session_state.page == "admin":
    st.subheader("👑 Admin Dashboard")
    
    users_count = pd.read_sql("SELECT COUNT(*) c FROM users", conn).iloc[0]["c"]
    ads_count = pd.read_sql("SELECT COUNT(*) c FROM ads", conn).iloc[0]["c"]
    msg_count = pd.read_sql("SELECT COUNT(*) c FROM messages", conn).iloc[0]["c"]
    
    # Top KPI Metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Registered Users", users_count)
    m2.metric("Total Active Ads", ads_count)
    m3.metric("Platform Messages Sent", msg_count)
    
    st.markdown("---")
    
    # Graphical Data
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Ads by Category**")
        cat_data = pd.read_sql("SELECT category, COUNT(*) as count FROM ads GROUP BY category", conn)
        if not cat_data.empty:
            st.bar_chart(cat_data.set_index('category'))
        else:
            st.write("No data available yet.")
            
    with col2:
        st.markdown("**Recent Ads Table**")
        recent_ads = pd.read_sql("SELECT title, category, price, location FROM ads ORDER BY id DESC LIMIT 10", conn)
        st.dataframe(recent_ads, use_container_width=True)
