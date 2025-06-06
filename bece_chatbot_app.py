
import streamlit as st
import pandas as pd
from fpdf import FPDF
import io

# Load school data from Excel
@st.cache_data
def load_data():
    df = pd.read_excel("bece_schools_2025.xlsx", sheet_name=None)
    school_data = pd.concat(df.values(), ignore_index=True)
    school_data.dropna(subset=["SCHOOL CODE", "SCHOOL NAME"], inplace=True)
    return school_data

schools = load_data()

# Chat UI
st.title("BECE School Selection Assistant 2025")
st.markdown("Helping students, parents, and teachers choose 7 schools based on WAEC guidelines.")

with st.form("school_selection"):
    name = st.text_input("Student Name")
    gender = st.selectbox("Gender", ["Male", "Female"])
    predicted_aggregate = st.slider("Predicted BECE Aggregate", 6, 30, 12)
    region_preferences = st.multiselect("Select up to 3 preferred regions", schools["REGION"].unique(), max_selections=3)
    career = st.text_input("What career are you most interested in? (e.g., Scientist, Accountant, Nurse)")
    submit = st.form_submit_button("Get School Recommendations")

if submit:
    # Filter logic (basic)
    recommended = schools[schools["REGION"].isin(region_preferences)]
    recommended = recommended[recommended["CATEGORY"].isin(["A", "B", "C", "D"])]
    recommended = recommended.head(20)

    st.subheader("📋 Recommended Schools")
    final_7 = recommended.sample(7).sort_values("CATEGORY")
    st.dataframe(final_7[["SCHOOL NAME", "SCHOOL CODE", "CATEGORY", "BOARDING", "PROGRAMMES OFFERED"]])

    if st.button("Generate PDF School Selection Form"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="2025 BECE School Selection Form", ln=True, align="C")
        pdf.ln(10)
        pdf.cell(100, 10, txt=f"Name: {name}", ln=True)
        pdf.cell(100, 10, txt=f"Gender: {gender}", ln=True)
        pdf.cell(100, 10, txt=f"Predicted Aggregate: {predicted_aggregate}", ln=True)
        pdf.cell(100, 10, txt=f"Career Goal: {career}", ln=True)
        pdf.ln(5)

        for i, row in final_7.iterrows():
            pdf.multi_cell(0, 10, txt=f"{row['SCHOOL NAME']} | Code: {row['SCHOOL CODE']} | Category: {row['CATEGORY']} | Boarding: {row['BOARDING']}\nPrograms: {row['PROGRAMMES OFFERED']}", border=1)

        pdf_output = io.BytesIO()
        pdf.output(pdf_output)
        st.download_button(label="📄 Download PDF Form", data=pdf_output.getvalue(), file_name="BECE_School_Selection_2025.pdf")
