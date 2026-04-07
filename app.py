import streamlit as st
import pandas as pd

st.set_page_config(page_title="TDS Portal V2", layout="wide")

@st.cache_data
def load_data():
    try:
        # FIX: usecols=range(13) ignores those extra ghost commas (14 and 15)
        # on_bad_lines='skip' ensures the app doesn't crash if a line is still messy
        df = pd.read_csv("tds_data.csv", 
                         sep=None, 
                         engine='python', 
                         usecols=range(13), 
                         on_bad_lines='skip')
        
        # Standardize columns
        df.columns = [c.strip() for c in df.columns]
        for col in ['Section', 'Payee Type']:
            df[col] = df[col].astype(str).str.strip()
            
        # Date Handling
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
    
    col1, col2 = st.columns(2)
    with col1:
        section = st.selectbox("1. Section", options=sorted(df['Section'].unique()))
        
        # NEW FEATURE: Selection for Single or Aggregate
        calc_mode = st.radio("Threshold Basis:", ["Single Transaction", "Aggregate (Full Year)"])
        
        amount = st.number_input(f"2. {calc_mode} Amount (INR)", min_value=0.0)
        pay_date = st.date_input("3. Date")
        
    with col2:
        pan_status = st.radio("4. PAN Available?", ["Yes", "No"])
        payee_options = sorted(df[df['Section'] == section]['Payee Type'].unique())
        payee_type = st.selectbox("5. Category", options=payee_options)

    if st.button("Calculate"):
        target = pd.to_datetime(pay_date)
        pot = df[(df['Section'] == section) & (df['Payee Type'] == payee_type)]
        rule = pot[(pot['Effective From'] <= target) & (pot['Effective To'] >= target)]
        
        if rule.empty and not pot.empty:
            rule = pot.sort_values(by='Effective From', ascending=False).head(1)

        if not rule.empty:
            sel = rule.iloc[0]
            rate_raw = str(sel['Rate of TDS (%)']).strip()
            
            if rate_raw.lower() == 'avg':
                st.info(f"Note: {sel['Notes']}")
            else:
                try:
                    base = float(rate_raw)
                    final = 20.0 if pan_status == "No" else base
                    
                    # DUAL THRESHOLD LOGIC
                    # Default threshold from CSV
                    thresh = float(sel['Threshold Amount (Rs)'])
                    
                    # Specific override for 194C Aggregate limit
                    if section == "194C" and calc_mode == "Aggregate (Full Year)":
                        thresh = 100000.0
                    
                    if amount > thresh:
                        st.success(f"✅ Deduct TDS: ₹{(amount * final / 100):,.2f}")
                        st.write(f"Applied Rate: {final}%")
                        st.caption(f"Reason: Amount exceeds {calc_mode} limit of ₹{thresh:,.0f}")
                    else:
                        st.warning(f"⚠️ Below {calc_mode} Threshold (₹{thresh:,.0f})")
                except ValueError:
                    st.error("Check Excel/CSV: Rate or Threshold is not a number.")
        else:
            st.error("No matching rule found for this Section/Payee/Date combo.")
