import streamlit as st
import pandas as pd

# 1. SETUP
st.set_page_config(page_title="TDS Pro V2", layout="wide")

@st.cache_data
def load_data():
    try:
        df = pd.read_csv("tds_data.csv", sep=None, engine='python')
        df.columns = [c.strip() for c in df.columns]
        for col in ['Section', 'Payee Type']:
            df[col] = df[col].astype(str).str.strip()
        df['Effective From'] = pd.to_datetime(df['Effective From'], dayfirst=True, errors='coerce').fillna(pd.Timestamp('1900-01-01'))
        df['Effective To'] = pd.to_datetime(df['Effective To'], dayfirst=True, errors='coerce').fillna(pd.Timestamp('2099-12-31'))
        return df
    except Exception as e:
        st.error(f"Data Error: {e}")
        return None

df = load_data()

if df is not None:
    st.title("🏛️ TDS Calculation Portal - Advanced V2")
    st.markdown("### *Feature: Dual Threshold Compliance*")
    st.write("---")

    # 2. INPUT LAYOUT
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Step 1: Transaction Details")
        section = st.selectbox("Select Income Tax Section", options=sorted(df['Section'].unique()))
        
        # FEATURE: Logic Choice
        calc_mode = st.radio("Threshold Basis:", ["Single Transaction", "Aggregate (Full Year)"])
        
        amount = st.number_input(f"Enter {calc_mode} Amount (INR)", min_value=0.0, format="%.2f")
        pay_date = st.date_input("Transaction Date")

    with col2:
        st.subheader("Step 2: Payee Information")
        pan_status = st.radio("Does the Payee have a valid PAN?", ["Yes", "No"])
        
        payee_options = sorted(df[df['Section'] == section]['Payee Type'].unique())
        payee_type = st.selectbox("Category of Payee", options=payee_options)

    # 3. ADVANCED CALCULATION
    if st.button("🚀 Run Compliance Check"):
        target = pd.to_datetime(pay_date)
        pot = df[(df['Section'] == section) & (df['Payee Type'] == payee_type)]
        rule = pot[(pot['Effective From'] <= target) & (pot['Effective To'] >= target)]
        
        # Fallback for future dates (2026)
        if rule.empty and not pot.empty:
            rule = pot.sort_values(by='Effective From', ascending=False).head(1)

        if not rule.empty:
            sel = rule.iloc[0]
            rate_raw = str(sel['Rate of TDS (%)']).strip()
            
            if rate_raw.lower() == 'avg':
                st.info(f"💡 **Slab-based Deduction Required:** {sel['Notes']}")
            else:
                base_rate = float(rate_raw)
                # Apply 20% Penalty if No PAN
                final_rate = 20.0 if pan_status == "No" else base_rate
                
                # THRESHOLD LOGIC
                # We use the CSV limit for Single, and 1 Lakh for Aggregate in 194C
                limit = float(sel['Threshold Amount (Rs)'])
                if section == "194C" and calc_mode == "Aggregate (Full Year)":
                    limit = 100000.0 # Standard Indian IT Aggregate for 194C
                
                if amount > limit:
                    tax_amount = (amount * final_rate) / 100
                    st.success(f"### ✅ TDS MUST BE DEDUCTED")
                    st.write(f"The amount exceeds the {calc_mode} limit of **₹{limit:,.0f}**.")
                    st.metric("TDS Payable", f"₹{tax_amount:,.2f}", f"Rate: {final_rate}%")
                else:
                    st.warning(f"### ⚠️ NO TDS REQUIRED")
                    st.write(f"Amount is within the {calc_mode} safety limit of **₹{limit:,.0f}**.")
        else:
            st.error("No matching rule found in database for this date/payee combo.")
            @st.cache_data
def load_data():
    try:
        # Added 'on_bad_lines' to skip or fix rows with extra commas
        df = pd.read_csv("tds_data.csv", 
                         sep=None, 
                         engine='python', 
                         on_bad_lines='skip') # This skips the broken line so the app loads
        
        df.columns = [c.strip() for c in df.columns]
        # ... (keep the rest of your cleaning code the same)
        return df
