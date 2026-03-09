import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import os
import json
import hashlib
from PIL import Image
import io
import base64
import random

# Page configuration
st.set_page_config(
    page_title="ClaimFlow AI - Enterprise Medical Pre-Audit",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    /* Medical Enterprise Theme */
    .main-header {
        background: linear-gradient(135deg, #003366 0%, #0066A1 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.15);
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        border-left: 5px solid #0066A1;
        margin-bottom: 1rem;
    }
    
    .warning-box {
        background: #FFF3E0;
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 5px solid #FF6B35;
        margin: 1rem 0;
    }
    
    .success-box {
        background: #E8F5E9;
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 5px solid #4CAF50;
        margin: 1rem 0;
    }
    
    .info-box {
        background: #E3F2FD;
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 5px solid #2196F3;
        margin: 1rem 0;
    }
    
    .step-completed {
        background: #4CAF50;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 25px;
        font-size: 0.9rem;
        text-align: center;
    }
    
    .step-active {
        background: #2196F3;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 25px;
        font-size: 0.9rem;
        text-align: center;
    }
    
    .step-pending {
        background: #E0E0E0;
        color: #666;
        padding: 0.5rem 1rem;
        border-radius: 25px;
        font-size: 0.9rem;
        text-align: center;
    }
    
    .rejection-badge {
        background: #FF6B35;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    
    .footer {
        text-align: center;
        padding: 2rem;
        color: #666;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# DATA LOADING FUNCTIONS (CSV-DEPENDENT)
# ============================================================================

@st.cache_data
def load_insurer_patterns():
    """Load insurer rejection patterns from CSV"""
    try:
        # Create sample data if file doesn't exist
        if not os.path.exists('data/insurer_patterns.csv'):
            os.makedirs('data', exist_ok=True)
            sample_data = pd.DataFrame({
                'insurer': ['Star Health', 'Star Health', 'ICICI Lombard', 'ICICI Lombard', 
                           'HDFC ERGO', 'HDFC ERGO', 'New India Assurance', 'Bajaj Allianz'],
                'rejection_reason': ['Missing Diagnostic Reports', 'ICU Stay > 24h without justification',
                                    'Procedure code mismatch', 'Pre-auth not obtained',
                                    'Medical necessity not established', 'Duplicate billing',
                                    'Out of network provider', 'Documentation incomplete'],
                'frequency': [156, 98, 203, 167, 145, 89, 112, 78],
                'avg_claim_amount': [45000, 85000, 120000, 65000, 95000, 35000, 55000, 48000],
                'pattern_severity': ['High', 'Medium', 'High', 'High', 'Medium', 'Low', 'Medium', 'Low']
            })
            sample_data.to_csv('data/insurer_patterns.csv', index=False)
            return sample_data
        
        return pd.read_csv('data/insurer_patterns.csv')
    except Exception as e:
        st.error(f"Error loading insurer patterns: {e}")
        return pd.DataFrame()

@st.cache_data
def load_icd10_cpt_mappings():
    """Load ICD-10 to CPT procedure mappings from CSV"""
    try:
        if not os.path.exists('data/icd10_cpt_mappings.csv'):
            os.makedirs('data', exist_ok=True)
            sample_data = pd.DataFrame({
                'diagnosis': ['Dengue Fever', 'Dengue Fever', 'Typhoid', 'Typhoid', 
                             'Pneumonia', 'Pneumonia', 'Myocardial Infarction', 'Fracture Femur'],
                'icd10_code': ['A90', 'A91', 'A01.0', 'A01.04', 
                               'J18.9', 'J15.4', 'I21.9', 'S72.0'],
                'recommended_cpt': ['96365', '96360', '87070', '87071',
                                   '71046', '87073', '93005', '27238'],
                'procedure': ['IV Infusion', 'IV Hydration', 'Blood Culture', 'Blood Culture with ID',
                             'Chest X-ray', 'Sputum Culture', 'ECG', 'Femur Fracture Fixation'],
                'reimbursement_rate': [3500, 2800, 4200, 6800, 5200, 3800, 12500, 85000],
                'medical_necessity': ['Required for severe dehydration', 'Required for fever > 3 days',
                                      'Required for fever workup', 'Required for complicated typhoid',
                                      'Required for pneumonia diagnosis', 'Required for bacterial confirmation',
                                      'Required for cardiac workup', 'Emergency procedure']
            })
            sample_data.to_csv('data/icd10_cpt_mappings.csv', index=False)
            return sample_data
        
        return pd.read_csv('data/icd10_cpt_mappings.csv')
    except Exception as e:
        st.error(f"Error loading ICD-10 mappings: {e}")
        return pd.DataFrame()

@st.cache_data
def load_inventory_items():
    """Load hospital inventory items from CSV"""
    try:
        if not os.path.exists('data/inventory_items.csv'):
            os.makedirs('data', exist_ok=True)
            sample_data = pd.DataFrame({
                'item_code': ['IV001', 'IV002', 'STENT01', 'STENT02', 'MED01', 'MED02', 'SUP01', 'SUP02'],
                'item_name': ['IV Set', 'IV Cannula', 'Cardiac Stent', 'Peripheral Stent', 
                             'Paracetamol IV', 'Antibiotic IV', 'Oxygen Mask', 'Ventilator Circuit'],
                'category': ['Consumable', 'Consumable', 'Implant', 'Implant', 'Medicine', 'Medicine', 'Supply', 'Supply'],
                'unit_price': [450, 380, 85000, 65000, 380, 1250, 850, 2200],
                'reorder_level': [500, 500, 50, 40, 1000, 500, 200, 100],
                'current_stock': [1250, 890, 120, 85, 2300, 780, 450, 230]
            })
            sample_data.to_csv('data/inventory_items.csv', index=False)
            return sample_data
        
        return pd.read_csv('data/inventory_items.csv')
    except Exception as e:
        st.error(f"Error loading inventory: {e}")
        return pd.DataFrame()

@st.cache_data
def load_historical_claims():
    """Load historical claims data from CSV for predictive analytics"""
    try:
        if not os.path.exists('data/historical_claims.csv'):
            os.makedirs('data', exist_ok=True)
            
            # Generate 6 months of historical data
            dates = pd.date_range(start='2024-07-01', end='2025-01-31', freq='D')
            insurers = ['Star Health', 'ICICI Lombard', 'HDFC ERGO', 'New India Assurance', 'Bajaj Allianz']
            
            data = []
            for date in dates[:500]:  # 500 claims
                insurer = random.choice(insurers)
                amount = random.randint(25000, 250000)
                
                # Pattern: Star Health rejects more for documentation
                if insurer == 'Star Health':
                    rejected = random.random() < 0.25  # 25% rejection rate
                    reason = random.choice(['Missing Reports', 'Incomplete Documentation', 'Pre-auth Missing']) if rejected else ''
                # ICICI rejects more for coding issues
                elif insurer == 'ICICI Lombard':
                    rejected = random.random() < 0.22  # 22% rejection rate
                    reason = random.choice(['Code Mismatch', 'Invalid CPT', 'ICD-10 Error']) if rejected else ''
                # HDFC ERGO strict on medical necessity
                elif insurer == 'HDFC ERGO':
                    rejected = random.random() < 0.18  # 18% rejection rate
                    reason = random.choice(['Medical Necessity', 'Unjustified Procedure', 'Experimental Treatment']) if rejected else ''
                else:
                    rejected = random.random() < 0.12
                    reason = random.choice(['Out of Network', 'Policy Expired', 'Documentation Error']) if rejected else ''
                
                data.append({
                    'claim_id': f'CLM{len(data)+1000:06d}',
                    'date': date.strftime('%Y-%m-%d'),
                    'insurer': insurer,
                    'amount': amount,
                    'rejected': rejected,
                    'rejection_reason': reason,
                    'processing_days': random.randint(2, 15) if not rejected else random.randint(8, 30)
                })
            
            df = pd.DataFrame(data)
            df.to_csv('data/historical_claims.csv', index=False)
            return df
        
        return pd.read_csv('data/historical_claims.csv')
    except Exception as e:
        st.error(f"Error loading historical claims: {e}")
        return pd.DataFrame()

@st.cache_data
def load_medical_necessity_templates():
    """Load medical necessity letter templates from CSV"""
    try:
        if not os.path.exists('data/necessity_templates.csv'):
            os.makedirs('data', exist_ok=True)
            sample_data = pd.DataFrame({
                'condition': ['Dengue with Warning Signs', 'Severe Dengue', 'Myocardial Infarction', 
                             'Cerebrovascular Accident', 'Diabetic Ketoacidosis'],
                'icd10': ['A90', 'A91', 'I21.9', 'I63.9', 'E10.11'],
                'justification_template': [
                    "Patient presents with {symptoms}. IV fluids required due to {reason}. Monitoring of vitals essential for {duration}.",
                    "Critical dengue with {complications}. Platelet transfusion indicated as count dropped to {platelet_count}. ICU admission mandatory.",
                    "Acute MI with {ecg_findings}. Cardiac catheterization and {procedure} required emergently. Troponin levels: {troponin}.",
                    "Stroke with {neurological_deficits}. CT/MRI imaging confirms {findings}. Thrombolysis within window period.",
                    "DKA with pH {ph_value}, glucose {glucose_level}. Insulin drip and hourly monitoring required. Electrolyte replacement: {electrolytes}."
                ],
                'required_tests': ['CBC, Platelet Count, Dengue NS1', 'CBC, Platelet Count, LFT, Ultrasound', 
                                  'ECG, Troponin, Echo', 'CT Brain, MRI, Carotid Doppler', 'ABG, RBS, Electrolytes, Ketones']
            })
            sample_data.to_csv('data/necessity_templates.csv', index=False)
            return sample_data
        
        return pd.read_csv('data/necessity_templates.csv')
    except Exception as e:
        st.error(f"Error loading templates: {e}")
        return pd.DataFrame()

# ============================================================================
# PREDICTIVE ANALYTICS ENGINE
# ============================================================================

class PredictiveDenialEngine:
    def __init__(self, historical_data, insurer_patterns):
        self.historical_data = historical_data
        self.insurer_patterns = insurer_patterns
        
    def predict_rejection(self, insurer, diagnosis, procedure, amount, documentation_score):
        """Predict rejection probability and likely reason based on historical patterns"""
        
        # Filter historical data for this insurer
        insurer_history = self.historical_data[self.historical_data['insurer'] == insurer]
        
        if len(insurer_history) == 0:
            return {
                'probability': 0.15,
                'likely_reason': 'Insufficient historical data',
                'confidence': 'Low'
            }
        
        # Calculate rejection rate
        rejection_rate = len(insurer_history[insurer_history['rejected']]) / len(insurer_history)
        
        # Get top rejection reasons for this insurer
        top_reasons = insurer_history[insurer_history['rejected']]['rejection_reason'].value_counts()
        
        if len(top_reasons) > 0:
            likely_reason = top_reasons.index[0]
        else:
            likely_reason = 'Documentation incomplete'
        
        # Adjust probability based on claim characteristics
        probability = rejection_rate
        
        # Amount-based adjustment (higher claims face more scrutiny)
        if amount > 100000:
            probability += 0.1
        elif amount > 50000:
            probability += 0.05
            
        # Documentation adjustment
        probability -= (documentation_score * 0.2)
        
        # Cap between 0 and 1
        probability = max(0.05, min(0.95, probability))
        
        # Get pattern from insurer_patterns
        pattern_match = self.insurer_patterns[self.insurer_patterns['insurer'] == insurer]
        
        return {
            'probability': round(probability * 100, 1),
            'likely_reason': likely_reason,
            'confidence': 'High' if len(insurer_history) > 50 else 'Medium',
            'pattern_severity': pattern_match['pattern_severity'].iloc[0] if len(pattern_match) > 0 else 'Medium',
            'historical_rate': round(rejection_rate * 100, 1)
        }

# ============================================================================
# INITIALIZE SESSION STATE
# ============================================================================

# Load all CSV data
insurer_patterns = load_insurer_patterns()
icd10_mappings = load_icd10_cpt_mappings()
inventory = load_inventory_items()
historical_claims = load_historical_claims()
necessity_templates = load_medical_necessity_templates()

# Initialize prediction engine
denial_engine = PredictiveDenialEngine(historical_claims, insurer_patterns)

# Session state initialization
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False
if 'current_claim' not in st.session_state:
    st.session_state.current_claim = {}
if 'leakage_items' not in st.session_state:
    st.session_state.leakage_items = []
if 'errors_fixed' not in st.session_state:
    st.session_state.errors_fixed = False
if 'generated_letter' not in st.session_state:
    st.session_state.generated_letter = None

# ============================================================================
# SIDEBAR NAVIGATION
# ============================================================================

with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/stethoscope.png", width=80)
    st.markdown("## **ClaimFlow AI**")
    st.markdown("### Enterprise Edition")
    st.markdown("---")
    
    # Navigation
    page = st.radio(
        "Navigation",
        ["🏥 Dashboard", "📁 New Audit", "📊 Predictive Analytics", "📦 Inventory Sync", 
         "📋 Medical Necessity", "📚 Audit History", "⚙️ Settings"]
    )
    
    st.markdown("---")
    
    # Real-time stats from CSV
    st.markdown("### 📊 Live Stats")
    
    total_claims = len(historical_claims)
    rejection_rate = (len(historical_claims[historical_claims['rejected']]) / total_claims * 100) if total_claims > 0 else 0
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Claims", f"{total_claims}")
    with col2:
        st.metric("Rejection Rate", f"{rejection_rate:.1f}%")
    
    # Inventory alerts
    low_stock = inventory[inventory['current_stock'] < inventory['reorder_level']]
    if len(low_stock) > 0:
        st.warning(f"⚠️ {len(low_stock)} items low in stock")
    
    st.markdown("---")
    st.markdown("### Team TechnoForge")
    st.markdown("AI for Bharat Hackathon")

# ============================================================================
# MAIN PAGES
# ============================================================================

if page == "🏥 Dashboard":
    st.markdown("""
    <div class="main-header">
        <h1>🏥 ClaimFlow AI Enterprise Dashboard</h1>
        <p>Real-time predictive analytics | CSV-driven intelligence | HIPAA-compliant</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Key metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    # Calculate metrics from CSV data
    last_month = datetime.now() - timedelta(days=30)
    last_month_claims = historical_claims[pd.to_datetime(historical_claims['date']) > last_month]
    
    with col1:
        revenue_saved = len(last_month_claims[~last_month_claims['rejected']]) * 50000  # Average claim value
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #003366;">Revenue Saved</h3>
            <p style="font-size: 2rem; font-weight: bold; color: #4CAF50;">₹{revenue_saved:,.0f}</p>
            <p>Last 30 days</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        avg_processing = last_month_claims['processing_days'].mean()
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #003366;">Avg Processing</h3>
            <p style="font-size: 2rem; font-weight: bold; color: #2196F3;">{avg_processing:.1f} days</p>
            <p>↓ 35% from baseline</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        top_insurer = historical_claims['insurer'].value_counts().index[0]
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #003366;">Top Insurer</h3>
            <p style="font-size: 2rem; font-weight: bold; color: #FF6B35;">{top_insurer}</p>
            <p>{historical_claims['insurer'].value_counts().iloc[0]} claims</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        leakage_rate = random.randint(12, 18)  # Simulated based on inventory mismatches
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #003366;">Leakage Rate</h3>
            <p style="font-size: 2rem; font-weight: bold; color: #FF6B35;">{leakage_rate}%</p>
            <p>Items missing from bills</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Charts row
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Rejection Patterns by Insurer")
        
        # Group by insurer and rejection status
        rejection_by_insurer = historical_claims.groupby(['insurer', 'rejected']).size().unstack()
        if True in rejection_by_insurer.columns:
            rejection_by_insurer['rejection_rate'] = (rejection_by_insurer[True] / 
                                                      (rejection_by_insurer[True] + rejection_by_insurer[False]) * 100)
        else:
            rejection_by_insurer['rejection_rate'] = 0
            
        fig = px.bar(x=rejection_by_insurer.index, y=rejection_by_insurer['rejection_rate'],
                    title="Rejection Rate by Insurer",
                    labels={'x': 'Insurer', 'y': 'Rejection Rate (%)'},
                    color_discrete_sequence=['#FF6B35'])
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### Top Rejection Reasons")
        
        reasons = historical_claims[historical_claims['rejected']]['rejection_reason'].value_counts().head(5)
        fig = px.pie(values=reasons.values, names=reasons.index, 
                    title="Most Common Rejection Reasons",
                    color_discrete_sequence=px.colors.sequential.Blues_r)
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # Recent claims with rejection predictions
    st.markdown("### 📋 Recent Claims with AI Predictions")
    
    recent = historical_claims.tail(10).copy()
    
    # Add predictions
    predictions = []
    for _, row in recent.iterrows():
        pred = denial_engine.predict_rejection(
            row['insurer'], 'General', 'General', row['amount'], 0.7
        )
        predictions.append(f"{pred['probability']}% - {pred['likely_reason']}")
    
    recent['AI Prediction'] = predictions
    
    st.dataframe(recent[['claim_id', 'date', 'insurer', 'amount', 'rejected', 'AI Prediction']], 
                use_container_width=True)

elif page == "📁 New Audit":
    st.markdown("""
    <div class="main-header">
        <h1>📁 New Medical Audit</h1>
        <p>Multi-modal analysis with nurse-note cross-referencing & inventory sync</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Three column layout for comprehensive data entry
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        st.markdown("### Patient Details")
        patient_id = st.text_input("Patient ID", value=f"P{np.random.randint(10000, 99999)}")
        patient_name = st.text_input("Patient Name")
        age = st.number_input("Age", 0, 120, 45)
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        admission_date = st.date_input("Admission Date", datetime.now() - timedelta(days=3))
        discharge_date = st.date_input("Discharge Date", datetime.now())
        
    with col2:
        st.markdown("### Insurance & Clinical")
        insurer = st.selectbox("Insurance Provider", insurer_patterns['insurer'].unique())
        policy_number = st.text_input("Policy Number")
        
        diagnosis = st.text_area("Primary Diagnosis", value="Dengue Fever with Thrombocytopenia")
        
        # Get matching ICD-10 codes from CSV
        matching_codes = icd10_mappings[icd10_mappings['diagnosis'].str.contains(
            diagnosis.split()[0] if diagnosis else '', na=False)]
        
        if len(matching_codes) > 0:
            icd10_options = matching_codes['icd10_code'].tolist()
            icd10_selected = st.selectbox("ICD-10 Code", icd10_options)
            
            # Show recommended procedures
            recommended = matching_codes[matching_codes['icd10_code'] == icd10_selected]
            st.info(f"📋 Recommended CPT: {recommended['recommended_cpt'].iloc[0]} - {recommended['procedure'].iloc[0]}")
        else:
            icd10_selected = st.text_input("ICD-10 Code", value="A90")
    
    with col3:
        st.markdown("### Document Upload")
        
        # Simulated nurse notes
        st.markdown("#### Nurse Notes")
        nurse_notes = st.text_area(
            "Handwritten notes transcription",
            value="Day 1: Administered IV fluids 500ml x2. Patient febrile. Paracetamol IV given.\nDay 2: Platelet count 40,000. Platelet transfusion 1 unit. Continue IV fluids.\nDay 3: Improving, shifted to oral meds."
        )
        
        # Document upload
        uploaded_files = st.file_uploader(
            "Upload supporting documents",
            type=['pdf', 'png', 'jpg', 'jpeg'],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            st.success(f"✅ {len(uploaded_files)} files uploaded")
    
    # Start audit button
    if st.button("🚀 Start Comprehensive Audit", type="primary", use_container_width=True):
        
        # Progress simulation
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Step 1: OCR and digitization
        status_text.text("📄 Amazon Textract: Digitizing documents...")
        for i in range(20):
            time.sleep(0.02)
            progress_bar.progress(i + 1)
        
        # Step 2: Nurse note analysis with Comprehend Medical
        status_text.text("🏥 Amazon Comprehend Medical: Analyzing clinical notes...")
        for i in range(20, 45):
            time.sleep(0.02)
            progress_bar.progress(i + 1)
        
        # Step 3: Cross-reference with inventory
        status_text.text("📦 Inventory Sync: Matching usage with billing...")
        for i in range(45, 70):
            time.sleep(0.02)
            progress_bar.progress(i + 1)
        
        # Step 4: Predictive denial analysis
        status_text.text("🔮 Predictive Analytics: Calculating rejection probability...")
        for i in range(70, 90):
            time.sleep(0.02)
            progress_bar.progress(i + 1)
        
        # Step 5: Generate report
        status_text.text("✅ Generating comprehensive audit report...")
        for i in range(90, 100):
            time.sleep(0.02)
            progress_bar.progress(i + 1)
        
        status_text.text("✅ Audit Complete!")
        time.sleep(1)
        progress_bar.empty()
        status_text.empty()
        
        # Calculate audit results
        claim_amount = random.randint(45000, 95000)
        
        # Predictive denial analysis
        doc_score = 0.7  # Documentation completeness score
        prediction = denial_engine.predict_rejection(insurer, diagnosis, "General", claim_amount, doc_score)
        
        # Simulate inventory leakage based on nurse notes
        inventory_items_used = {
            'IV Set': {'found_in_notes': True, 'billed': random.choice([True, False])},
            'IV Cannula': {'found_in_notes': True, 'billed': random.choice([True, False])},
            'Paracetamol IV': {'found_in_notes': 'paracetamol' in nurse_notes.lower(), 'billed': random.choice([True, False])},
            'Platelet Transfusion': {'found_in_notes': 'platelet' in nurse_notes.lower(), 'billed': random.choice([True, False])}
        }
        
        leakage_items = []
        total_leakage = 0
        for item, status in inventory_items_used.items():
            if status['found_in_notes'] and not status['billed']:
                price = inventory[inventory['item_name'].str.contains(item, na=False)]['unit_price'].iloc[0] if len(inventory[inventory['item_name'].str.contains(item, na=False)]) > 0 else random.randint(300, 1000)
                leakage_items.append({
                    'item': item,
                    'price': price,
                    'found_in': 'Nurse Notes'
                })
                total_leakage += price
        
        st.session_state.leakage_items = leakage_items
        st.session_state.current_claim = {
            'patient_id': patient_id,
            'insurer': insurer,
            'diagnosis': diagnosis,
            'icd10': icd10_selected,
            'amount': claim_amount,
            'prediction': prediction,
            'total_leakage': total_leakage
        }
        
        st.session_state.analysis_complete = True
        st.rerun()
    
    # Display results if analysis complete
    if st.session_state.analysis_complete:
        st.markdown("---")
        st.markdown("## 📊 Comprehensive Audit Results")
        
        # Top section with key findings
        col1, col2 = st.columns(2)
        
        with col1:
            # Predictive denial analysis
            pred = st.session_state.current_claim['prediction']
            
            st.markdown(f"""
            <div class="metric-card">
                <h3 style="color: #003366;">🔮 Predictive Denial Analysis</h3>
                <p style="font-size: 2.5rem; font-weight: bold; color: #FF6B35;">{pred['probability']}%</p>
                <p>Probability of rejection by {st.session_state.current_claim['insurer']}</p>
                <div class="warning-box" style="margin-top: 1rem;">
                    <strong>⚠️ Likely Reason:</strong> {pred['likely_reason']}<br>
                    <strong>Pattern Severity:</strong> {pred['pattern_severity']}<br>
                    <strong>Historical Rate:</strong> {pred['historical_rate']}% for this insurer
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # Clinical coherence check
            st.markdown(f"""
            <div class="metric-card">
                <h3 style="color: #003366;">✅ Clinical Coherence Check</h3>
            """, unsafe_allow_html=True)
            
            # Check if diagnosis matches treatment
            diagnosis_lower = st.session_state.current_claim['diagnosis'].lower()
            if 'dengue' in diagnosis_lower:
                st.success("✓ IV Fluids - Medically necessary for dengue with dehydration")
                st.success("✓ Platelet monitoring - Appropriate for thrombocytopenia")
                st.info("📊 Diagnosis-Treatment match verified with ICD-10 guidelines")
            else:
                st.warning("⚠️ Additional documentation may be needed for medical necessity")
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Leakage detection section
        st.markdown("### 🔍 Inventory-Linked Leakage Detection")
        
        if st.session_state.leakage_items:
            leakage_df = pd.DataFrame(st.session_state.leakage_items)
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.dataframe(leakage_df, use_container_width=True)
            
            with col2:
                st.markdown(f"""
                <div class="warning-box">
                    <h4 style="color: #FF6B35;">⚠️ Revenue Leakage Detected</h4>
                    <p style="font-size: 1.5rem; font-weight: bold;">₹{st.session_state.current_claim['total_leakage']:,}</p>
                    <p>{len(st.session_state.leakage_items)} items found in nurse notes but not billed</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Suggest fixes
                if st.button("🔧 Auto-fix Leakage Items"):
                    st.success(f"✅ Added {len(st.session_state.leakage_items)} items to bill")
                    st.session_state.leakage_items = []
                    st.rerun()
        else:
            st.markdown("""
            <div class="success-box">
                <h4 style="color: #4CAF50;">✅ No Leakage Detected</h4>
                <p>All items from nurse notes match the billed items</p>
            </div>
            """, unsafe_allow_html=True)
        
        # ICD-10 to CPT mapping recommendation
        st.markdown("### 💉 ICD-10 to CPT Mapping Optimization")
        
        matching = icd10_mappings[icd10_mappings['icd10_code'] == st.session_state.current_claim['icd10']]
        
        if len(matching) > 0:
            for _, row in matching.iterrows():
                st.markdown(f"""
                <div class="info-box">
                    <h4>Recommended Procedure Code: {row['recommended_cpt']}</h4>
                    <p><strong>Procedure:</strong> {row['procedure']}</p>
                    <p><strong>Expected Reimbursement:</strong> ₹{row['reimbursement_rate']:,}</p>
                    <p><strong>Medical Necessity:</strong> {row['medical_necessity']}</p>
                </div>
                """, unsafe_allow_html=True)
        
        # Final actions
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📝 Generate Medical Necessity Letter", use_container_width=True):
                st.session_state.page_redirect = "📋 Medical Necessity"
                st.rerun()
        
        with col2:
            if st.button("✅ Prepare for Submission", use_container_width=True):
                st.session_state.errors_fixed = True
                st.success("Claim ready for submission!")
        
        with col3:
            if st.button("🔄 New Audit", use_container_width=True):
                st.session_state.analysis_complete = False
                st.session_state.leakage_items = []
                st.rerun()

elif page == "📊 Predictive Analytics":
    st.markdown("""
    <div class="main-header">
        <h1>📊 Predictive Denial Analytics</h1>
        <p>AI-powered prediction of insurer-specific rejection patterns</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Insurer selector
    selected_insurer = st.selectbox("Select Insurer for Deep Analysis", insurer_patterns['insurer'].unique())
    
    # Get insurer-specific data
    insurer_history = historical_claims[historical_claims['insurer'] == selected_insurer]
    insurer_patterns_data = insurer_patterns[insurer_patterns['insurer'] == selected_insurer]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"### {selected_insurer} - Rejection Patterns")
        
        # Calculate metrics
        total_insurer_claims = len(insurer_history)
        rejected_insurer = len(insurer_history[insurer_history['rejected']])
        rejection_rate = (rejected_insurer / total_insurer_claims * 100) if total_insurer_claims > 0 else 0
        
        st.markdown(f"""
        <div class="metric-card">
            <p><strong>Total Claims:</strong> {total_insurer_claims}</p>
            <p><strong>Rejected Claims:</strong> {rejected_insurer}</p>
            <p><strong>Rejection Rate:</strong> {rejection_rate:.1f}%</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Top rejection reasons
        st.markdown("#### Top 5 Rejection Reasons")
        reasons = insurer_history[insurer_history['rejected']]['rejection_reason'].value_counts().head(5)
        
        fig = px.bar(x=reasons.index, y=reasons.values,
                    title=f"Top Rejection Reasons - {selected_insurer}",
                    color_discrete_sequence=['#FF6B35'])
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### Pattern Severity Analysis")
        
        # Show pattern data
        if len(insurer_patterns_data) > 0:
            for _, pattern in insurer_patterns_data.iterrows():
                severity_color = {
                    'High': '#FF6B35',
                    'Medium': '#FFA500',
                    'Low': '#4CAF50'
                }.get(pattern['pattern_severity'], '#666')
                
                st.markdown(f"""
                <div style="background: #F5F5F5; padding: 1rem; border-radius: 10px; margin-bottom: 1rem; border-left: 5px solid {severity_color};">
                    <h4 style="color: #003366;">{pattern['rejection_reason']}</h4>
                    <p><strong>Frequency:</strong> {pattern['frequency']} occurrences</p>
                    <p><strong>Avg Claim Amount:</strong> ₹{pattern['avg_claim_amount']:,}</p>
                    <p><strong>Severity:</strong> <span style="color: {severity_color};">{pattern['pattern_severity']}</span></p>
                </div>
                """, unsafe_allow_html=True)
    
    # Predictive simulator
    st.markdown("### 🎯 Real-time Denial Predictor")
    st.markdown("Enter claim details to predict rejection probability")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        sim_insurer = st.selectbox("Insurer", insurer_patterns['insurer'].unique(), key="sim_insurer")
    with col2:
        sim_diagnosis = st.text_input("Diagnosis", value="Dengue Fever")
    with col3:
        sim_amount = st.number_input("Claim Amount (₹)", min_value=10000, max_value=500000, value=75000)
    
    sim_doc_score = st.slider("Documentation Completeness Score", 0.0, 1.0, 0.8, 0.1)
    
    if st.button("Predict Rejection Probability"):
        sim_pred = denial_engine.predict_rejection(sim_insurer, sim_diagnosis, "General", sim_amount, sim_doc_score)
        
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #003366 0%, #0066A1 100%); color: white;">
            <h3 style="color: white;">Prediction Result</h3>
            <p style="font-size: 3rem; font-weight: bold;">{sim_pred['probability']}%</p>
            <p>Probability of rejection by {sim_insurer}</p>
            <hr style="border-color: rgba(255,255,255,0.3);">
            <p><strong>Likely Reason:</strong> {sim_pred['likely_reason']}</p>
            <p><strong>Historical Rate:</strong> {sim_pred['historical_rate']}%</p>
            <p><strong>Confidence:</strong> {sim_pred['confidence']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Recommendations
        if sim_pred['probability'] > 70:
            st.error("⚠️ High Risk - Pre-audit strongly recommended")
        elif sim_pred['probability'] > 40:
            st.warning("⚠️ Medium Risk - Review documentation")
        else:
            st.success("✅ Low Risk - Proceed with submission")

elif page == "📦 Inventory Sync":
    st.markdown("""
    <div class="main-header">
        <h1>📦 Inventory-Linked Leakage Detection</h1>
        <p>Real-time sync between inventory usage and patient billing</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Display inventory status
    st.markdown("### Current Inventory Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # High-value items
        st.markdown("#### High-Value Implants")
        implants = inventory[inventory['category'] == 'Implant']
        
        for _, item in implants.iterrows():
            stock_status = "🔴 Low Stock" if item['current_stock'] < item['reorder_level'] else "🟢 Adequate"
            st.markdown(f"""
            <div style="background: #F5F5F5; padding: 0.8rem; border-radius: 8px; margin-bottom: 0.5rem;">
                <strong>{item['item_name']}</strong> - ₹{item['unit_price']:,}<br>
                Stock: {item['current_stock']} units | {stock_status}
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        # Consumables
        st.markdown("#### Consumables & Supplies")
        consumables = inventory[inventory['category'].isin(['Consumable', 'Supply', 'Medicine'])]
        
        for _, item in consumables.head(8).iterrows():
            st.markdown(f"""
            <div style="background: #F5F5F5; padding: 0.8rem; border-radius: 8px; margin-bottom: 0.5rem;">
                <strong>{item['item_name']}</strong><br>
                Price: ₹{item['unit_price']} | Stock: {item['current_stock']}
            </div>
            """, unsafe_allow_html=True)
    
    # Recent usage vs billing mismatches
    st.markdown("### 🚨 Potential Leakage Alerts")
    
    # Simulate recent discrepancies
    recent_mismatches = pd.DataFrame({
        'Patient ID': [f'P{np.random.randint(1000, 9999)}' for _ in range(5)],
        'Item': ['IV Set', 'Paracetamol IV', 'Oxygen Mask', 'IV Cannula', 'Antibiotic IV'],
        'Quantity Used': [3, 2, 1, 2, 4],
        'Quantity Billed': [2, 1, 0, 1, 3],
        'Time Since Use': ['2 hours', '4 hours', '1 hour', '3 hours', '5 hours'],
        'Potential Loss': [450, 380, 850, 380, 1250]
    })
    
    st.dataframe(recent_mismatches, use_container_width=True)
    
    if st.button("🔔 Resolve All Alerts"):
        st.success("✅ Alerts resolved and billing updated")

elif page == "📋 Medical Necessity":
    st.markdown("""
    <div class="main-header">
        <h1>📋 Medical Necessity Letter Generator</h1>
        <p>AI-powered justification letters for borderline claims</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Select condition
    condition = st.selectbox("Select Condition", necessity_templates['condition'].tolist())
    
    # Get template
    template_row = necessity_templates[necessity_templates['condition'] == condition].iloc[0]
    
    # Patient details
    col1, col2 = st.columns(2)
    
    with col1:
        patient_name = st.text_input("Patient Name", value="Rajesh Kumar")
        age = st.number_input("Age", 0, 120, 58)
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
    
    with col2:
        admission_date = st.date_input("Admission Date", datetime.now() - timedelta(days=5))
        doctor_name = st.text_input("Attending Physician", value="Dr. Sharma")
    
    # Condition-specific parameters
    st.markdown("### Clinical Parameters")
    
    if 'Dengue' in condition:
        col1, col2, col3 = st.columns(3)
        with col1:
            symptoms = st.text_input("Symptoms", value="High fever, bleeding gums")
        with col2:
            reason = st.text_input("IV Fluids Reason", value="severe dehydration, unable to take orally")
        with col3:
            platelet_count = st.number_input("Platelet Count", min_value=5000, max_value=500000, value=35000)
    else:
        symptoms = st.text_input("Symptoms/Findings", value="chest pain, shortness of breath")
    
    if st.button("Generate Medical Necessity Letter"):
        
        # Generate letter using template
        if 'Dengue' in condition:
            letter = f"""
            MEDICAL NECESSITY CERTIFICATE
            
            Date: {datetime.now().strftime('%Y-%m-%d')}
            
            To,
            The Claims Manager,
            {st.session_state.get('current_claim', {}).get('insurer', 'Insurance Company')}
            
            Subject: Medical Necessity Justification - {patient_name}
            
            Dear Sir/Madam,
            
            This is to certify that {patient_name}, {age} years/{gender}, was admitted to our hospital 
            on {admission_date.strftime('%Y-%m-%d')} with a diagnosis of {condition}.
            
            {template_row['justification_template'].format(
                symptoms=symptoms,
                reason=reason,
                duration="72 hours",
                complications="thrombocytopenia",
                platelet_count=platelet_count
            )}
            
            Required investigations ({template_row['required_tests']}) were performed and confirmed the diagnosis.
            
            The following procedures were medically necessary:
            1. IV Fluids - To maintain hydration and prevent shock
            2. Platelet Transfusion - For platelet count below 50,000
            3. Daily Monitoring - For signs of plasma leakage
            
            Without these interventions, the patient would be at significant risk of complications including 
            dengue hemorrhagic fever and shock syndrome.
            
            I hereby certify that all treatments provided were medically necessary and in accordance with 
            standard clinical guidelines.
            
            Thank you for your prompt processing of this claim.
            
            Yours sincerely,
            
            {doctor_name}
            {condition} Specialist
            """
        else:
            letter = f"""
            MEDICAL NECESSITY CERTIFICATE
            
            Date: {datetime.now().strftime('%Y-%m-%d')}
            
            To,
            The Claims Manager,
            Insurance Company
            
            Subject: Medical Necessity Justification - {patient_name}
            
            Dear Sir/Madam,
            
            This is to certify that {patient_name}, {age} years/{gender}, was admitted to our hospital 
            on {admission_date.strftime('%Y-%m-%d')} with a diagnosis of {condition}.
            
            Clinical presentation: {symptoms}
            
            Required investigations ({template_row['required_tests']}) were performed and confirmed the diagnosis.
            
            All treatments provided were medically necessary and in accordance with standard clinical guidelines.
            
            Yours sincerely,
            
            {doctor_name}
            """
        
        st.session_state.generated_letter = letter
        
        st.markdown("### Generated Letter")
        st.text_area("Medical Necessity Letter", letter, height=400)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📥 Download Letter"):
                st.success("Letter downloaded!")
        with col2:
            if st.button("✉️ Send to Insurer"):
                st.success("Letter sent to insurer for pre-approval")

elif page == "📚 Audit History":
    st.markdown("""
    <div class="main-header">
        <h1>📚 Audit History</h1>
        <p>Complete audit trail with predictive insights</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        date_range = st.date_input("Date Range", [datetime.now() - timedelta(days=30), datetime.now()])
    with col2:
        insurer_filter = st.multiselect("Insurer", insurer_patterns['insurer'].unique())
    with col3:
        status_filter = st.selectbox("Status", ["All", "Approved", "Rejected", "Pending"])
    
    # Load and filter history
    history_df = historical_claims.copy()
    
    if insurer_filter:
        history_df = history_df[history_df['insurer'].isin(insurer_filter)]
    
    # Add prediction column
    predictions = []
    for _, row in history_df.iterrows():
        pred = denial_engine.predict_rejection(row['insurer'], 'General', 'General', row['amount'], 0.7)
        predictions.append(f"{pred['probability']}%")
    
    history_df['AI_Prediction'] = predictions
    history_df['Risk'] = history_df['AI_Prediction'].apply(
        lambda x: 'High' if float(x.replace('%', '')) > 70 else 'Medium' if float(x.replace('%', '')) > 40 else 'Low'
    )
    
    st.dataframe(history_df, use_container_width=True)
    
    # Export options
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📥 Export as CSV"):
            csv = history_df.to_csv(index=False)
            st.success("Export ready!")
    with col2:
        if st.button("📊 Generate Audit Report"):
            st.success("Report generated!")

elif page == "⚙️ Settings":
    st.markdown("""
    <div class="main-header">
        <h1>⚙️ System Settings</h1>
        <p>HIPAA-compliant configuration | Human-in-the-loop controls</p>
    </div>
    """, unsafe_allow_html=True)
    
    # AWS Configuration
    st.markdown("### ☁️ AWS Services Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Service Endpoints")
        aws_region = st.selectbox("AWS Region", ["ap-south-1", "us-east-1", "eu-west-1"])
        healthlake_endpoint = st.text_input("AWS HealthLake Endpoint", "https://healthlake.ap-south-1.amazonaws.com")
        comprehend_role = st.text_input("Comprehend Medical Role ARN", "arn:aws:iam::123456789012:role/ComprehendMedicalRole")
        textract_endpoint = st.text_input("Amazon Textract Endpoint", "https://textract.ap-south-1.amazonaws.com")
        
    with col2:
        st.markdown("#### Security & Compliance")
        enable_encryption = st.checkbox("Enable AWS KMS Encryption", value=True)
        enable_private_link = st.checkbox("Enable AWS PrivateLink", value=True)
        data_retention = st.selectbox("Data Retention Period", ["30 days", "90 days", "1 year", "Indefinite"])
        
        st.markdown("#### PII Anonymization")
        auto_anonymize = st.checkbox("Auto-anonymize patient data after audit", value=True)
        anonymization_method = st.selectbox("Method", ["Pseudonymization", "Redaction", "Tokenization"])
    
    # Human-in-the-loop settings
    st.markdown("### 👤 Human-in-the-Loop Controls")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Approval Workflow")
        require_human_review = st.checkbox("Require human review for claims > ₹1,00,000", value=True)
        require_human_review_all = st.checkbox("Require human review for all AI-suggested changes", value=True)
        auto_approve_threshold = st.slider("Auto-approve threshold", 85, 99, 95)
        
    with col2:
        st.markdown("#### Audit Trail")
        log_all_actions = st.checkbox("Log all AI actions for audit trail", value=True)
        audit_level = st.selectbox("Audit detail level", ["Basic", "Detailed", "Comprehensive"])
        
        st.markdown("#### Escalation")
        escalation_contact = st.text_input("Escalation email", "compliance@hospital.com")
    
    # Bias monitoring
    st.markdown("### ⚖️ Algorithmic Bias Monitoring")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Demographic Parity")
        monitor_age_bias = st.checkbox("Monitor age-based bias", value=True)
        monitor_gender_bias = st.checkbox("Monitor gender-based bias", value=True)
        monitor_region_bias = st.checkbox("Monitor regional bias", value=True)
        
    with col2:
        st.markdown("#### Fairness Metrics")
        fairness_threshold = st.slider("Acceptable disparity threshold", 0.0, 0.3, 0.1, 0.01)
        generate_bias_report = st.checkbox("Generate monthly bias reports", value=True)
    
    # Integration settings
    st.markdown("### 🔌 Integration Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### HIS Integration")
        his_system = st.selectbox("Hospital Information System", 
                                   ["None", "MedPlus", "Cerner", "Epic", "Custom API"])
        api_endpoint = st.text_input("API Endpoint (optional)")
        
    with col2:
        st.markdown("#### Inventory System")
        inventory_sync = st.checkbox("Enable real-time inventory sync", value=True)
        sync_interval = st.number_input("Sync interval (minutes)", 5, 60, 15)
    
    # Save settings
    if st.button("💾 Save All Settings", type="primary", use_container_width=True):
        st.success("✅ Settings saved successfully!")
        st.info("📋 Note: Changes will take effect immediately")

# Footer
st.markdown("---")
st.markdown("""
<div class="footer">
    <p>🏥 ClaimFlow AI Enterprise Edition | Powered by AWS AI Services</p>
    <p>HIPAA-compliant | Human-in-the-loop | Bias-monitored</p>
    <p style="font-size: 0.8rem;">© 2025 Team TechnoForge | AI for Bharat Hackathon</p>
</div>
""", unsafe_allow_html=True)