import streamlit as st
import logging
from parser import parse_query
from query_builder import generate_sql
import visualizers

# Standardize logging configuration for the production web app
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configure Streamlit page
st.set_page_config(page_title="NLP to SQL Engine", page_icon="🔍", layou="centered")

# Load NLP Model
nlp = visualizers.load_spacy_model()

# Header Section
st.title("NLP-to-SQL Engine")
st.markdown("""
This engine securely translates natural language into strictly **parameterized SQL queries** using traditional NLP.
It relies on NLTK for POS-tagging, stopword filtering, and math state machines.
""")

st.divider()

user_input = st.text_input(
    "Ask a question about the employee database:", 
    placeholder="e.g., Find senior developers in Pune with a salary over 80,000"
)

if st.button("Generate SQL", type="primary"):
    if user_input.strip():
        with st.spinner("Analyzing text and securing query..."):
            try:
                # 1. Execute Text Parsing
                logger.info(f"Processing Request: {user_input}")
                parsed_data = parse_query(user_input)
                
                # 2. Build Safe Parameterized SQL
                sql_query, sql_params = generate_sql(parsed_data)
                
                # Render Safe Output Formats
                st.success("Query Securley Translated!")
                
                # Display base query
                st.subheader("Base Secure SQL Query String")
                st.code(sql_query, language="sql")
                
                # Display parameterized isolated variables
                st.subheader("Isolated Statement Parameters")
                st.info(f"Arguments: {sql_params}")
                
                # Expandable diagnostics for visibility
                with st.expander("See how the NLP Engine parsed this", expanded=True):
                    
                    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
                        "Data JSON", 
                        "Word Cloud & POS", 
                        "Tree & NER", 
                        "Embeddings", 
                        "Attention", 
                        "Topics"
                    ])
                    
                    with tab1:
                        st.write("**Processed Entities & Numerics:**")
                        st.json(parsed_data)
                        
                    with tab2:
                        visualizers.render_wordcloud(user_input)
                        st.divider()
                        visualizers.render_pos_barchart(user_input)
                        
                    with tab3:
                        visualizers.render_ner_and_tree(user_input, nlp)
                        
                    with tab4:
                        visualizers.render_word_embeddings(user_input, nlp)
                        
                    with tab5:
                        st.write("**Simulated Attention Heatmap:**")
                        visualizers.render_attention_heatmap(parsed_data, user_input)
                        
                    with tab6:
                        visualizers.render_topic_modeling(user_input, nlp)
                    
            except ValueError as ve:
                logger.warning(f"Value Error processed safely: {ve}")
                st.warning(f"Could not translate your query securely: {ve}")
            except Exception as e:
                logger.error(f"Unexpected crash preventing SQL generation: {e}", exc_info=True)
                st.error(f"A system error occurred while generating the safe query: {e}")
    else:
        st.warning("Please enter a query about the database to start.")
