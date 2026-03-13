import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import base64
import time

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="Kerala Buy & Sell", page_icon="🌴", layout="wide")

# ---------- CONSTANTS ----------
# Set this to your phone number, which will serve as the unique admin login ID
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
    
    # Try adding columns for backward compatibility if the DB already exists
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN address TEXT")
        conn.commit()
    except sqlite3.OperationalError: pass
    
    # Ads Table (Updated to 'image_base64_json' for multiple images)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ads(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_mobile TEXT,
        title TEXT,
        price REAL,
        category TEXT,
        location TEXT,
        description TEXT,
        image_base64_json TEXT,  
        boost TEXT,
        views INTEGER,
        status TEXT,
        created_at TEXT
    )""")

    # Try adding status column for existing databases
    try:
        cursor.execute("ALTER TABLE ads ADD COLUMN status TEXT DEFAULT 'Approved'")
        conn.commit()
    except sqlite3.OperationalError: pass
    
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

# NEW FEATURE: Encode multiple images as a JSON list of Base64 strings
def get_images_as_base64(upload_files):
    if upload_files:
        encoded_images = []
        for file in upload_files:
            encoded_images.append(base64.b64encode(file.read()).decode())
        import json
        return json.dumps(encoded_images)
    return None

# Placeholder function for sending a WhatsApp message via API (Twilio, Meta, etc.)
def send_background_whatsapp(new_user_mobile, new_user_address):
    """
    To make this hidden from the user, you must use a background backend service 
    like the WhatsApp Business API (via providers like Twilio or Meta).
    """
    message = f"🚨 New User Registered on Kerala Buy & Sell!\n\nMobile: {new_user_mobile}\nAddress: {new_user_address}"
    # This keeps the functionality separate so it doesn't break the user experience
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

# ---------- THEME AND CUSTOM CSS ----------
# Recreating the Clean White, Green, and Orange theme from the photos
st.markdown("""
<style>
    /* White, modern background */
    .stApp {
        background-color: #f7f9fb;
    }
    
    /* Sleek Main Header resembling the top-right photo */
    .main-header {
        background: white;
        padding: 15px 30px;
        border-radius: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.05);
        margin-bottom: 25px;
        border: 1px solid #e1e8ed;
    }
    .main-header h1 {
        color: #1a1a1a !important;
        font-weight: 800;
        font-size: 28px;
        margin: 0;
    }
    
    /* Modern Input Styling */
    div[data-baseweb="input"] {
        border-radius: 8px !important;
    }
    
    /* Login & Ad Card styles based on the photos */
    .product-card {
        background: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.05);
        margin-bottom: 15px;
        border: 1px solid #f0f2f6;
        transition: 0.2s;
    }
    .product-card:hover {
        transform: translateY(-2px);
        box-shadow: 0px 5px 15px rgba(0,0,0,0.1);
    }
    
    .price-tag {
        color: #e65c00;
        font-size: 20px;
        font-weight: 800;
        margin: 5px 0;
    }
    
    /* Green, pill-shaped category buttons from the mobile design */
    .category-pill {
        background-color: white;
        color: #1e8e3e;
        border: 2px solid #1e8e3e;
        padding: 10px 18px;
        border-radius: 30px;
        text-align: center;
        font-weight: bold;
        box-shadow: 0px 2px 4px rgba(0,0,0,0.05);
        display: inline-block;
        margin: 5px;
    }
    
    /* Green buttons matching the 'Chat' button from the photo */
    .btn-chat {
        background-color: #1e8e3e;
        color: white !important;
        padding: 8px 15px;
        border-radius: 6px;
        text-decoration: none;
        font-weight: bold;
        display: block;
        text-align: center;
        width: 100%;
        margin-top: 10px;
    }
    
    /* Orange buttons matching 'Sell Now' from the photo */
    .btn-sell {
        background-color: #ff6a00;
        color: white !important;
        padding: 8px 15px;
        border-radius: 6px;
        text-decoration: none;
        font-weight: bold;
        display: block;
        text-align: center;
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# ---------- HEADER (RECREATED FROM PHOTO) ----------
st.markdown(f'<div class="main-header"><h1>Kerala Buy & Sell</h1><span style="color:gray;">Kerala\'s No.1 Classifieds Site</span></div>', unsafe_allow_html=True)

# ---------- AUTHENTICATION FLOW (LOGIN/SIGNUP WITH OTP) ----------
if st.session_state.user is None:
    st.subheader("Login / Registration")
    
    with st.container(border=True):
        col1, col2 = st.columns(2)
        
        # New Feature: If OTP has been sent, show OTP input field
        if st.session_state.otp_sent:
            with col1:
                st.info(f"An OTP has been sent to {st.session_state.temp_mobile}. (Demo OTP: **{st.session_state.expected_otp}**)")
                entered_otp = st.text_input("Enter 4-Digit OTP", max_chars=4, key="otp_input")
                
                b_cols = st.columns(2)
                # Verify OTP and log user in
                if b_cols[0].button("Verify & Login", use_container_width=True):
                    if entered_otp == st.session_state.expected_otp:
                        mobile = st.session_state.temp_mobile
                        address = st.session_state.temp_address
                        
                        cursor.execute("SELECT * FROM users WHERE mobile=?", (mobile,))
                        user = cursor.fetchone()
                        
                        # New user, register, and silently notify admin
                        if not user:
                            execute_query("INSERT INTO users(mobile, address, created_at) VALUES(?,?,?)", (mobile, address, datetime.now()))
                            send_background_whatsapp(mobile, address)
                            st.success("Registration successful!")
                            time.sleep(1)
                        
                        st.session_state.user = mobile
                        st.session_state.otp_sent = False
                        st.rerun()
                    else:
                        st.error("Invalid OTP. Please try again.")
                
                # Option to cancel and return to inputting number
                if b_cols[1].button("Back", use_container_width=True):
                    st.session_state.otp_sent = False
                    st.rerun()
        
        # Initial login step: Input Mobile and Address
        else:
            with col1:
                mobile = st.text_input("📱 Mobile Number (10 digits)", max_chars=10, key="login_mobile")
                address = st.text_area("🏠 Address (Required for new users)", key="login_address")
                
                # Check for existing user
                cursor.execute("SELECT * FROM users WHERE mobile=?", (mobile,))
                user_exists = cursor.fetchone()
                
                if st.button("Get OTP", use_container_width=True):
                    if len(mobile) == 10:
                        if not user_exists and not address.strip():
                            st.warning("Address is mandatory for new users.")
                        else:
                            st.session_state.temp_mobile = mobile
                            st.session_state.temp_address = address if not user_exists else ""
                            import random
                            st.session_state.expected_otp = str(random.randint(1000, 9999))
                            st.session_state.otp_sent = True
                            st.rerun()
                    else:
                        st.error("Please enter a valid 10-digit mobile number.")
                        
            with col2:
                # Welcome image matching the design
                st.image("https://images.unsplash.com/photo-1599305090598-fe179d501c27?q=80&w=600", use_container_width=True)
                
    st.stop() # Prevents other content from loading until logged in

# ---------- DYNAMIC NAVIGATION (HIDING ADMIN FROM USERS) ----------
st.markdown("---")
nav_items = [("Home", "home"), ("Post Ad", "post"), ("My Ads", "myads"), ("Messages", "chat"), ("Tools", "tools")]

# Add Admin Dashboard ONLY for the specific admin number
if st.session_state.user == ADMIN_NUMBER:
    nav_items.append(("👑 Admin Dashboard", "admin"))

nav_items.append(("Logout", "logout"))
nav_cols = st.columns(len(nav_items))

for col, (page_name, key) in zip(nav_cols, nav_items):
    if col.button(page_name, use_container_width=True):
        if key == "logout":
            st.session_state.user = None
            st.session_state.otp_sent = False
            st.session_state.page = "home"
            st.rerun()
        else:
            st.session_state.page = key
            st.rerun()
st.markdown("---")

# ================= PAGE ROUTING =================

# ---------- 1. HOME PAGE ----------
if st.session_state.page == "home":
    # Main search bar and banner matching the design
    st.markdown('<div class="product-card" style="text-align:center;">', unsafe_allow_html=True)
    st.image("https://images.unsplash.com/photo-1582650849208-41c6e118c77b?q=80&w=1200", use_container_width=True, caption="Buy & Sell Easily in Kerala")
    search = st.text_input("🔍 Search products, locations, categories...", key="main_search")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Modern category pillars matching the mobile and desktop photo
    st.markdown("### Browse Categories")
    categories = ["Mobiles", "Electronics", "Vehicles", "Property", "Jobs"]
    c_cols = st.columns(len(categories))
    for c_col, cat in zip(c_cols, categories):
        c_col.markdown(f'<div class="category-pill">{cat}</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 🔥 Latest Approved Listings")
    
    # Ad cards style from photos. Showing only approved ads.
    query = "SELECT * FROM ads WHERE status='Approved' ORDER BY CASE boost WHEN 'Spotlight' THEN 1 WHEN 'Featured' THEN 2 WHEN 'Fast Sell' THEN 3 ELSE 4 END, id DESC"
    ads_df = pd.read_sql(query, conn)
    
    if search:
        ads_df = ads_df[ads_df['title'].str.lower().str.contains(search.lower()) | 
                        ads_df['category'].str.lower().str.contains(search.lower()) | 
                        ads_df['location'].str.lower().str.contains(search.lower())]
    
    if ads_df.empty:
        st.info("No listings found matching your criteria.")
    else:
        for i, row in ads_df.iterrows():
            st.markdown('<div class="product-card">', unsafe_allow_html=True)
            img_col, info_col, action_col = st.columns([1.5, 3, 1])
            
            with img_col:
                if row["image_base64_json"]:
                    import json
                    images = json.loads(row["image_base64_json"])
                    if images:
                        st.image(base64.b64decode(images[0]), use_container_width=True)
                    else:
                        st.image("https://via.placeholder.com/300x200?text=No+Image", use_container_width=True)
                else:
                    st.image("https://via.placeholder.com/300x200?text=No+Image", use_container_width=True)
            
            with info_col:
                boost_badge = f" ⭐ {row['boost']}" if row['boost'] != "Normal" else ""
                st.markdown(f"#### <span style='color:black;'>{row['title']}</span>{boost_badge}", unsafe_allow_html=True)
                st.markdown(f"<div class='price-tag'>₹{row['price']:,.2f}</div>", unsafe_allow_html=True)
                st.markdown(f"<p style='color:gray;'>{row['category']} | {row['location']}</p>", unsafe_allow_html=True)
                st.markdown(f"<p style='color:black;'>{row['description']}</p>", unsafe_allow_html=True)
            
            with action_col:
                whatsapp_link = f"https://wa.me/{row['user_mobile']}?text=Hi, I am interested in your ad: {row['title']}"
                st.markdown(f"<a href='{whatsapp_link}' target='_blank' class='btn-chat'>💬 WhatsApp</a>", unsafe_allow_html=True)
                st.caption(f"Seller: {row['user_mobile']}")
            
            st.markdown("</div>", unsafe_allow_html=True)

# ---------- 2. POST AD (WITH MULTI-IMAGE UPLOAD) ----------
elif st.session_state.page == "post":
    st.subheader("🚀 Post Your Ad")
    
    with st.form("post_ad_form"):
        col1, col2 = st.columns(2)
        title = col1.text_input("Ad Title*", required=True)
        price = col2.number_input("Price (₹)*", min_value=0.0, step=100.0)
        category = col1.selectbox("Category*", ["Mobiles", "Electronics", "Vehicles", "Property", "Jobs"])
        location = col2.text_input("Location*", required=True)
        desc = st.text_area("Detailed Description")
        
        # New Feature: Upload Multiple Images
        uploaded_files = st.file_uploader("Upload Product Images (Max 5)", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)
        
        boost = st.selectbox("Boost Your Ad", ["Normal", "Fast Sell", "Featured", "Spotlight"])
        submitted = st.form_submit_button("Publish Ad")
        
        if submitted:
            if not uploaded_files:
                st.error("Please upload at least one image.")
            elif len(uploaded_files) > 5:
                st.error("You can upload a maximum of 5 images.")
            else:
                img_data_json = get_images_as_base64(uploaded_files)
                execute_query("INSERT INTO ads(user_mobile, title, price, category, location, description, image_base64_json, boost, views, status, created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                              (st.session_state.user, title, price, category, location, desc, img_data_json, boost, 0, 'Approved', datetime.now()))
                st.success("🎉 Ad Posted Successfully!")

# ---------- 3. MY ADS (AD MANAGEMENT) ----------
elif st.session_state.page == "myads":
    st.subheader("📋 Manage My Ads")
    my_ads = pd.read_sql("SELECT * FROM ads WHERE user_mobile=?", conn, params=(st.session_state.user,))
    if my_ads.empty:
        st.info("You haven't posted any ads yet.")
    else:
        for i, row in my_ads.iterrows():
            with st.container(border=True):
                col1, col2 = st.columns([4, 1])
                status_color = "#1e8e3e" if row['status'] == 'Approved' else "#ffc107" if row['status'] == 'Pending' else "#dc3545"
                col1.markdown(f"**{row['title']}** - ₹{row['price']} | <span style='color:{status_color}; font-weight:bold;'>{row['status']}</span>", unsafe_allow_html=True)
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
            receiver = st.text_input("Recipient Mobile Number")
            msg = st.text_area("Type your message here...")
            if st.form_submit_button("Send Message"):
                if receiver and msg:
                    execute_query("INSERT INTO messages(sender, receiver, message, created_at) VALUES(?,?,?,?)",
                                  (st.session_state.user, receiver, msg, datetime.now()))
                    st.success("Message Sent Successfully!")

# ---------- 5. TOOLS ----------
elif st.session_state.page == "tools":
    st.subheader("🧮 Calculator Tools")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### GST Calculator")
        with st.container(border=True):
            amount = st.number_input("Base Amount (₹)", min_value=0.0)
            rate = st.selectbox("GST Rate (%)", [5, 12, 18, 28])
            if amount > 0:
                gst_amount = amount * rate / 100
                st.metric("Total GST Amount", f"₹{gst_amount:,.2f}")
                st.metric("Total Bill (Amount + GST)", f"₹{(amount + gst_amount):,.2f}")
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

# ---------- 6. ADMIN DASHBOARD (RECREATED FROM BOTTOM-LEFT PHOTO) ----------
elif st.session_state.page == "admin" and st.session_state.user == ADMIN_NUMBER:
    st.subheader("👑 Secret Admin Dashboard")
    
    # KPIs from the Admin Panel photo
    users_df = pd.read_sql("SELECT * FROM users", conn)
    ads_df = pd.read_sql("SELECT * FROM ads", conn)
    
    m1, m2, m3, m4 = st.columns(4)
    # Style the columns based on the green, orange, blue, and red from the photo
    m1.markdown(f'<div style="background-color:#1e8e3e; color:white; padding:15px; border-radius:10px; text-align:center;"><p>Total Users</p><h2>{len(users_df)}</h2></div>', unsafe_allow_html=True)
    m2.markdown(f'<div style="background-color:#ff6a00; color:white; padding:15px; border-radius:10px; text-align:center;"><p>Total Listings</p><h2>{len(ads_df)}</h2></div>', unsafe_allow_html=True)
    m3.markdown(f'<div style="background-color:#007bff; color:white; padding:15px; border-radius:10px; text-align:center;"><p>Approved Ads</p><h2>{len(ads_df[ads_df["status"]=="Approved"])}</h2></div>', unsafe_allow_html=True)
    m4.markdown(f'<div style="background-color:#dc3545; color:white; padding:15px; border-radius:10px; text-align:center;"><p>Pending Ads</p><h2>{len(ads_df[ads_df["status"]=="Pending"])}</h2></div>', unsafe_allow_html=True)
    
    st.markdown("### Latest Listings Management")
    # Interactive dataframe to review/approve/reject ads based on photo table
    ad_table = ads_df[['id', 'title', 'category', 'price', 'user_mobile', 'location', 'status']]
    
    selected_ad_id = st.selectbox("Select Ad ID to Review", ad_table['id'].tolist())
    
    # Review single ad details
    if selected_ad_id:
        ad_details = ads_df[ads_df['id'] == selected_ad_id].iloc[0]
        st.write(f"**User**: {ad_details['user_mobile']} | **Location**: {ad_details['location']} | **Status**: {ad_details['status']}")
        
        c1, c2, c3 = st.columns(3)
        if c1.button("✅ Approve", key="appr"):
            execute_query("UPDATE ads SET status='Approved' WHERE id=?", (selected_ad_id,))
            st.success(f"Ad {selected_ad_id} Approved.")
            st.rerun()
        if c2.button("🚫 Reject", key="rej"):
            execute_query("UPDATE ads SET status='Rejected' WHERE id=?", (selected_ad_id,))
            st.warning(f"Ad {selected_ad_id} Rejected.")
            st.rerun()
        if c3.button("🗑️ Delete", key="del_admin"):
            execute_query("DELETE FROM ads WHERE id=?", (selected_ad_id,))
            st.error(f"Ad {selected_ad_id} Deleted.")
            st.rerun()
            
    # Display the full database tables
    st.markdown("### User Database")
    st.dataframe(users_df, use_container_width=True)
    
    st.markdown("### Ads Database")
    st.dataframe(ads_df, use_container_width=True)
