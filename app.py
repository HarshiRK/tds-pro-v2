import streamlit as st
import pandas as pd

st.set_page_config(page_title="TDS Portal V2", layout="wide")

@st.cache_data
def load_data():
    try:
        # UPDATED FILENAME: Matching your new Excel file
        df = pd.read_excel("TDS_Master_Data.xlsx", engine='openpyxl')
        
        # CLEANING: This part is crucial for the 194C categories to appear
        df.columns = [c.strip() for c in df.columns]
        
        # Force these columns to be clean text strings
        df['Section'] = df['Section'].astype(str).str.strip()
        df['Payee Type'] = df['Payee Type'].astype(str).str.strip()
        
        # Standardize Rates and Thresholds to numbers
        df['Threshold Amount (Rs)'] = pd.to_numeric(df['Threshold Amount (Rs)'], errors='coerce').fillna(0)
        
        # Date Handling
        df['Effective From'] = pd.to_datetime(df['Effective From'], errors='coerce')
        df['Effective To'] = pd.to_datetime(df['Effective To'], errors='coerce').fillna(pd.Timestamp('2099-12-31'))
        
        return df
    except Exception as e:
        st.error(f"Excel Load Error: {e}. Check if 'TDS_Master_Data.xlsx' is on GitHub.")
        return None

df = load_data()

if df is not None:
    st.title("🏛️ TDS Calculation Portal - Advanced V2")
    st.write("---")
    
    col1, col2 = st.columns(2)
    with col1:
        # 1. SECTION SELECTION
        sections = sorted([s for s in df['Section'].unique() if s != 'nan' and s != 'None'])
        section = st.selectbox("1. Select Section", options=sections)
        
        calc_mode = st.radio("Threshold Basis:", ["Single Transaction", "Aggregate (Full Year)"])
        amount = st.number_input(f"2. {calc_mode} Amount (INR)", min_value=0.0)
        pay_date = st.date_input("3. Transaction Date")

    with col2:
        # 2. PAN & CATEGORY SELECTION
        pan_status = st.radio("4. PAN Available?", ["Yes", "No"])
        
        # This filter ensures 'Individual/HUF' and 'Others' show up for 194C
        filtered_df = df[df['Section'] == section]
        payee_options = sorted([p for p in filtered_df['Payee Type'].unique() if p != 'nan' and p != 'None'])
        
        payee_type = st.selectbox("5. Category of Payee", options=payee_options)

    # 3. CALCULATION LOGIC
    if st.button("Calculate"):
        target = pd.to_datetime(pay_date)
        match = filtered_df[filtered_df['Payee Type'] == payee_type]
        rule = match[(match['Effective From'] <= target) & (match['Effective To'] >= target)]
        
        # Latest rate fallback
        if rule.empty and not match.empty:
            rule = match.sort_values(by='Effective From', ascending=False).head(1)

        if not rule.empty:
            sel = rule.iloc[0]
            rate_raw = str(sel['Rate of TDS (%)']).strip().lower()
            
            if rate_raw == 'avg':
                st.info(f"Note: {sel['Notes']}")
            else:
                try:
                    base = float(sel['Rate of TDS (%)'])
                    final = 20.0 if pan_status == "No" else base
                    thresh = float(sel['Threshold Amount (Rs)'])
                    
                    # Aggregate logic for 194C
                    if section == "194C" and calc_mode == "Aggregate (Full Year)":
                        thresh = 100000.0
                    
                    if amount > thresh:
                        st.success(f"Deduct: ₹{(amount * final / 100):,.2f} (@ {final}%)")
                    else:
                        st.warning(f"Below {calc_mode} limit (₹{thresh:,.0f})")
                except:
                    st.error("Data Value Error: Check the rates in your Excel sheet.")
