import streamlit as st 
import sqlite3 
import pandas as pd 
from datetime import datetime 
import base64 
from PIL import Image 
import io 
 
# ---------- PAGE CONFIG ---------- 
st.set_page_config(page_title="Kerala Buy & Sell", layout="wide", initial_sidebar_state="collapsed") 
 
# ---------- DATABASE ---------- 
conn = sqlite3.connect("marketplace.db", check_same_thread=False) 
cursor = conn.cursor() 
 
# Users Table 
cursor.execute(""" 
CREATE TABLE IF NOT EXISTS users( 
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    mobile TEXT UNIQUE, 
    created_at TEXT 
) 
""") 
 
# Ads Table (Added status column) 
cursor.execute(""" 
CREATE TABLE IF NOT EXISTS ads( 
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    user_mobile TEXT, 
    title TEXT, 
    price REAL, 
    category TEXT, 
    location TEXT, 
    description TEXT, 
    image TEXT, 
    boost TEXT, 
    views INTEGER, 
    status TEXT DEFAULT 'Available', 
    created_at TEXT 
) 
""") 
 
# Messages Table 
cursor.execute(""" 
CREATE TABLE IF NOT EXISTS messages( 
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    sender TEXT, 
    receiver TEXT, 
    message TEXT, 
    created_at TEXT 
) 
""") 
 
# Migration: Add status column if it doesn't exist (for existing dbs) 
try: 
    cursor.execute("ALTER TABLE ads ADD COLUMN status TEXT DEFAULT 'Available'") 
except sqlite3.OperationalError: 
    pass # Column already exists 
 
conn.commit() 
 
# ---------- SESSION ---------- 
if "page" not in st.session_state: 
    st.session_state.page = "home" 
 
if "user" not in st.session_state: 
    st.session_state.user = None 
 
if "selected_category" not in st.session_state: 
    st.session_state.selected_category = "All" 
 
# ---------- GRASS THEME ---------- 
st.markdown(""" 
<style> 
    body { 
        background: linear-gradient(-45deg, #1e8e3e, #2ecc71, #27ae60, #16a085); 
        background-size: 400% 400%; 
        animation: grass 15s ease infinite; 
        color: #333; 
    } 
    @keyframes grass { 
        0% { background-position: 0% 50% } 
        50% { background-position: 100% 50% } 
        100% { background-position: 0% 50% } 
    } 
    .header { 
        background: #1e8e3e; 
        padding: 20px; 
        border-radius: 12px; 
        color: white; 
        font-size: 32px; 
        font-weight: bold; 
        text-align: center; 
        margin-bottom: 20px; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.2); 
    } 
    .card { 
        background: white; 
        padding: 20px; 
        border-radius: 15px; 
        box-shadow: 0px 4px 12px rgba(0,0,0,0.15); 
        margin-bottom: 20px; 
        transition: transform 0.2s; 
    } 
    .card:hover { 
        transform: translateY(-5px); 
    } 
    .price { 
        color: #d35400; 
        font-size: 24px; 
        font-weight: bold; 
    } 
    .greenbtn { 
        background: #1e8e3e; 
        color: white; 
        padding: 10px; 
        border-radius: 8px; 
        text-align: center; 
        display: block; 
        text-decoration: none; 
        font-weight: bold; 
    } 
    .orangebtn { 
        background: #e67e22; 
        color: white; 
        padding: 10px; 
        border-radius: 8px; 
        text-align: center; 
        display: block; 
        text-decoration: none; 
        font-weight: bold; 
    } 
    .redbtn { 
        background: #c0392b; 
        color: white; 
        padding: 10px; 
        border-radius: 8px; 
        text-align: center; 
        display: block; 
        text-decoration: none; 
        font-weight: bold; 
    } 
    .category-card { 
        background: white; 
        padding: 15px; 
        border-radius: 10px; 
        text-align: center; 
        box-shadow: 0px 2px 8px rgba(0,0,0,0.1); 
        cursor: pointer; 
        border: 2px solid transparent; 
    } 
    .category-card.active { 
        border: 2px solid #1e8e3e; 
        background: #e8f5e9; 
    } 
    .stTextInput>div>div>input, .stTextArea textarea { 
        border-radius: 10px; 
    } 
    .sold-badge { 
        background: #e74c3c; 
        color: white; 
        padding: 5px 10px; 
        border-radius: 5px; 
        font-weight: bold; 
        font-size: 12px; 
        display: inline-block; 
        margin-bottom: 5px; 
    } 
</style> 
""", unsafe_allow_html=True) 
 
