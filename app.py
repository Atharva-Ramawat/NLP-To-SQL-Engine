import streamlit as st
from parser import parse_query
from query_builder import generate_sql

# Set up the page layout
st.set_page_config(page_title="NLP to SQL Engine", page_icon="🔍", layout="centered")

# Header Section
st.title("🔍 NLP-to-SQL Translation Engine")
st.markdown("""
This engine translates natural language into SQL queries using **traditional NLP (NLTK)**. 
It relies on Part-of-Speech tagging, lemmatization, and rule-based state machines—**100% local, no LLMs required.**
""")

st.divider()

# Input Section
user_input = st.text_input(
    "Ask a question about the employee database:", 
    placeholder="e.g., Find senior developers in Pune with a salary over 80000"
)

# Generation Button
if st.button("Generate SQL", type="primary"):
    if user_input.strip():
        with st.spinner("Analyzing text with NLTK..."):
            # Step 1: Parse the natural language
            parsed_data = parse_query(user_input)
            
            # Step 2: Build the SQL string
            sql_query = generate_sql(parsed_data)
            
            # Output Section
            st.success("Query Generated Successfully!")
            
            # Display the final SQL in a nice code block
            st.subheader("Generated SQL Query")
            st.code(sql_query, language="sql")
            
            # Provide an expander to show the "under the hood" NLP logic (Great for portfolios)
            with st.expander("🛠️ See how the NLP Engine parsed this"):
                st.write("**Extracted Entities & Math Logic:**")
                st.json(parsed_data)
    else:
        st.warning("Please enter a query first.")