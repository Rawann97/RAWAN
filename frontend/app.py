import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="OpMet Reports", layout="wide")
st.sidebar.title("📌 Navigation")
page = st.sidebar.radio("Go to:", ["Main Dashboard", "Weekly Report", "Monthly Report"])

URL_BASE = "http://fastapi_backend:8000"

@st.cache_data(ttl=60) 
def get_data():
    try:
        res = requests.get(f"{URL_BASE}/messages", timeout=10)
        res.raise_for_status() 
        return pd.DataFrame(res.json())
    except Exception as e:
        st.error(f"⚠️ Error fetching data: {e}")
        return None
    
if page == "Main Dashboard":
    st.title("📊 OpMet Quality Control")
    df = get_data()
    if df is not None:
        # تأكدي أن عمود is_approved موجود، إذا لم يوجد نفترض أنه False للكل
        if 'is_approved' not in df.columns:
            df['is_approved'] = False

        c1, c2, c3 = st.columns(3)
        
        # 1. إجمالي الرسائل
        c1.metric("Total Messages", len(df))
        
        # 2. الرسائل المعتمدة (التي ضغطتِ عليها Approve)
        approved_count = len(df[df['is_approved'] == True])
        c2.metric("Approved Messages", approved_count)
        
        # 3. الرسائل التي لم تُعتمد بعد (Pending)
        pending_count = len(df[df['is_approved'] == False])
        c3.metric("Pending Review", pending_count)
        
        st.write("---")
        
        # عرض البيانات مع تمييز المعتمد منها (اختياري)
        st.subheader("Recent Messages Data")
        st.dataframe(df, use_container_width=True)
#if page == "Main Dashboard":
    #st.title("📊 OpMet Quality Control")
    #df = get_data()
    #if df is not None:
        #c1, c2, c3 = st.columns(3)
        #c1.metric("Total Messages", len(df))
        #c2.metric("Valid Messages", len(df[df['classification'].str.contains('Valid|1', na=False)]))
        #c3.metric("Delayed (N)", len(df[df['classification'] == 'N']))
        
        #st.write("---")
        #st.dataframe(df, use_container_width=True)

elif page == "Weekly Report":
    st.title("📅 Weekly Performance Report")
    df = get_data()
    
    if df is not None:
        df['msg_date'] = pd.to_datetime(df['msg_date'])
        
        # 1. الإحصائيات العامة للأسبوع (KPIs) 
        total_week = len(df)
        on_time_week = len(df[df['classification'].str.contains('Valid|1', na=False)])
        completion_rate = (on_time_week / total_week * 100) if total_week > 0 else 0
        
        col1, col2 = st.columns(2)
        col1.metric("Weekly Completion Rate", f"{round(completion_rate, 2)}%")
        col2.metric("Total Weekly Messages", total_week)
        
        st.write("---")

        # 2. ملخص لكل محطة (Per-station summaries)
        st.subheader("📍 Station Performance Summary")

        station_stats = df.groupby('filename').agg(
            Total=('id', 'count'),
            On_Time=('classification', lambda x: x.str.contains('Valid|1').sum()),
            Delayed=('classification', lambda x: (x == 'N').sum()),
            Missing=('classification', lambda x: (x == '0').sum())
        ).reset_index()
        
        station_stats['Success_%'] = (station_stats['On_Time'] / station_stats['Total'] * 100).round(1)
        st.dataframe(station_stats.sort_values(by='Success_%', ascending=False), use_container_width=True)

        # 3. الرسم البياني لليوم 
        st.subheader("📆 Day-by-Day Performance")
        df['Day'] = df['msg_date'].dt.day_name()
        # ترتيب الأيام بشكل صحيح
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_counts = df.groupby('Day').size().reindex(days_order).fillna(0)
        
        st.bar_chart(day_counts)
        
    else:
        st.error("Could not fetch data.")

elif page == "Monthly Report":
    st.title("📈 Monthly Trends & Exports")
    df = get_data()
    if df is not None:
        st.write("### Download Aggregated Report")
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Report as CSV",
            data=csv,
            file_name='opmet_monthly_report.csv',
            mime='text/csv',
        )
        
        # رسم بياني للتوجه 
        st.subheader("Message Trends")
        df['Date'] = pd.to_datetime(df['msg_date']).dt.date
        trend_data = df.groupby('Date').size()
        st.line_chart(trend_data)

        st.write("---")
        st.subheader("✅ Supervisor Review")
        
        # نطلع الرسائل اللي ما تمت الموافقة عليها
        pending = df[df['is_approved'] == False]
        
        if not pending.empty:
            supervisor_name = st.text_input("Enter Supervisor Name", placeholder="Write your name here...")
            msg_id = st.selectbox("Select Msg ID to Approve", pending['id'])

            if st.button("Approve This Message"):
                if supervisor_name:
                    res = requests.post(f"{URL_BASE}/messages/{msg_id}/approve?name={supervisor_name}")
                    if res.status_code == 200:
                        st.success(f"Message {msg_id} Approved by {supervisor_name}! 🎉")
                        st.cache_data.clear()  
                        st.rerun()
                    else:
                        st.error("Failed to approve. Check backend connection.")
                else:
                    st.warning("⚠️ Please enter your name before approving.")
        else:
            st.info("Everything is approved! 🎉")
