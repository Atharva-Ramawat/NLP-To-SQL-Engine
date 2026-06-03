import streamlit as st
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import spacy
import spacy_streamlit
from sklearn.decomposition import PCA
import numpy as np
import plotly.express as px
import pandas as pd
import seaborn as sns
import nltk
from collections import Counter

@st.cache_resource
def load_spacy_model():
    try:
        return spacy.load("en_core_web_sm")
    except Exception as e:
        st.error(f"Failed to load spaCy model: {e}")
        return None

def render_wordcloud(text):
    if not text.strip():
        st.warning("No text to generate word cloud.")
        return
    
    # Generate word cloud
    wordcloud = WordCloud(width=800, height=400, background_color='white', colormap='viridis').generate(text)
    
    # Display the generated image
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis("off")
    st.pyplot(fig)

def render_pos_barchart(text):
    tokens = nltk.word_tokenize(text)
    tagged = nltk.pos_tag(tokens)
    
    tags = [tag for word, tag in tagged]
    tag_counts = Counter(tags)
    
    if not tag_counts:
         st.warning("No tokens found.")
         return
         
    df = pd.DataFrame(tag_counts.items(), columns=["POS Tag", "Count"]).sort_values(by="Count", ascending=False)
    
    fig = px.bar(df, x="POS Tag", y="Count", title="Part of Speech (POS) Tag Frequencies", color="Count", color_continuous_scale="blues")
    st.plotly_chart(fig, use_container_width=True)

def render_ner_and_tree(text, nlp):
    if not nlp:
        st.error("spaCy model is not loaded.")
        return
    
    doc = nlp(text)
    from spacy import displacy
    import warnings
    
    st.subheader("Named Entity Recognition (NER)")
    if doc.ents:
        ner_html = displacy.render(doc, style="ent")
        st.markdown(ner_html, unsafe_allow_html=True)
    else:
        st.info("🔍 No standard named entities (persons, orgs, locations) detected. The small `en_core_web_sm` model may miss informal city names — try phrasing like \"developers in Pune, India\".")
    
    st.subheader("Dependency Syntax Tree")
    st.markdown("<br>", unsafe_allow_html=True)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dep_html = displacy.render(doc, style="dep", options={'distance': 100})
    if dep_html:
        scrolling_div = f"<div style='overflow-x: auto; white-space: nowrap;'>{dep_html}</div>"
        st.write(scrolling_div, unsafe_allow_html=True)
    else:
        st.info("No dependencies found.")

def render_word_embeddings(text, nlp):
    if not nlp:
        return
    
    doc = nlp(text)
    words = []
    vectors = []
    
    for token in doc:
        if not token.is_stop and not token.is_punct and token.has_vector:
            words.append(token.text)
            vectors.append(token.vector)
            
    if len(words) < 3:
        st.info("Not enough meaningful words with vectors to perform PCA. (Try a longer sentence)")
        return
        
    vectors = np.array(vectors)
    
    # Perform PCA down to 2 dimensions
    pca = PCA(n_components=min(2, len(words)))
    try:
         vectors_2d = pca.fit_transform(vectors)
    except Exception as e:
         st.error(f"PCA computation failed: {e}")
         return
         
    df = pd.DataFrame({
        "x": vectors_2d[:, 0],
        "y": vectors_2d[:, 1] if vectors_2d.shape[1] > 1 else np.zeros(len(vectors_2d)),
        "word": words
    })
    
    fig = px.scatter(df, x="x", y="y", text="word", title="Word Embeddings (PCA space)")
    fig.update_traces(textposition='top center', marker=dict(size=12, color='DarkSlateGrey'))
    st.plotly_chart(fig, use_container_width=True)

def render_attention_heatmap(parsed_data, text):
    """ Simulate an attention heatmap based on keyword/schema matching. """
    tokens = nltk.word_tokenize(text)
    
    # give weight to words found in parsed constraints
    weights = []
    
    # Extract known targets
    important_words = set()
    for kw in parsed_data.get("keywords", []):
         important_words.add(kw["word"].lower())
    for grp in parsed_data.get("group_by", []):
         important_words.add(grp.lower())
    for ord in parsed_data.get("order_by", []):
         important_words.add(ord["word"].lower())
         
    for token in tokens:
        w_lower = token.lower()
        if w_lower in important_words:
            weights.append(0.9) # High Attention for captured keywords
        elif w_lower in ["where", "filter", "group", "by", "order", "sort", "limit"]:
            weights.append(0.6) # Medium attention for structural SQL hints
        else:
            weights.append(0.1) # Low attention for stop words or ignored words
            
    if not weights:
         return
         
    # Visualize as heatmap
    arr = np.array(weights).reshape(1, -1)
    
    fig, ax = plt.subplots(figsize=(max(len(tokens)*0.5, 5), 2))
    sns.heatmap(arr, annot=np.array(tokens).reshape(1, -1), fmt="", cmap="YlOrRd", cbar=True, ax=ax, xticklabels=False, yticklabels=False)
    st.pyplot(fig)

def render_topic_modeling(text, nlp):
    """ Provide context for the topic of the query. """
    if not nlp: return
    doc = nlp(text)
    
    topics = [chunk.text for chunk in doc.noun_chunks]
    
    if not topics:
         st.info("No discernible topic chunks found.")
         return
         
    st.write("**Extracted Noun Chunks (Candidate Topics):**")
    for t in topics:
        st.button(t, key=f"topic_{t}")
    
    st.markdown("**(Note: Traditional Topic Modeling (LDA) requires a large document corpus. Here we display syntactic noun chunks bounding the context of the query)**")
