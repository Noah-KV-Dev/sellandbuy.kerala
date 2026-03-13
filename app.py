import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="Kerala Buy & Sell", layout="wide")

# ---------- DATABASE ----------
conn = sqlite3.connect("marketplace.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY AUTOINCREMENT,
mobile TEXT,
created_at TEXT
)
""")

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
created_at TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS messages(
id INTEGER PRIMARY KEY AUTOINCREMENT,
sender TEXT,
receiver TEXT,
message TEXT,
created_at TEXT
)
""")

conn.commit()

# ---------- SESSION ----------
if "page" not in st.session_state:
    st.session_state.page = "home"

if "user" not in st.session_state:
    st.session_state.user = None

# ---------- GRASS THEME ----------
st.markdown("""
<style>

body{
background: linear-gradient(-45deg,#1e8e3e,#2ecc71,#27ae60,#16a085);
background-size:400% 400%;
animation:grass 12s ease infinite;
}

@keyframes grass{
0%{background-position:0% 50%}
50%{background-position:100% 50%}
100%{background-position:0% 50%}
}

.header{
background:#1e8e3e;
padding:18px;
border-radius:12px;
color:white;
font-size:28px;
font-weight:bold;
}

.card{
background:white;
padding:15px;
border-radius:15px;
box-shadow:0px 4px 12px rgba(0,0,0,0.2);
margin-bottom:15px;
}

.price{
color:#ff6a00;
font-size:22px;
font-weight:bold;
}

.greenbtn{
background:#1e8e3e;
color:white;
padding:6px;
border-radius:8px;
text-align:center;
}

.orangebtn{
background:#ff6a00;
color:white;
padding:6px;
border-radius:8px;
text-align:center;
}

.category{
background:white;
padding:10px;
border-radius:10px;
text-align:center;
box-shadow:0px 2px 10px rgba(0,0,0,0.2);
}

</style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.markdown('<div class="header">Kerala Buy & Sell</div>', unsafe_allow_html=True)

# ---------- LOGIN ----------
if st.session_state.user is None:

    st.subheader("Mobile Login")

    mobile = st.text_input("Enter Mobile Number")

    consent = st.checkbox("Notify admin on WhatsApp when I sign up")

    if st.button("Login / Signup"):

        cursor.execute("SELECT * FROM users WHERE mobile=?", (mobile,))
        user = cursor.fetchone()

        if not user:
            cursor.execute(
                "INSERT INTO users(mobile,created_at) VALUES(?,?)",
                (mobile, datetime.now())
            )
            conn.commit()

            if consent:
                msg = f"New user signup: {mobile}"
                admin_link = f"https://wa.me/918590304889?text={msg}"
                st.markdown(f"[Notify Admin on WhatsApp]({admin_link})")

        st.session_state.user = mobile
        st.success("Login successful")

# ---------- MENU ----------
if st.session_state.user:

    m1,m2,m3,m4,m5,m6,m7 = st.columns(7)

    if m1.button("Home"): st.session_state.page="home"
    if m2.button("Post Ad"): st.session_state.page="post"
    if m3.button("My Ads"): st.session_state.page="myads"
    if m4.button("Messages"): st.session_state.page="chat"
    if m5.button("GST"): st.session_state.page="gst"
    if m6.button("EMI"): st.session_state.page="emi"
    if m7.button("Admin"): st.session_state.page="admin"

# ---------- SEARCH ----------
search = st.text_input("Search products")

# ---------- CATEGORIES ----------
st.subheader("Categories")

c1,c2,c3,c4,c5 = st.columns(5)

c1.markdown('<div class="category">Mobiles</div>', unsafe_allow_html=True)
c2.markdown('<div class="category">Electronics</div>', unsafe_allow_html=True)
c3.markdown('<div class="category">Vehicles</div>', unsafe_allow_html=True)
c4.markdown('<div class="category">Property</div>', unsafe_allow_html=True)
c5.markdown('<div class="category">Jobs</div>', unsafe_allow_html=True)

# ---------- POST AD ----------
if st.session_state.page == "post":

    st.subheader("Post Ad")

    title = st.text_input("Title")
    price = st.number_input("Price")
    category = st.selectbox("Category",["Mobiles","Electronics","Vehicles","Property","Jobs"])
    location = st.text_input("Location")
    desc = st.text_area("Description")
    image = st.text_input("Image URL")

    boost = st.selectbox("Boost",
    ["Normal","Fast Sell","Featured","Spotlight"])

    if st.button("Publish"):

        cursor.execute("""
        INSERT INTO ads(
        user_mobile,title,price,category,
        location,description,image,boost,views,created_at
        )
        VALUES(?,?,?,?,?,?,?,?,?,?)
        """,(st.session_state.user,title,price,category,
        location,desc,image,boost,0,datetime.now()))

        conn.commit()

        st.success("Ad Posted")

# ---------- SHOW ADS ----------
st.subheader("Latest Listings")

ads = pd.read_sql("""
SELECT * FROM ads
ORDER BY
CASE
WHEN boost='Spotlight' THEN 1
WHEN boost='Featured' THEN 2
WHEN boost='Fast Sell' THEN 3
ELSE 4
END,
id DESC
""", conn)

for i,row in ads.iterrows():

    st.markdown('<div class="card">', unsafe_allow_html=True)

    col1,col2 = st.columns([1,3])

    if row["image"]:
        col1.image(row["image"], width=120)
    else:
        col1.image("https://via.placeholder.com/120")

    col2.markdown(f"### {row['title']}")
    col2.markdown(f"<div class='price'>₹{row['price']}</div>", unsafe_allow_html=True)
    col2.write("📍", row["location"])

    whatsapp_link = f"https://wa.me/{row['user_mobile']}"

    b1,b2 = col2.columns(2)

    b1.markdown(
        f"<a href='{whatsapp_link}'><div class='greenbtn'>Chat</div></a>",
        unsafe_allow_html=True
    )

    b2.markdown(
        "<div class='orangebtn'>Sell</div>",
        unsafe_allow_html=True
    )

    st.markdown("</div>", unsafe_allow_html=True)

# ---------- GST ----------
if st.session_state.page == "gst":

    st.subheader("GST Calculator")

    amount = st.number_input("Amount")
    rate = st.selectbox("GST %",[5,12,18,28])

    gst = amount * rate / 100
    total = amount + gst

    st.write("GST:", gst)
    st.write("Total:", total)

# ---------- EMI ----------
if st.session_state.page == "emi":

    st.subheader("EMI Calculator")

    loan = st.number_input("Loan Amount")
    rate = st.number_input("Interest %")
    years = st.number_input("Years")

    months = years * 12
    r = rate/(12*100)

    if r>0:
        emi = loan*r*(1+r)**months/((1+r)**months-1)
        st.metric("Monthly EMI", emi)

# ---------- CHAT ----------
if st.session_state.page == "chat":

    st.subheader("Messages")

    receiver = st.text_input("Send to Mobile")
    msg = st.text_input("Message")

    if st.button("Send"):

        cursor.execute("""
        INSERT INTO messages(sender,receiver,message,created_at)
        VALUES(?,?,?,?)
        """,(st.session_state.user,receiver,msg,datetime.now()))

        conn.commit()

        st.success("Message Sent")

# ---------- ADMIN ----------
if st.session_state.page == "admin":

    st.subheader("Admin Dashboard")

    users = pd.read_sql("SELECT COUNT(*) c FROM users",conn).iloc[0]["c"]
    ads_count = pd.read_sql("SELECT COUNT(*) c FROM ads",conn).iloc[0]["c"]

    a,b,c = st.columns(3)

    a.metric("Users", users)
    b.metric("Ads", ads_count)
    c.metric("Revenue","-")

    st.subheader("Recent Ads")

    data = pd.read_sql("""
    SELECT title,category,price,location
    FROM ads ORDER BY id DESC LIMIT 10
    """, conn)

    st.dataframe(data)

# ---------- MAP ----------
st.subheader("Map")

map_data = pd.DataFrame({
"lat":[11.2588],
"lon":[75.7804]
})

st.map(map_data)
