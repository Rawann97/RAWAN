import streamlit as st
import requests
import pandas as pd

st.title("Daily OpMet Report")

# 1. Input Section
st.subheader("Add New Entry")
with st.form("input_form"):
    msg_text = st.text_area("Message Content:")
    if st.form_submit_button("Send to Database"):
        res = requests.post("http://backend:8000/messages", json={"content": msg_text})
        st.success("Saved!") if res.status_code == 200 else st.error("Error")

st.divider()

# 2. Report Filters Section (Same as your PDF)
st.subheader("Report Filters")
col1, col2 = st.columns(2)
with col1:
    st.selectbox("Message Type", ["All", "Daily MCC", "Report Generator"])
with col2:
    st.date_input("Select Date")

# 3. Generate Button & Table
if st.button("Generate Report Summary"):
    res = requests.get("http://backend:8000/messages")
    if res.status_code == 200:
        data = res.json()
        if data:
            st.table(pd.DataFrame(data))
        else:
            st.warning("No data found.")