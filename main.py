from parser import parse_query
from query_builder import generate_sql

def main():
    print("--- NLP to SQL Engine v2.0 Initialized ---\n")
    
    queries = [
        "Find senior developers with a salary over 80000.",
        "Show me managers in Pune with salary under 50000.",
        "Get developers in Nagpur with exactly 60000 salary."
    ]
    
    for q in queries:
        print(f"User Query: '{q}'")
        
        parsed_data = parse_query(q)
        print(f"Parsed Data: {parsed_data}")
        
        sql_query = generate_sql(parsed_data)
        print(f"Generated SQL: {sql_query}\n")
        print("-" * 50)

if __name__ == "__main__":
    main()