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

if "page" not in st.session_state:
    st.session_state.page="home"

# ---------------- STYLE ----------------

st.markdown("""
<style>

.title{
font-size:40px;
font-weight:bold;
color:#0f9d58;
}

.button-row button{
background:#0f9d58;
color:white;
border-radius:8px;
width:100%;
height:45px;
font-weight:bold;
}

.card{
background:white;
padding:15px;
border-radius:12px;
box-shadow:0px 3px 12px rgba(0,0,0,0.15);
margin-bottom:20px;
}

.price{
color:#ff6f00;
font-size:22px;
font-weight:bold;
}

</style>
""",unsafe_allow_html=True)

# ---------------- HEADER ----------------

st.markdown('<div class="title">Kerala Buy & Sell</div>',unsafe_allow_html=True)

# ---------------- HOME BUTTON MENU ----------------

col1,col2,col3,col4=st.columns(4)

if col1.button("Browse Ads"):
    st.session_state.page="browse"

if col2.button("Post Ad"):
    st.session_state.page="post"

if col3.button("My Ads"):
    st.session_state.page="myads"

if col4.button("Favourites"):
    st.session_state.page="fav"

col5,col6,col7=st.columns(3)

if col5.button("Login"):
    st.session_state.page="login"

if col6.button("Signup"):
    st.session_state.page="signup"

if col7.button("Admin"):
    st.session_state.page="admin"

st.divider()

# ---------------- HOME PAGE ----------------

if st.session_state.page=="home":

    st.subheader("Latest Listings")

    df=get_ads()

    cols=st.columns(3)

    for i,row in df.head(9).iterrows():

        with cols[i%3]:

            st.markdown('<div class="card">',unsafe_allow_html=True)

            if row["image"]:
                st.image(row["image"],use_column_width=True)

            st.markdown(f"### {row['title']}")
            st.markdown(f'<div class="price">₹ {row["price"]}</div>',unsafe_allow_html=True)

            st.write("📍",row["location"])

            st.markdown('</div>',unsafe_allow_html=True)

# ---------------- BROWSE ----------------

elif st.session_state.page=="browse":

    st.header("Browse Marketplace")

    search=st.text_input("Search")

    df=get_ads()

    if search:
        df=df[df["title"].str.contains(search,case=False)]

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

            st.markdown('</div>',unsafe_allow_html=True)

# ---------------- POST AD ----------------

