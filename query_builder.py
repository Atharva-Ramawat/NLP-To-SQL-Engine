import logging
from typing import Dict, Any, Tuple, List

logger = logging.getLogger(__name__)

# Expanded Schema Mapping for Medium-Level Queries
SCHEMA_MAPPING = {
    # --- Geographic (City) ---
    "nagpur": "city",
    "mumbai": "city",
    "pune": "city",
    "bangalore": "city",
    "hyderabad": "city",
    "delhi": "city",
    "chennai": "city",
    "noida": "city",
    "city": "city",
    "cities": "city",

    # --- Departments ---
    "engineering": "department",
    "sales": "department",
    "marketing": "department",
    "hr": "department",
    "finance": "department",
    "it": "department",
    "department": "department",
    "team": "department",

    # --- Roles & Specializations ---
    "developers": "role",
    "developer": "role",
    "managers": "role",
    "manager": "role",
    "analyst": "role",
    "scientists": "role",
    "engineer": "role",
    "devops": "role",
    "testers": "role",
    "role": "role",
    "roles": "role",

    # --- Seniority & Levels ---
    "senior": "level",
    "junior": "level",
    "lead": "level",
    "intern": "level",
    "fresher": "level",
    "director": "level",
    "level": "level",

    # --- Employment Status & Work Mode ---
    "remote": "work_mode",
    "hybrid": "work_mode",
    "onsite": "work_mode",
    "active": "status",
    "inactive": "status",
    "resigned": "status",
    "fired": "status",

    # --- Quantitative / Numeric Synonyms ---
    "salary": "salary",
    "pay": "salary",
    "compensation": "salary",
    "bonus": "bonus",
    "experience": "experience",
    "years": "experience",
    "tenure": "experience",
    "rating": "performance_score",
    "score": "performance_score",
    "performance": "performance_score",

    # --- Target Entities / Wildcards ---
    "employees": "*",
    "people": "*",
    "staff": "*",
    "workers": "*"
}

NUMERIC_COLUMNS = {"salary", "experience", "bonus", "performance_score"} 

