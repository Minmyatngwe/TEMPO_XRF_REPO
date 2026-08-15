import streamlit as st 

st.subheader("XRAY Tube filter Supported Shape")

with st.expander("show"):
    st.image("views/images/xray_tube_supportedshape.png")

st.subheader("Suppored Sample shape")
with st.expander("show"):
    st.image("views/images/sample.png")
    
st.subheader("Supported detector collimatory shape")
with st.expander("show"):
    st.image("views/images/detector_collimator.png")
    
st.subheader("Supported detector shape")
with st.expander("show"):
    st.image("views/images/detector_shape.png")