import nltk

nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)
nltk.download('averaged_perceptron_tagger_eng', quiet=True)

def parse_query(user_input):
    """
    Extracts standard entities AND numerical filters based on comparative words.
    """
    tokens = nltk.word_tokenize(user_input.lower())
    tagged_tokens = nltk.pos_tag(tokens)
    
    search_parameters = []
    numeric_conditions = []
    
    # Dictionary mapping English words to SQL math operators
    operator_map = {
        'over': '>', 'greater': '>', 'more': '>', 'above': '>',
        'under': '<', 'less': '<', 'below': '<',
        'exactly': '=', 'equal': '='
    }
    
    current_operator = '=' # Default to exact match if no word is found
    
    for word, tag in tagged_tokens:
        # 1. State Tracking: If we see a math word, remember it
        if word in operator_map:
            current_operator = operator_map[word]
            
        # 2. Number Parsing: NLTK tags numbers as 'CD' (Cardinal Digit)
        elif tag == 'CD' or word.isnumeric():
            numeric_conditions.append({
                "operator": current_operator,
                "value": word
            })
            current_operator = '=' # Reset the state machine after using the operator
            
        # 3. Standard Entity Extraction (ignoring our operator words)
        elif tag in ('NN', 'NNS', 'NNP', 'JJ') and word not in operator_map:
            search_parameters.append(word)
            
    return {
        "keywords": search_parameters,
        "numerics": numeric_conditions
    }