def generate_sql(parsed_data: Dict[str, Any]) -> Tuple[str, List[Any]]:
    logger.info("Generating fully optimized safe SQL structure.")
    
    keywords = parsed_data.get('keywords', [])
    numerics = parsed_data.get('numerics', [])
    aggregations = parsed_data.get('aggregations', [])
    group_items = parsed_data.get('group_by', [])
    order_items = parsed_data.get('order_by', [])
    limit_val = parsed_data.get('limit', None)

    ir = {
        "filters": {"type": "OR", "groups": []},
        "numeric_filters": [],
        "group_by": [],
        "aggregations": [],
        "having": [],
        "order_by": [],
        "limit": limit_val
    }

    # 1. Group By (Dimensions Only)
    for col in group_items:
        c = SCHEMA_MAPPING.get(col)
        # Dynamically ensure we ONLY extract bare schema labels and not filter values (e.g., 'city' = safe, 'pune' = reject)
        if c and (col == c or col == c + "s" or col == "cities"):
            if c not in NUMERIC_COLUMNS and c != "*" and c not in ir["group_by"]:
                ir["group_by"].append(c)

    # 2. Aggregations (Measures Only)
    agg_target_col = None
    
    unique_aggs = []
    for agg in aggregations:
        target = agg["target"]
        func = agg["func"]
        
        c = SCHEMA_MAPPING.get(target) if target != "*" else "*"
        if not c and target != "*":
            continue
            
        if func == "TOTAL_OR_COUNT":
            func = "SUM" if c in NUMERIC_COLUMNS else "COUNT"
            
        # Enforce measure rules (SUM, AVG, MIN, MAX only on numerics)
        if func in ("SUM", "AVG", "MIN", "MAX") and c not in NUMERIC_COLUMNS:
            continue
            
        item = {"func": func, "field": c}
        if item not in unique_aggs:
            unique_aggs.append(item)
            if c != "*":
                agg_target_col = c

    ir["aggregations"] = unique_aggs

    # 3. Filters (Dimensions) -> Handling cross-column OR Tree
    keyword_groups = [[]]
    for kw in keywords:
        if kw.get('logic') == "OR":
            keyword_groups.append([kw])
        else:
            keyword_groups[-1].append(kw)
            
    for grp in keyword_groups:
        col_clusters = {}
        for kw in grp:
            word = kw['word'].lower()
            negated = kw['negated']
            
            if word in SCHEMA_MAPPING:
                column = SCHEMA_MAPPING[word]
                
                # Bare Dimension Injection
                if column not in NUMERIC_COLUMNS and column != "*":
                    if word == column or word == column + "s" or word == "cities":
                        if column not in ir["group_by"]:
                            ir["group_by"].append(column)
                        continue
                        
                    if column not in col_clusters:
                        col_clusters[column] = {"include": [], "exclude": []}
                        
                    if negated and word not in col_clusters[column]["exclude"]:
                        col_clusters[column]["exclude"].append(word)
                    elif not negated and word not in col_clusters[column]["include"]:
                        col_clusters[column]["include"].append(word)
                        
        grp_filters = []
        for col, rules in col_clusters.items():
            if rules["include"]:
                op = "=" if len(rules["include"]) == 1 else "IN"
                val = rules["include"][0] if len(rules["include"]) == 1 else rules["include"]
                grp_filters.append({"field": col, "op": op, "value": val})
            if rules["exclude"]:
                op = "!=" if len(rules["exclude"]) == 1 else "NOT IN"
                val = rules["exclude"][0] if len(rules["exclude"]) == 1 else rules["exclude"]
                grp_filters.append({"field": col, "op": op, "value": val})
                
        if grp_filters:
            ir["filters"]["groups"].append(grp_filters)

    # 4. Filters (Measurements / Having)
    for num_cond in numerics:
        explicit_col = num_cond.get('target_col')
        target = explicit_col if explicit_col else agg_target_col
        if not target:
            continue
            
        op = num_cond.get('operator')
        neg = num_cond.get('negated', False)
        val = num_cond.get('value')
        
        if op == "BETWEEN":
            real_op = "NOT BETWEEN" if neg else "BETWEEN"
        else:
            invert_map = {'>': '<=', '<': '>=', '=': '!=', '>=': '<', '<=': '>'}
            real_op = invert_map.get(op, '!=') if neg else op
            
        # Ascertain if this is WHERE or HAVING
        is_having = False
        mapped_func = None
        if ir["group_by"]:
            for a in ir["aggregations"]:
                if a["field"] == target:
                    is_having = True
                    mapped_func = a["func"]
                    break
                    
        if is_having:
            ir["having"].append({"func": mapped_func, "field": target, "op": real_op, "value": val})
        else:
            ir["numeric_filters"].append({"field": target, "op": real_op, "value": val})

    # 5. Sorting
    if order_items:
        for ord_item in order_items:
            col_key = ord_item.get('word', ord_item.get('column'))
            c = SCHEMA_MAPPING.get(col_key)
            if c:
                direction = ord_item.get('direction') or "DESC"
                matched_agg = None
                for a in ir["aggregations"]:
                    if a["field"] == c:
                        matched_agg = a
                        break
                        
                if matched_agg:
                    ir["order_by"].append({"func": matched_agg["func"], "field": c, "direction": direction})
                elif c not in NUMERIC_COLUMNS:
                    ir["order_by"].append({"field": c, "direction": direction})
                else:
                    ir["order_by"].append({"field": c, "direction": direction})
    
    # Implicit Sorting (Rank Intent caching)
    if not ir["order_by"]:
        for kw in keywords:
            if kw.get('direction'):
                if ir["aggregations"]:
                    agg = ir["aggregations"][-1]
                    ir["order_by"].append({"func": agg["func"], "field": agg["field"], "direction": kw['direction']})
                else:
                    ir["order_by"].append({"field": "salary", "direction": kw['direction']})
                break

    # OLAP Semantic Hierarchy Override
    if ir["group_by"] and ir["aggregations"] and ir["order_by"]:
        new_order = []
        for g in ir["group_by"][:-1]: 
            new_order.append({"field": g, "direction": "ASC"})
            
        measure_hooked = False
        for o in ir["order_by"]:
            if "func" in o:
                new_order.append(o)
                measure_hooked = True
                
        if not measure_hooked:
            agg = ir["aggregations"][0]
            new_order.append({"func": agg["func"], "field": agg["field"], "direction": "DESC"})
            
        dedup_order = []
        for o in new_order:
            if o not in dedup_order:
                dedup_order.append(o)
        ir["order_by"] = dedup_order

    return ir