# ---------- HEADER ---------- 
st.markdown('<div class="header">🌴 Kerala Buy & Sell 🌴</div>', unsafe_allow_html=True) 
 
# ---------- LOGIN ---------- 
if st.session_state.user is None: 
    with st.container(): 
        st.subheader("📱 Mobile Login") 
        col1, col2 = st.columns([2, 1]) 
        with col1: 
            mobile = st.text_input("Enter 10 Digit Mobile Number", placeholder="9876543210") 
        with col2: 
            st.write("") # Spacer 
            st.write("") # Spacer 
            consent = st.checkbox("Notify Admin on WhatsApp") 
         
        if st.button("Login / Signup", use_container_width=True): 
            if len(mobile) >= 10: 
                cursor.execute("SELECT * FROM users WHERE mobile=?", (mobile,)) 
                user = cursor.fetchone() 
 
                if not user: 
                    cursor.execute( 
                        "INSERT INTO users(mobile, created_at) VALUES(?,?)", 
                        (mobile, datetime.now()) 
                    ) 
                    conn.commit() 
                    if consent: 
                        msg = f"New user signup: {mobile}" 
                        admin_link = f"https://wa.me/918590304889?text={msg}" 
                        st.markdown(f"[Click here to Notify Admin]({admin_link})") 
 
                st.session_state.user = mobile 
                st.rerun() 
            else: 
                st.error("Please enter a valid mobile number") 
 
# ---------- MENU ---------- 
if st.session_state.user: 
    # Top Navigation Bar 
    cols = st.columns(7) 
    pages = ["Home", "Post Ad", "My Ads", "Messages", "GST", "EMI", "Admin"] 
    icons = ["🏠", "📝", "📂", "💬", "🧾", "🏦", "⚙️"] 
     
    for i, (col, page, icon) in enumerate(zip(cols, pages, icons)): 
        with col: 
            # Highlight current page 
            btn_type = "primary" if st.session_state.page == page.lower() else "secondary" 
            if st.button(f"{icon} {page}", key=page, use_container_width=True): 
                st.session_state.page = page.lower() 
                st.rerun() 
 
    st.write("---") 
 
# ---------- LOGIC: SEARCH & FILTER ---------- 
# Initialize query params 
search_term = st.session_state.get("search_term", "") 
selected_cat = st.session_state.selected_category 
 
# ---------- RENDER PAGES ---------- 
 
