import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Kerala Buy & Sell", layout="wide")

# ---------------- DATABASE ----------------

conn = sqlite3.connect("kerala_market.db",check_same_thread=False)
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
    """,(user,title,price,cat,loc,desc,img,str(datetime.now())))

    conn.commit()

def get_ads():
    return pd.read_sql("SELECT * FROM ads ORDER BY id DESC",conn)

# ---------------- SESSION ----------------

if "user" not in st.session_state:
    st.session_state.user=None

# ---------------- STYLE ----------------

st.markdown("""
<style>

.main-title{
font-size:40px;
font-weight:700;
color:#0f9d58;
}

.sub-title{
font-size:20px;
color:gray;
margin-bottom:20px;
}

.card{
background:white;
padding:15px;
border-radius:12px;
box-shadow:0px 3px 15px rgba(0,0,0,0.1);
margin-bottom:20px;
}

.price{
color:#ff6f00;
font-size:22px;
font-weight:bold;
}

.category-btn button{
width:100%;
background:#0f9d58;
color:white;
border-radius:8px;
}

.searchbox input{
border-radius:10px;
}

</style>
""",unsafe_allow_html=True)

# ---------------- HEADER ----------------

col1,col2=st.columns([1,4])

with col1:
    st.image("https://cdn-icons-png.flaticon.com/512/3081/3081559.png",width=80)

with col2:
    st.markdown('<div class="main-title">Kerala Buy & Sell</div>',unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Buy & Sell Easily in Kerala</div>',unsafe_allow_html=True)

# ---------------- MENU ----------------

menu=st.sidebar.selectbox(
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

    st.markdown("### 🔍 Search Marketplace")

    search=st.text_input("",placeholder="Search products...")

    st.markdown("### Categories")

    categories=[
    "Mobiles","Electronics","Vehicles",
    "Property","Jobs","Furniture"
    ]

    cols=st.columns(6)

    for i,c in enumerate(categories):
        cols[i].button(c)

    st.markdown("### Latest Listings")

    df=get_ads()

    if search:
        df=df[df["title"].str.contains(search,case=False)]

    cols=st.columns(3)

    for i,row in df.head(12).iterrows():

        with cols[i%3]:

            st.markdown('<div class="card">',unsafe_allow_html=True)

            if row["image"]:
                st.image(row["image"],use_column_width=True)

            st.markdown(f"### {row['title']}")
            st.markdown(f'<div class="price">₹ {row["price"]}</div>',unsafe_allow_html=True)

            st.write("📍",row["location"])

            if st.session_state.user:

                if st.button("❤️ Favourite",key=f"h{i}"):

                    cursor.execute(
                    "INSERT INTO favourites(user,title) VALUES(?,?)",
                    (st.session_state.user,row["title"])
                    )
                    conn.commit()

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

            st.markdown(f"### {row['title']}")
            st.markdown(f'<div class="price">₹ {row["price"]}</div>',unsafe_allow_html=True)

            st.write("📍",row["location"])
            st.write(row["description"])

            st.button("💬 Contact Seller",key=f"c{i}")

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
        ["Mobiles","Electronics","Vehicles","Property","Jobs","Furniture","Others"]
        )

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

    c1,c2=st.columns(2)

    c1.metric("Total Ads",len(ads))
    c2.metric("Total Users",len(users))

    st.subheader("All Ads")
    st.dataframe(ads)

    st.subheader("All Users")
    st.dataframe(users)
