import streamlit as st 
st.title("ROBOAI XRF SIMULATION")


home_page = st.Page(
    "pages/parameters.py",
    title="Home",
    icon="🏠",
    default=True
)

pg=st.navigation([
    home_page
])

pg.run()