# --- POST AD PAGE --- 
if st.session_state.page == "post ad": 
    st.subheader("📝 Post New Ad") 
     
    with st.form("post_ad_form"): 
        col1, col2 = st.columns(2) 
         
        with col1: 
            title = st.text_input("Title *") 
            category = st.selectbox("Category", ["Mobiles", "Electronics", "Vehicles", "Property", "Jobs", "Others"]) 
            price = st.number_input("Price (₹)", min_value=0.0) 
         
        with col2: 
            location = st.text_input("Location *") 
            desc = st.text_area("Description") 
            image_file = st.file_uploader("Upload Image", type=['jpg', 'png', 'jpeg']) 
         
        boost = st.selectbox("Boost Your Ad", ["Normal", "Fast Sell", "Featured", "Spotlight"]) 
         
        submitted = st.form_submit_button("Publish Ad", use_container_width=True) 
         
        if submitted: 
            if not title or not location: 
                st.error("Title and Location are required.") 
            else: 
                # Handle Image Upload 
                img_str = "" 
                if image_file: 
                    img = Image.open(image_file) 
                    # Resize to save space 
                    img.thumbnail((400, 400))  
                    buf = io.BytesIO() 
                    img.save(buf, format="JPEG") 
                    byte_data = buf.getvalue() 
                    img_str = base64.b64encode(byte_data).decode('utf-8') 
                 
                cursor.execute(""" 
                INSERT INTO ads( 
                    user_mobile, title, price, category, 
                    location, description, image, boost, views, created_at 
                ) VALUES(?,?,?,?,?,?,?,?,?,?) 
                """, (st.session_state.user, title, price, category, 
                      location, desc, img_str, boost, 0, datetime.now())) 
                 
                conn.commit() 
                st.success("✅ Ad Published Successfully!") 
                st.balloons() 
 
# --- MY ADS PAGE --- 
elif st.session_state.page == "my ads": 
    st.subheader("📂 My Listings") 
     
    user_ads = pd.read_sql( 
        "SELECT * FROM ads WHERE user_mobile=? ORDER BY id DESC",  
        conn,  
        params=(st.session_state.user,) 
    ) 
 
    if user_ads.empty: 
        st.info("You haven't posted any ads yet.") 
    else: 
        for i, row in user_ads.iterrows(): 
            st.markdown('<div class="card">', unsafe_allow_html=True) 
            col1, col2 = st.columns([1, 3]) 
             
            if row["image"]: 
                try: 
                    img_data = base64.b64decode(row["image"]) 
                    col1.image(img_data, width=100) 
                except: 
                    col1.warning("Img Error") 
             
            with col2: 
                status_badge = f"<span class='sold-badge'>{row['status']}</span>" if row['status'] == 'Sold' else "" 
                st.markdown(f"### {row['title']} {status_badge}", unsafe_allow_html=True) 
                st.write(f"Price: ₹{row['price']} | Views: {row['views']}") 
                st.write(f"Category: {row['category']} | Boost: {row['boost']}") 
 
            # Action Buttons 
            c1, c2, c3 = st.columns(3) 
            if c1.button(f"🗑️ Delete", key=f"del_{row['id']}"): 
                cursor.execute("DELETE FROM ads WHERE id=?", (row['id'],)) 
                conn.commit() 
                st.rerun() 
             
            if row['status'] == 'Available': 
                if c2.button(f"✅ Mark Sold", key=f"sold_{row['id']}"): 
                    cursor.execute("UPDATE ads SET status='Sold' WHERE id=?", (row['id'],)) 
                    conn.commit() 
                    st.rerun() 
            else: 
                if c2.button(f"🔄 Relist", key=f"relist_{row['id']}"): 
                    cursor.execute("UPDATE ads SET status='Available' WHERE id=?", (row['id'],)) 
                    conn.commit() 
                    st.rerun() 
 
            st.markdown('</div>', unsafe_allow_html=True) 
 
# --- MESSAGES PAGE --- 
elif st.session_state.page == "messages": 
    st.subheader("💬 Messages") 
     
    # Inbox 
    st.write("### Inbox") 
    inbox = pd.read_sql(""" 
        SELECT sender, message, created_at FROM messages  
        WHERE receiver=? ORDER BY id DESC LIMIT 10 
    """, conn, params=(st.session_state.user,)) 
     
    if not inbox.empty: 
        for i, row in inbox.iterrows(): 
            st.info(f"**From:** {row['sender']} | **Time:** {row['created_at']}\n\n{row['message']}") 
    else: 
        st.write("No messages yet.") 
 
    st.write("---") 
     
    # Send Message 
    st.write("### Send Message") 
    receiver = st.text_input("Receiver Mobile Number") 
    msg = st.text_area("Your Message") 
     
    if st.button("Send Message"): 
        if receiver and msg: 
            cursor.execute(""" 
            INSERT INTO messages(sender, receiver, message, created_at) 
            VALUES(?,?,?,?) 
            """, (st.session_state.user, receiver, msg, datetime.now())) 
            conn.commit() 
            st.success("Message Sent!") 
        else: 
            st.error("Please fill all fields") 
 
