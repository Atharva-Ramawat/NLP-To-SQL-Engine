def generate_sql(parsed_data):
    """
    Maps text entities to string columns and numeric entities to math conditions.
    """
    keywords = parsed_data['keywords']
    numerics = parsed_data['numerics']
    
    column_mapping = {
        "nagpur": "city",
        "mumbai": "city",
        "pune": "city",
        "developers": "role",
        "developer": "role",
        "manager": "role",
        "senior": "level",
        "junior": "level",
        "salary": "salary" 
    }

    conditions = []

    # 1. Handle String / Categorical Matchers
    for word in keywords:
        if word in column_mapping:
            column = column_mapping[word]
            if column != "salary": # Don't treat salary as a string match
                conditions.append(f"{column} = '{word.capitalize()}'")

    # 2. Handle Numerical / Math Matchers
    # For this prototype, if they mention 'salary' and provide numbers, we link them
    if "salary" in keywords and numerics:
        for num_cond in numerics:
            op = num_cond['operator']
            val = num_cond['value']
            conditions.append(f"salary {op} {val}")

    base_query = "SELECT * FROM employees"

    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)

    return base_query + ";"