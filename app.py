import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Kerala Buy & Sell",
    layout="wide"
)

# ---------------- DATABASE ----------------
conn = sqlite3.connect("marketplace.db",check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS ads(
id INTEGER PRIMARY KEY AUTOINCREMENT,
title TEXT,
price REAL,
category TEXT,
location TEXT,
description TEXT,
image TEXT,
created_at TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY AUTOINCREMENT,
mobile TEXT,
created_at TEXT
)
""")

conn.commit()

# ---------------- CSS DESIGN ----------------
st.markdown("""
<style>

body{
background:#f5f7fb;
}

.header{
background:#1b8c3c;
padding:15px;
border-radius:10px;
color:white;
font-size:28px;
font-weight:bold;
}

.category{
background:white;
padding:15px;
border-radius:12px;
text-align:center;
box-shadow:0px 3px 10px rgba(0,0,0,0.1);
}

.adcard{
background:white;
padding:15px;
border-radius:12px;
box-shadow:0px 3px 10px rgba(0,0,0,0.15);
margin-bottom:20px;
}

.price{
color:#ff6a00;
font-size:20px;
font-weight:bold;
}

.btnchat{
background:#1b8c3c;
color:white;
padding:8px 15px;
border-radius:8px;
text-align:center;
}

.btnsell{
background:#ff6a00;
color:white;
padding:8px 15px;
border-radius:8px;
text-align:center;
}

</style>
""",unsafe_allow_html=True)

# ---------------- HEADER ----------------

st.markdown(
'<div class="header">🛍 Kerala Buy & Sell</div>',
unsafe_allow_html=True
)

st.write("Buy & Sell Easily in Kerala")

# ---------------- SEARCH ----------------

col1,col2 = st.columns([4,1])

search = col1.text_input("Search products")

if col2.button("Search"):
    st.success("Searching...")

# ---------------- CATEGORIES ----------------

st.subheader("Categories")

c1,c2,c3,c4 = st.columns(4)

c1.markdown('<div class="category">📱 Mobiles</div>',unsafe_allow_html=True)
c2.markdown('<div class="category">💻 Electronics</div>',unsafe_allow_html=True)
c3.markdown('<div class="category">🚗 Vehicles</div>',unsafe_allow_html=True)
c4.markdown('<div class="category">💼 Jobs</div>',unsafe_allow_html=True)

st.write("")

# ---------------- POST AD ----------------

with st.expander("Post Your Ad"):

    title = st.text_input("Title")

    price = st.number_input("Price")

    category = st.selectbox(
        "Category",
        ["Mobiles","Electronics","Vehicles","Jobs"]
    )

    location = st.text_input("Location")

    desc = st.text_area("Description")

    if st.button("Post Ad"):

        cursor.execute("""
        INSERT INTO ads(
        title,price,category,location,description,created_at
        )
        VALUES(?,?,?,?,?,?)
        """,(title,price,category,location,desc,datetime.now()))

        conn.commit()

        st.success("Ad Posted Successfully")

# ---------------- LIST ADS ----------------

st.subheader("Latest Listings")

ads = pd.read_sql(
"SELECT * FROM ads ORDER BY id DESC",
conn
)

for i,row in ads.iterrows():

    st.markdown('<div class="adcard">',unsafe_allow_html=True)

    col1,col2 = st.columns([1,3])

    col1.image(
        "https://via.placeholder.com/150",
        width=120
    )

    col2.markdown(f"### {row['title']}")
    col2.markdown(
        f"<div class='price'>₹{row['price']}</div>",
        unsafe_allow_html=True
    )
    col2.write(row["location"])

    b1,b2 = col2.columns(2)

    b1.markdown(
        "<div class='btnchat'>Chat</div>",
        unsafe_allow_html=True
    )

    b2.markdown(
        "<div class='btnsell'>Sell Now</div>",
        unsafe_allow_html=True
    )

    st.markdown('</div>',unsafe_allow_html=True)

# ---------------- ADMIN PANEL ----------------

st.subheader("Admin Dashboard")

total_users = pd.read_sql(
"SELECT COUNT(*) c FROM users",
conn
).iloc[0]["c"]

total_ads = pd.read_sql(
"SELECT COUNT(*) c FROM ads",
conn
).iloc[0]["c"]

a,b,c,d = st.columns(4)

a.metric("Total Users",total_users)
b.metric("Total Listings",total_ads)
c.metric("Active Chats","0")
d.metric("Pending Ads","0")