def generate_sql(parsed_data: Dict[str, Any]) -> Tuple[str, List[Any]]:
    logger.info("Generating SQL from standard IR Query Plan.")
    
    if not parsed_data:
        raise ValueError("Cannot parse an empty sentence context.")
        
    ir = build_query_plan(parsed_data)
    params = []
    
    # 1. SELECT clause
    select_items = []
    if ir["group_by"]:
        for g in ir["group_by"]:
            select_items.append(g)
            
    if ir["aggregations"]:
        for a in ir["aggregations"]:
            item = f"{a['func']}(*)" if a['field'] == "*" else f"{a['func']}({a['field']})"
            if item not in select_items:
                select_items.append(item)
                
    select_clause = ", ".join(select_items) if select_items else "*"
    base_query = f"SELECT {select_clause} FROM employees"
    
    # 2. WHERE clause
    where_pieces = []
    
    if ir["filters"]["groups"]:
        or_groups_str = []
        for grp in ir["filters"]["groups"]:
            and_pieces = []
            for f in grp:
                field = f["field"]
                op = f["op"]
                val = f["value"]
                
                left = f"lower({field})" if field not in NUMERIC_COLUMNS and field != "*" else field
                if op in ("IN", "NOT IN"):
                    placeholders = ", ".join(["?"] * len(val))
                    and_pieces.append(f"{left} {op} ({placeholders})")
                    params.extend(val)
                else:
                    and_pieces.append(f"{left} {op} ?")
                    params.append(val)
                    
            if and_pieces:
                if len(and_pieces) > 1:
                    or_groups_str.append("(" + " AND ".join(and_pieces) + ")")
                else:
                    or_groups_str.append(and_pieces[0])
                    
        if or_groups_str:
            where_pieces.append("(" + " OR ".join(or_groups_str) + ")" if len(or_groups_str) > 1 else or_groups_str[0])
            
    if ir.get("numeric_filters"):
        for f in ir["numeric_filters"]:
            left = f["field"]
            if f["op"] in ("BETWEEN", "NOT BETWEEN"):
                where_pieces.append(f"{left} {f['op']} ? AND ?")
                params.extend(f["value"])
            else:
                where_pieces.append(f"{left} {f['op']} ?")
                params.append(f["value"])
                
    if where_pieces:
        base_query += " WHERE " + " AND ".join(where_pieces)

    # 3. GROUP BY
    if ir["group_by"]:
        base_query += " GROUP BY " + ", ".join(ir["group_by"])

    # 4. HAVING
    if ir["having"]:
        having_pieces = []
        for f in ir["having"]:
            left = f"{f['func']}(*)" if f['field'] == "*" else f"{f['func']}({f['field']})"
            op = f["op"]
            val = f["value"]
            
            if op in ("BETWEEN", "NOT BETWEEN"):
                having_pieces.append(f"{left} {op} ? AND ?")
                params.extend(val)
            else:
                having_pieces.append(f"{left} {op} ?")
                params.append(val)
                
        base_query += " HAVING " + " AND ".join(having_pieces)

    # 5. ORDER BY
    if ir["order_by"]:
        order_pieces = []
        for o in ir["order_by"]:
            if "func" in o:
                left = f"{o['func']}(*)" if o['field'] == "*" else f"{o['func']}({o['field']})"
            else:
                left = o['field']
                
            direction = o.get("direction", "DESC")
            
            if not ir["group_by"] and ir["aggregations"]:
                continue
                
            order_pieces.append(f"{left} {direction}")
            
        if order_pieces:
            base_query += " ORDER BY " + ", ".join(order_pieces)

    # 6. LIMIT
    if ir["limit"]:
        base_query += f" LIMIT {ir['limit']}"

    # 7. Fail Fast Defense
    if base_query == "SELECT * FROM employees" and not ir["limit"] and not ir["filters"]["groups"] and not ir["aggregations"] and not ir["numeric_filters"]:
        raise ValueError("This text could not map to the database schema accurately. No recognizable relationships found.")
        
    base_query += ";"
    
    return base_query, params