elif st.session_state.page=="post":

    if not st.session_state.user:
        st.warning("Please login first")
    else:

        st.header("Post Ad")

        title=st.text_input("Title")
        price=st.number_input("Price")

        category=st.selectbox(
        "Category",
        ["Mobiles","Electronics","Vehicles","Property","Jobs","Furniture"]
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

            st.success("Ad Posted")

# ---------------- MY ADS ----------------

elif st.session_state.page=="myads":

    if not st.session_state.user:
        st.warning("Login first")
    else:

        st.header("My Ads")

        df=pd.read_sql(
        "SELECT * FROM ads WHERE user=?",
        conn,
        params=(st.session_state.user,)
        )

        st.dataframe(df)

# ---------------- FAVOURITES ----------------

elif st.session_state.page=="fav":

    if not st.session_state.user:
        st.warning("Login first")
    else:

        st.header("Favourite Ads")

        df=pd.read_sql(
        "SELECT * FROM favourites WHERE user=?",
        conn,
        params=(st.session_state.user,)
        )

        st.dataframe(df)

# ---------------- LOGIN ----------------

elif st.session_state.page=="login":

    st.header("Login")

    u=st.text_input("Username")
    p=st.text_input("Password",type="password")

    if st.button("Login"):

        user=login(u,p)

        if user:
            st.session_state.user=u
            st.success("Login Successful")
            st.session_state.page="home"
        else:
            st.error("Invalid Login")

# ---------------- SIGNUP ----------------

elif st.session_state.page=="signup":

    st.header("Signup")

    u=st.text_input("Username")
    p=st.text_input("Password",type="password")

    if st.button("Create Account"):

        signup(u,p)

        st.success("Account Created")

# ---------------- ADMIN ----------------

elif st.session_state.page=="admin":

    st.header("Admin Dashboard")

    ads=get_ads()
    users=pd.read_sql("SELECT * FROM users",conn)

    col1,col2=st.columns(2)

    col1.metric("Total Ads",len(ads))
    col2.metric("Total Users",len(users))

    st.subheader("All Ads")
    st.dataframe(ads)

    st.subheader("All Users")
    st.dataframe(users)
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

if "page" not in st.session_state:
    st.session_state.page="home"

# ---------------- STYLE ----------------

st.markdown("""
<style>

.title{
font-size:40px;
font-weight:bold;
color:#0f9d58;
}

.button-row button{
background:#0f9d58;
color:white;
border-radius:8px;
width:100%;
height:45px;
font-weight:bold;
}

.card{
background:white;
padding:15px;
border-radius:12px;
box-shadow:0px 3px 12px rgba(0,0,0,0.15);
margin-bottom:20px;
}

.price{
color:#ff6f00;
font-size:22px;
font-weight:bold;
}

</style>
""",unsafe_allow_html=True)

# ---------------- HEADER ----------------

st.markdown('<div class="title">Kerala Buy & Sell</div>',unsafe_allow_html=True)

# ---------------- HOME BUTTON MENU ----------------

col1,col2,col3,col4=st.columns(4)

if col1.button("Browse Ads"):
    st.session_state.page="browse"

if col2.button("Post Ad"):
    st.session_state.page="post"

if col3.button("My Ads"):
    st.session_state.page="myads"

if col4.button("Favourites"):
    st.session_state.page="fav"

col5,col6,col7=st.columns(3)

if col5.button("Login"):
    st.session_state.page="login"

if col6.button("Signup"):
    st.session_state.page="signup"

if col7.button("Admin"):
    st.session_state.page="admin"

st.divider()

# ---------------- HOME PAGE ----------------

if st.session_state.page=="home":

    st.subheader("Latest Listings")

    df=get_ads()

    cols=st.columns(3)

    for i,row in df.head(9).iterrows():

        with cols[i%3]:

            st.markdown('<div class="card">',unsafe_allow_html=True)

            if row["image"]:
                st.image(row["image"],use_column_width=True)

            st.markdown(f"### {row['title']}")
            st.markdown(f'<div class="price">₹ {row["price"]}</div>',unsafe_allow_html=True)

            st.write("📍",row["location"])

            st.markdown('</div>',unsafe_allow_html=True)

# ---------------- BROWSE ----------------

elif st.session_state.page=="browse":

    st.header("Browse Marketplace")

    search=st.text_input("Search")

    df=get_ads()

    if search:
        df=df[df["title"].str.contains(search,case=False)]

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

            st.markdown('</div>',unsafe_allow_html=True)

# ---------------- POST AD ----------------

elif st.session_state.page=="post":

    if not st.session_state.user:
        st.warning("Please login first")
    else:

        st.header("Post Ad")

        title=st.text_input("Title")
        price=st.number_input("Price")

        category=st.selectbox(
        "Category",
        ["Mobiles","Electronics","Vehicles","Property","Jobs","Furniture"]
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

            st.success("Ad Posted")

# ---------------- MY ADS ----------------

elif st.session_state.page=="myads":

    if not st.session_state.user:
        st.warning("Login first")
    else:

        st.header("My Ads")

        df=pd.read_sql(
        "SELECT * FROM ads WHERE user=?",
        conn,
        params=(st.session_state.user,)
        )

        st.dataframe(df)

# ---------------- FAVOURITES ----------------

elif st.session_state.page=="fav":

    if not st.session_state.user:
        st.warning("Login first")
    else:

        st.header("Favourite Ads")

        df=pd.read_sql(
        "SELECT * FROM favourites WHERE user=?",
        conn,
        params=(st.session_state.user,)
        )

        st.dataframe(df)

# ---------------- LOGIN ----------------

elif st.session_state.page=="login":

    st.header("Login")

    u=st.text_input("Username")
    p=st.text_input("Password",type="password")

    if st.button("Login"):

        user=login(u,p)

        if user:
            st.session_state.user=u
            st.success("Login Successful")
            st.session_state.page="home"
        else:
            st.error("Invalid Login")

# ---------------- SIGNUP ----------------

elif st.session_state.page=="signup":

    st.header("Signup")

    u=st.text_input("Username")
    p=st.text_input("Password",type="password")

    if st.button("Create Account"):

        signup(u,p)

        st.success("Account Created")

# ---------------- ADMIN ----------------

elif st.session_state.page=="admin":

    st.header("Admin Dashboard")

    ads=get_ads()
    users=pd.read_sql("SELECT * FROM users",conn)

    col1,col2=st.columns(2)

    col1.metric("Total Ads",len(ads))
    col2.metric("Total Users",len(users))

    st.subheader("All Ads")
    st.dataframe(ads)

    st.subheader("All Users")
    st.dataframe(users)
