import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Kerala Buy & Sell", layout="wide")

ADMIN_NUMBER = "918590304889"

# ---------------- DATABASE ----------------
conn = sqlite3.connect("marketplace.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY AUTOINCREMENT,
mobile TEXT UNIQUE,
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
created_at TEXT
)
""")

conn.commit()

# ---------------- SESSION ----------------
if "user" not in st.session_state:
    st.session_state.user = None

# ---------------- THEME ----------------
st.markdown("""
<style>

body{
background: linear-gradient(135deg,#1e8e3e,#2ecc71);
}

.header{
background:#1e8e3e;
padding:15px;
border-radius:10px;
color:white;
font-size:28px;
font-weight:bold;
}

.card{
background:white;
padding:15px;
border-radius:10px;
box-shadow:0px 3px 10px rgba(0,0,0,0.2);
margin-bottom:15px;
}

.price{
color:#ff6a00;
font-size:20px;
font-weight:bold;
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

# ---------------- HEADER ----------------
st.markdown('<div class="header">Kerala Buy & Sell</div>', unsafe_allow_html=True)

# ---------------- LOGIN ----------------
if st.session_state.user is None:

    st.subheader("Login / Signup")

    mobile = st.text_input("Mobile Number")

    if st.button("Login"):

        cursor.execute("SELECT * FROM users WHERE mobile=?", (mobile,))
        user = cursor.fetchone()

        if not user:
            cursor.execute(
                "INSERT INTO users(mobile,created_at) VALUES(?,?)",
                (mobile, datetime.now())
            )
            conn.commit()

            # ADMIN WHATSAPP NOTIFY LINK
            msg = f"New user signup: {mobile}"
            link = f"https://wa.me/{ADMIN_NUMBER}?text={msg}"

            st.success("New user created")
            st.markdown(f"[Notify Admin on WhatsApp]({link})")

        st.session_state.user = mobile
        st.success("Login Successful")

# ---------------- MAIN APP ----------------
if st.session_state.user:

    st.write("Logged in as:", st.session_state.user)

    # MENU
    m1,m2,m3 = st.columns(3)

    page = "home"

    if m1.button("Home"):
        page="home"

    if m2.button("Post Ad"):
        page="post"

    if st.session_state.user == ADMIN_NUMBER:
        if m3.button("Admin"):
            page="admin"

    # ---------------- POST AD ----------------
    if page=="post":

        st.subheader("Post Ad")

        title = st.text_input("Title")
        price = st.number_input("Price")
        category = st.selectbox("Category",
        ["Mobiles","Electronics","Vehicles","Property","Jobs"])
        location = st.text_input("Location")
        desc = st.text_area("Description")
        image = st.text_input("Image URL")

        if st.button("Publish Ad"):

            cursor.execute("""
            INSERT INTO ads(
            user_mobile,title,price,category,
            location,description,image,boost,created_at
            )
            VALUES(?,?,?,?,?,?,?,?,?)
            """,(
            st.session_state.user,
            title,
            price,
            category,
            location,
            desc,
            image,
            "Normal",
            datetime.now()
            ))

            conn.commit()

            st.success("Ad Posted")

    # ---------------- SHOW ADS ----------------
    st.subheader("Latest Listings")

    ads = pd.read_sql("SELECT * FROM ads ORDER BY id DESC", conn)

    for i,row in ads.iterrows():

        st.markdown('<div class="card">', unsafe_allow_html=True)

        col1,col2 = st.columns([1,3])

        if row["image"]:
            col1.image(row["image"], width=120)
        else:
            col1.image("https://via.placeholder.com/120")

        col2.markdown(f"### {row['title']}")
        col2.markdown(
            f"<div class='price'>₹{row['price']}</div>",
            unsafe_allow_html=True
        )

        col2.write("📍", row["location"])

        chat = f"https://wa.me/{row['user_mobile']}"

        col2.markdown(
        f"[Chat Seller]({chat})"
        )

        st.markdown("</div>", unsafe_allow_html=True)

    # ---------------- ADMIN PANEL ----------------
    if st.session_state.user == ADMIN_NUMBER:

        st.subheader("Admin Panel")

        users = pd.read_sql("SELECT * FROM users", conn)
        ads = pd.read_sql("SELECT * FROM ads", conn)

        st.write("Total Users:", len(users))
        st.write("Total Ads:", len(ads))

        st.subheader("All Users")
        st.dataframe(users)

        st.subheader("All Ads")
        st.dataframe(ads)