# --- GST PAGE --- 
elif st.session_state.page == "gst": 
    st.subheader("🧾 GST Calculator") 
     
    col1, col2 = st.columns(2) 
    with col1: 
        amount = st.number_input("Amount (₹)", value=1000.0) 
    with col2: 
        rate = st.selectbox("GST Rate %", [5, 12, 18, 28], index=2) 
 
    gst = amount * rate / 100 
    total = amount + gst 
    cgst = gst / 2 
    sgst = gst / 2 
 
    st.write("---") 
    c1, c2, c3 = st.columns(3) 
    c1.metric("CGST", f"₹{cgst:.2f}") 
    c2.metric("SGST", f"₹{sgst:.2f}") 
    c3.metric("Total GST", f"₹{gst:.2f}") 
     
    st.success(f"Grand Total: ₹{total:.2f}") 
 
# --- EMI PAGE --- 
elif st.session_state.page == "emi": 
    st.subheader("🏦 EMI Calculator") 
     
    col1, col2, col3 = st.columns(3) 
    with col1: 
        loan = st.number_input("Loan Amount (₹)", value=100000.0) 
    with col2: 
        rate = st.number_input("Interest Rate (%)", value=10.0) 
    with col3: 
        years = st.number_input("Tenure (Years)", value=1) 
 
    months = years * 12 
    r = rate / (12 * 100) 
 
    if r > 0: 
        emi = loan * r * (1 + r)**months / ((1 + r)**months - 1) 
        total_pay = emi * months 
        interest = total_pay - loan 
         
        st.write("---") 
        st.metric("Monthly EMI", f"₹{emi:,.2f}") 
        st.write(f"Total Interest: ₹{interest:,.2f}") 
        st.write(f"Total Payment: ₹{total_pay:,.2f}") 
    else: 
        st.write("Enter a valid interest rate.") 
 
# --- ADMIN PAGE --- 
elif st.session_state.page == "admin": 
    # Simple admin check (In production, use proper auth) 
    if st.session_state.user == "918590304889" or st.session_state.user == "admin":  
        st.subheader("⚙️ Admin Dashboard") 
         
        users_count = pd.read_sql("SELECT COUNT(*) c FROM users", conn).iloc[0]["c"] 
        ads_count = pd.read_sql("SELECT COUNT(*) c FROM ads", conn).iloc[0]["c"] 
        sold_count = pd.read_sql("SELECT COUNT(*) c FROM ads WHERE status='Sold'", conn).iloc[0]["c"] 
 
        a, b, c = st.columns(3) 
        a.metric("Total Users", users_count) 
        b.metric("Total Ads", ads_count) 
        c.metric("Items Sold", sold_count) 
 
        st.subheader("Recent Activity") 
        recent = pd.read_sql("SELECT title, price, status, user_mobile FROM ads ORDER BY id DESC LIMIT 10", conn) 
        st.dataframe(recent, use_container_width=True) 
    else: 
        st.error("🚫 Access Denied. Admins only.") 
 
