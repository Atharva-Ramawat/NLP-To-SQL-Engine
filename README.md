# 🔍  NLP-to-SQL Engine

![Python](https://img.shields.io/badge/Python-3.x-blue.svg)
![NLTK](https://img.shields.io/badge/NLTK-Natural_Language_Toolkit-green.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-Web_Framework-red.svg)
![License](https://img.shields.io/badge/License-MIT-purple.svg)

## 📌 Overvie
**Text2Query Core** is a deterministic, rule-based natural language processing engine that translates human language into structured SQL queries. 

Unlike modern generative AI wrappers, this project is built entirely from the ground up using **traditional NLP architectures**. It operates 100% locally with zero external API dependencies, ensuring total data privacy, instantaneous execution, and highly predictable state-machine routing. 

Currently, the engine is configured to query an `employees` database, but the semantic parser can be mapped to any relational schema.

## ✨ Core Features
* **Zero-Shot LLM Dependency:** Runs entirely on local rule-based dictionaries and statistical tagging.
* **Semantic Entity Extraction:** Isolates highly relevant database columns (cities, roles, levels) while safely ignoring conversational filler.
* **Comparative Operator Parsing:** Intelligently maps English comparator words (*"over"*, *"under"*, *"exactly"*) to SQL math operators (`>`, `<`, `=`) and binds them to numeric data.
* **Automated Plural Handling:** Uses linguistic lemmatization to reduce nouns to their base forms, drastically reducing the size of required database mapping dictionaries.
* **Interactive UI:** Features a clean, local web interface built with Streamlit to visualize the translation pipeline in real-time.

---

## 🧠 Under the Hood: The NLP Architecture

To achieve accurate translation without a Large Language Model, this engine utilizes a multi-stage traditional NLP pipeline powered by the **Natural Language Toolkit (NLTK)**:

1. **Tokenization (`nltk.word_tokenize`):** The raw user string is stripped of capitalization and broken down into an iterable array of distinct linguistic tokens.
2. **Part-of-Speech (POS) Tagging (`nltk.pos_tag`):** Using the Averaged Perceptron Tagger, the engine grammatically classifies every token. It explicitly targets Nouns (`NN`, `NNS`, `NNP`) and Adjectives (`JJ`) as potential database entities, and Cardinal Digits (`CD`) as numeric filters.
3. **Lemmatization (`WordNetLemmatizer`):** Extracted nouns are passed through the WordNet lexical database to find their morphological root (e.g., converting "managers" to "manager"). This prevents exact-string mismatch errors in the SQL builder.
4. **State Machine Logic:** A custom Python parser watches for contextual math triggers (e.g., "greater than") and alters the state of the next extracted integer, mapping them together as a unified numeric condition.

---

## 🚀 Installation & Setup

**1. Clone the repository and navigate to the directory:**
```bash
git clone [https://github.com/yourusername/nlp-to-sql-engine.git](https://github.com/yourusername/nlp-to-sql-engine.git)
cd nlp-to-sql-engine
```

**2. Set up a virtual environment:**
```bash
python -m venv venv
# On Windows: venv\Scripts\activate
# On Mac/Linux: source venv/bin/activate
```

**3. Install dependencies:**
```bash
pip install -r requirements.txt
```

**4. Launch the application:**
```bash
streamlit run app.py
```

---

## 🧪 Example Queries

Try pasting these into the Streamlit interface to see the engine in action:

* **Categorical Mapping:** > *"Find me the senior developers in Pune."*
  👉 `SELECT * FROM employees WHERE level = 'Senior' AND role = 'Developer' AND city = 'Pune';`

* **Comparative Math Logic:** > *"Show managers with a salary over 80000."*
  👉 `SELECT * FROM employees WHERE role = 'Manager' AND salary > 80000;`

* **Graceful Failure (Out of Domain):** > *"Find me a cheap hotel with a swimming pool."*
  👉 `SELECT * FROM employees;` *(Safely ignores unmapped entities).*

---
