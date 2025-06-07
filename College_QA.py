import streamlit as st
import pandas as pd
import google.generativeai as genai
import os

# ✅ BEST PRACTICE — either use env or secrets.toml
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or "AIzaSyCHrPFUWdGbZAcV82nTm8WMhe9HDRwd5rg"
genai.configure(api_key=GEMINI_API_KEY)


# Load Excel data
@st.cache_data
def load_data():
    xls = pd.ExcelFile("C:/Users/jayal/Downloads/greenfield_college_3years_data.xlsx", engine="openpyxl")
    data = {
        "students": xls.parse("Students"),
        "teachers": xls.parse("Teachers"),
        "courses": xls.parse("Courses"),
    }
    return data

data = load_data()

# Show data previews
st.title("🎓 Greenfield College – Q&A Assistant")
with st.expander("📚 View Data"):
    st.subheader("Students")
    st.dataframe(data["students"])
    st.subheader("Teachers")
    st.dataframe(data["teachers"])
    st.subheader("Courses")
    st.dataframe(data["courses"])

# User question
st.markdown("## ❓ Ask a question about the college")
user_question = st.text_area("Ask your question (e.g., Who teaches Chemistry? How many students were enrolled in 2022?)")

if st.button("🔍 Get Answer") and user_question:
    # Format all data into a context for Gemini
    context = ""
    for name, df in data.items():
        context += f"\nSheet: {name.title()}\n"
        context += df.to_csv(index=False)

    prompt = f"""
You are a helpful assistant for answering questions based on structured college data.
Here is the dataset:\n{context}\n
Now answer this question clearly and accurately:\n{user_question}
"""

    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    st.markdown("### 📌 Answer")
    st.write(response.text)