# --- HOME PAGE (DEFAULT) --- 
else: 
    # Search Bar 
    search = st.text_input("🔍 Search Products...", key="search_term", placeholder="Type to search...") 
     
    # Category Filter Logic 
    st.subheader("Categories") 
    cat_cols = st.columns(6) 
    categories = ["All", "Mobiles", "Electronics", "Vehicles", "Property", "Jobs"] 
     
    for i, (col, cat_name) in enumerate(zip(cat_cols, categories)): 
        with col: 
            # Generate a unique key for each button 
            if st.button(cat_name, key=f"cat_{cat_name}"): 
                st.session_state.selected_category = cat_name 
                st.rerun() 
     
    # Visual indicator for selected category 
    st.write(f"**Selected Category:** {st.session_state.selected_category}") 
 
    # --- SHOW ADS --- 
    st.subheader("🛍️ Latest Listings") 
 
    # Build SQL Query dynamically 
    query = """ 
    SELECT * FROM ads  
    WHERE status='Available'  
    """ 
    params = [] 
 
    # Search Filter 
    if search: 
        query += " AND (title LIKE ? OR description LIKE ?)" 
        params.extend([f"%{search}%", f"%{search}%"]) 
     
    # Category Filter 
    if st.session_state.selected_category != "All": 
        query += " AND category=?" 
        params.append(st.session_state.selected_category) 
 
    # Sorting (Boosted first) 
    query += """ 
    ORDER BY 
    CASE 
        WHEN boost='Spotlight' THEN 1 
        WHEN boost='Featured' THEN 2 
        WHEN boost='Fast Sell' THEN 3 
        ELSE 4 
    END, 
    id DESC 
    """ 
 
    ads_df = pd.read_sql(query, conn, params=params) 
 
    if ads_df.empty: 
        st.warning("No ads found matching your criteria.") 
    else: 
        # Increment views for displayed ads 
        ad_ids = ads_df['id'].tolist() 
        cursor.execute(f"UPDATE ads SET views = views + 1 WHERE id IN ({','.join('?'*len(ad_ids))})", ad_ids) 
        conn.commit() 
 
        # Grid Layout for Ads 
        cols = st.columns(3) # 3 ads per row 
         
        for idx, row in ads_df.iterrows(): 
            col = cols[idx % 3] 
             
            with col: 
                st.markdown('<div class="card">', unsafe_allow_html=True) 
                 
                # Image Handling 
                if row["image"]: 
                    try: 
                        img_data = base64.b64decode(row["image"]) 
                        st.image(img_data, use_container_width=True) 
                    except: 
                        st.image("https://via.placeholder.com/300x200?text=Image+Error", use_container_width=True) 
                else: 
                    st.image("https://via.placeholder.com/300x200?text=No+Image", use_container_width=True) 
 
                # Details 
                st.markdown(f"### {row['title']}") 
                st.markdown(f"<div class='price'>₹{row['price']:,.0f}</div>", unsafe_allow_html=True) 
                st.caption(f"📍 {row['location']} | Views: {row['views']}") 
                 
                # Contact Buttons 
                c1, c2 = st.columns(2) 
                 
                whatsapp_link = f"https://wa.me/{row['user_mobile']}?text=Hi, I'm interested in {row['title']}" 
                call_link = f"tel:{row['user_mobile']}" 
                 
                c1.markdown( 
                    f"<a href='{whatsapp_link}' target='_blank' class='greenbtn'>💬 Chat</a>", 
                    unsafe_allow_html=True 
                ) 
                c2.markdown( 
                    f"<a href='{call_link}' class='orangebtn'>📞 Call</a>", 
                    unsafe_allow_html=True 
                ) 
                 
                st.markdown('</div>', unsafe_allow_html=True) 
 
    # ---------- MAP ---------- 
    st.subheader("📍 Map View (Kerala)") 
     
    # Generate random map data for demo based on ads count 
    # In a real app, you would geocode the 'location' column 
    num_points = min(len(ads_df), 10) 
     
    if num_points > 0: 
        map_data = pd.DataFrame({ 
            'lat': [10.5 + (i * 0.1) for i in range(num_points)], # Mock lat for Kerala 
            'lon': [76.2 + (i * 0.05) for i in range(num_points)] # Mock lon for Kerala 
        }) 
        st.map(map_data, zoom=7) 
    else: 
        map_data = pd.DataFrame({"lat": [10.8505], "lon": [76.2711]}) # Center of Kerala 
        st.map(map_data, zoom=7) 
