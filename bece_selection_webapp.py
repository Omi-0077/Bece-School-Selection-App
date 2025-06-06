import streamlit as st
import pandas as pd
from fpdf import FPDF
import io

# --- Load School Data ---
@st.cache_data
def load_school_data():
    # Use your official Excel file here
    df = pd.read_excel("FINAL 2025 SECOND CYCLE SCHOOLS REGISTER.xlsx", sheet_name=None)
    all_schools = pd.concat(df.values(), ignore_index=True)
    all_schools.dropna(subset=["SCHOOL CODE", "SCHOOL NAME"], inplace=True)
    return all_schools

schools_df = load_school_data()

# --- Helper Functions for School Filtering and Compliance ---
def filter_by_guidelines(df, aggregate, gender, region_prefs, career, tvet_only=False, stem_only=False):
    # 1. Filter by region(s), aggregate/cutoff, and gender
    filtered = df[
        (df["REGION"].isin(region_prefs)) &
        (df["GENDER"].str.contains(gender, case=False, na=False)) &
        (df["CUTOFF"].apply(lambda x: aggregate <= int(str(x).split("-")[1]) if pd.notna(x) and "-" in str(x) else True))
    ]
    # 2. Optionally filter by TVET/STEM
    if tvet_only:
        filtered = filtered[filtered["CATEGORY"].isin(["A", "B", "C"])]
        filtered = filtered[filtered["SCHOOL TYPE"].str.contains("TVET|TECHNICAL", case=False, na=False)]
    if stem_only:
        filtered = filtered[filtered["PROGRAMMES OFFERED"].str.contains("SCIENCE|STEM", case=False, na=False)]
    # 3. Optionally filter by career interest
    if career:
        filtered = filtered[filtered["PROGRAMMES OFFERED"].str.contains(career, case=False, na=False)]
    return filtered

def validate_selections(main_choices, alt_choices):
    # Ensure guideline compliance
    cats = main_choices["CATEGORY"].tolist()
    catA = cats.count("A")
    catB = cats.count("B")
    if catA > 1:
        return False, "Cannot select more than one Category A school."
    if catB > 2:
        return False, "Cannot select more than two Category B schools."
    # Alt choices: must be from Appendix 3
    if not all("APPENDIX 3" in str(row) for row in alt_choices["REMARKS"].tolist()):
        return False, "Alternative schools must be from Appendix 3."
    return True, ""

# --- Streamlit Web UI ---
st.set_page_config(page_title="BECE School Selection App 2025", layout="centered")
st.title("BECE School Selection Guidance 2025")
st.markdown(
    """
    Welcome! This assistant guides BECE students and parents to select schools in line with GES/TVET 2025 rules.
    """
)

# Step 1: User Inputs
with st.form("user_inputs"):
    st.header("Step 1: Your Details")
    name = st.text_input("Student Name")
    gender = st.selectbox("Gender", ["Male", "Female"])
    predicted_aggregate = st.slider("Predicted BECE Aggregate", 6, 30, 12)
    region_prefs = st.multiselect("Select up to 3 preferred regions", sorted(schools_df["REGION"].unique()), max_selections=3)
    career = st.text_input("Career Interest (e.g., Science, Business, Technical, STEM, etc.)")
    tvet_only = st.checkbox("I want only TVET/Technical schools")
    stem_only = st.checkbox("I want only STEM/Science-focused schools")
    st.info("Next, you'll select your 7 schools (5 main, 2 alternatives).")
    submit_btn = st.form_submit_button("Show School Options")

if submit_btn:
    st.header("Step 2: School Selection")
    filtered_schools = filter_by_guidelines(
        schools_df, predicted_aggregate, gender, region_prefs, career, tvet_only, stem_only
    )
    # Main Choices
    st.subheader("Select Your 5 Main Schools (Order Matters)")
    main_choices = st.dataframe(
        filtered_schools[["SCHOOL NAME", "SCHOOL CODE", "CATEGORY", "REGION", "BOARDING", "PROGRAMMES OFFERED", "CUTOFF"]].reset_index(drop=True),
        use_container_width=True,
        hide_index=True
    )
    selected_main = st.multiselect(
        "Pick 5 main schools by SCHOOL CODE (in order of preference):",
        filtered_schools["SCHOOL CODE"], max_selections=5
    )
    # Alt Choices
    st.subheader("Select 2 Alternative Schools (Appendix 3 only)")
    appendix3_schools = filtered_schools[filtered_schools["REMARKS"].str.contains("APPENDIX 3", na=False)]
    alt_choices = st.dataframe(
        appendix3_schools[["SCHOOL NAME", "SCHOOL CODE", "CATEGORY", "REGION", "BOARDING", "PROGRAMMES OFFERED", "CUTOFF"]].reset_index(drop=True),
        use_container_width=True,
        hide_index=True
    )
    selected_alt = st.multiselect(
        "Pick 2 alternative schools by SCHOOL CODE (Appendix 3):",
        appendix3_schools["SCHOOL CODE"], max_selections=2
    )

    if st.button("Validate and Download Selection as PDF"):
        # Build chosen DataFrames
        main_df = filtered_schools[filtered_schools["SCHOOL CODE"].isin(selected_main)].copy()
        alt_df = appendix3_schools[appendix3_schools["SCHOOL CODE"].isin(selected_alt)].copy()
        valid, msg = validate_selections(main_df, alt_df)
        if not valid:
            st.error(msg)
        elif main_df.shape[0] != 5 or alt_df.shape[0] != 2:
            st.error("You must select exactly 5 main and 2 alternative schools.")
        else:
            st.success("Selections are valid! Generating your PDF form...")
            # --- PDF Generation ---
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 16)
            pdf.cell(200, 10, "2025 BECE School Selection Form", ln=1, align="C")
            pdf.set_font("Arial", "", 12)
            pdf.cell(100, 10, f"Name: {name}", ln=1)
            pdf.cell(100, 10, f"Gender: {gender}", ln=1)
            pdf.cell(100, 10, f"Predicted Aggregate: {predicted_aggregate}", ln=1)
            pdf.cell(100, 10, f"Career Interest: {career}", ln=1)
            pdf.ln(5)
            for idx, row in main_df.iterrows():
                pdf.multi_cell(0, 10, f"{idx+1}. {row['SCHOOL NAME']} | Code: {row['SCHOOL CODE']} | Category: {row['CATEGORY']} | Boarding: {row['BOARDING']} | Programs: {row['PROGRAMMES OFFERED']} | Cut-off: {row['CUTOFF']}", border=1)
            pdf.ln(3)
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, "Alternative Schools (Appendix 3):", ln=1)
            pdf.set_font("Arial", "", 12)
            for idx, row in alt_df.iterrows():
                pdf.multi_cell(0, 10, f"{idx+6}. {row['SCHOOL NAME']} | Code: {row['SCHOOL CODE']} | Category: {row['CATEGORY']} | Boarding: {row['BOARDING']} | Programs: {row['PROGRAMMES OFFERED']} | Cut-off: {row['CUTOFF']}", border=1)
            pdf.ln(2)
            pdf.set_font("Arial", "I", 11)
            pdf.cell(0, 10, "Double-check your choices with a teacher or guardian. Best of luck!", ln=1)
            pdf_output = io.BytesIO()
            pdf.output(pdf_output)
            st.download_button(
                label="📄 Download PDF Form",
                data=pdf_output.getvalue(),
                file_name="BECE_School_Selection_2025.pdf"
            )

st.markdown("---")
st.caption("Strictly adheres to the 2025 GES/TVET School Selection Guidelines. For details, see the full guideline in the help section.")