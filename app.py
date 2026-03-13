import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Kerala Buy & Sell", layout="wide")

# ---------------- DATABASE ----------------
conn = sqlite3.connect("kerala_market.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT,
password TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS ads(
id INTEGER PRIMARY KEY AUTOINCREMENT,
user TEXT,
title TEXT,
price REAL,
category TEXT,
location TEXT,
description TEXT,
image BLOB,
date TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS favourites(
id INTEGER PRIMARY KEY AUTOINCREMENT,
user TEXT,
title TEXT
)
""")

conn.commit()

# ---------------- FUNCTIONS ----------------

def signup(u,p):
    cursor.execute("INSERT INTO users(username,password) VALUES(?,?)",(u,p))
    conn.commit()

def login(u,p):
    cursor.execute("SELECT * FROM users WHERE username=? AND password=?",(u,p))
    return cursor.fetchone()

def add_ad(user,title,price,cat,loc,desc,img):

    cursor.execute("""
    INSERT INTO ads(user,title,price,category,location,description,image,date)
    VALUES(?,?,?,?,?,?,?,?)
    """,(user,title,price,cat,loc,desc,img,datetime.now()))

    conn.commit()

def get_ads():
    return pd.read_sql("SELECT * FROM ads ORDER BY id DESC",conn)

def get_my_ads(user):
    return pd.read_sql("SELECT * FROM ads WHERE user=?",(user,),conn)

def add_fav(user,title):
    cursor.execute("INSERT INTO favourites(user,title) VALUES(?,?)",(user,title))
    conn.commit()

def get_favs(user):
    return pd.read_sql("SELECT * FROM favourites WHERE user=?",(user,),conn)

# ---------------- SESSION ----------------
if "user" not in st.session_state:
    st.session_state.user=None

# ---------------- STYLE ----------------
st.markdown("""
<style>

.header{
background:linear-gradient(90deg,#0f9d58,#34a853);
padding:18px;
border-radius:10px;
color:white;
font-size:28px;
font-weight:bold;
}

.card{
background:white;
padding:12px;
border-radius:10px;
box-shadow:0 2px 12px rgba(0,0,0,0.1);
margin-bottom:15px;
}

</style>
""",unsafe_allow_html=True)

st.markdown('<div class="header">Kerala Buy & Sell Marketplace</div>',unsafe_allow_html=True)

# ---------------- MENU ----------------
menu = st.sidebar.selectbox(
"Menu",
[
"Home",
"Browse",
"Post Ad",
"My Ads",
"Favourites",
"Login",
"Signup",
"Admin"
]
)

# ---------------- HOME ----------------
if menu=="Home":

    st.subheader("Buy & Sell Across Kerala")

    search=st.text_input("Search products")

    categories=[
    "Mobiles","Electronics","Vehicles",
    "Property","Jobs","Furniture"
    ]

    cols=st.columns(len(categories))

    for i,c in enumerate(categories):
        cols[i].button(c)

    st.markdown("### Latest Listings")

    df=get_ads()

    if search:
        df=df[df["title"].str.contains(search,case=False)]

    cols=st.columns(3)

    for i,row in df.head(9).iterrows():

        with cols[i%3]:

            st.markdown('<div class="card">',unsafe_allow_html=True)

            if row["image"]:
                st.image(row["image"],use_column_width=True)

            st.markdown(f"**{row['title']}**")

            st.write("₹",row["price"])

            st.write("📍",row["location"])

            if st.session_state.user:

                if st.button("❤️ Favourite",key=f"h{i}"):

                    add_fav(st.session_state.user,row["title"])

            st.markdown('</div>',unsafe_allow_html=True)

# ---------------- BROWSE ----------------
elif menu=="Browse":

    st.title("Marketplace")

    df=get_ads()

    cat=st.selectbox(
    "Filter Category",
    ["All","Mobiles","Electronics","Vehicles","Property","Jobs","Furniture"]
    )

    if cat!="All":
        df=df[df["category"]==cat]

    cols=st.columns(3)

    for i,row in df.iterrows():

        with cols[i%3]:

            st.markdown('<div class="card">',unsafe_allow_html=True)

            if row["image"]:
                st.image(row["image"],use_column_width=True)

            st.markdown(f"**{row['title']}**")

            st.write("₹",row["price"])

            st.write("📍",row["location"])

            st.write(row["description"])

            st.button("Contact Seller",key=f"c{i}")

            st.markdown('</div>',unsafe_allow_html=True)

# ---------------- POST AD ----------------
elif menu=="Post Ad":

    if not st.session_state.user:

        st.warning("Please login first")

    else:

        st.title("Sell Your Item")

        title=st.text_input("Title")

        price=st.number_input("Price")

        category=st.selectbox(
        "Category",
        [
        "Mobiles","Electronics","Vehicles",
        "Property","Jobs","Furniture","Others"
        ])

        location=st.text_input("Location")

        desc=st.text_area("Description")

        img=st.file_uploader("Upload Image")

        if st.button("Post Listing"):

            image=None

            if img:
                image=img.read()

            add_ad(
            st.session_state.user,
            title,
            price,
            category,
            location,
            desc,
            image
            )

            st.success("Listing Posted Successfully")

# ---------------- MY ADS ----------------
elif menu=="My Ads":

    if not st.session_state.user:

        st.warning("Login first")

    else:

        st.title("My Listings")

        df=pd.read_sql(
        "SELECT * FROM ads WHERE user=?",
        conn,
        params=(st.session_state.user,)
        )

        st.dataframe(df)

# ---------------- FAVOURITES ----------------
elif menu=="Favourites":

    if not st.session_state.user:

        st.warning("Login first")

    else:

        st.title("Favourite Ads")

        df=pd.read_sql(
        "SELECT * FROM favourites WHERE user=?",
        conn,
        params=(st.session_state.user,)
        )

        st.dataframe(df)

# ---------------- LOGIN ----------------
elif menu=="Login":

    st.title("User Login")

    u=st.text_input("Username")
    p=st.text_input("Password",type="password")

    if st.button("Login"):

        user=login(u,p)

        if user:

            st.session_state.user=u

            st.success("Login successful")

        else:

            st.error("Invalid login")

# ---------------- SIGNUP ----------------
elif menu=="Signup":

    st.title("Create Account")

    u=st.text_input("Username")
    p=st.text_input("Password",type="password")

    if st.button("Signup"):

        signup(u,p)

        st.success("Account created")

# ---------------- ADMIN ----------------
elif menu=="Admin":

    st.title("Admin Dashboard")

    ads=get_ads()

    users=pd.read_sql("SELECT * FROM users",conn)

    st.metric("Total Ads",len(ads))
    st.metric("Total Users",len(users))

    st.subheader("All Ads")
    st.dataframe(ads)

    st.subheader("All Users")
    st.dataframe(users)
