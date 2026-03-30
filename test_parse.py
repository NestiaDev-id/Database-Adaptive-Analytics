import json
import re
from api.app.models.analysis_intent import AnalysisIntent, AnalysisResponse
from api.app.services.adapters import SQLAdapter

# Simulating FULL LLM response with natural language + JSON (NO markdown fences!)
llm_response = """
📌 User Intent Interpretation
The user wants to display the top 5 best-selling products.

🧠 Analysis Approach
We will aggregate sales data by product and sort by total sales.

🔧 Analysis Intent

json
{
  "intent_type": "top_n",
  "target_entity": "sales",
  "fields": ["product_id", "quantity_sold"],
  "filters": [],
  "aggregations": [
    {"func": "sum", "field": "quantity_sold", "alias": "total_sales"}
  ],
  "group_by": ["product_id"],
  "order_by": [{"field": "total_sales", "direction": "desc"}],
  "limit": 5,
  "time_field": null,
  "time_granularity": null
}

📈 Recommended Visualization
A bar chart would work well.
"""

print("=== Testing UPDATED find_json_block ===")
print(f"LLM Response length: {len(llm_response)} chars")

# NEW find_json_block with brace counting
def find_json_block(text):
    # Case 1: Try Markdown Code Blocks first
    match = re.search(r'```\s*(?:json)?\s*([\s\S]*?)\s*```', text, re.IGNORECASE)
    if match:
        print("Matched: Case 1 (Markdown fences)")
        return match.group(1), match.start(), match.end()
    
    # Case 2: Find JSON object using brace counting
    json_label_match = re.search(r'\bjson\s*\n\s*\{', text, re.IGNORECASE)
    
    if json_label_match:
        start = json_label_match.end() - 1
        block_start = json_label_match.start()
        print("Matched: Case 2 (json label with brace counting)")
    else:
        start = text.find('{"intent_type"')
        if start == -1:
            start = text.find("{'intent_type")
        if start == -1:
            start = text.find('{')
        if start == -1:
            return None
        block_start = start
        print("Matched: Case 3 (Fallback braces)")
    
    # Count braces to find matching close
    depth = 0
    in_string = False
    escape_next = False
    
    for i in range(start, len(text)):
        char = text[i]
        
        if escape_next:
            escape_next = False
            continue
            
        if char == '\\' and in_string:
            escape_next = True
            continue
            
        if char == '"':
            in_string = not in_string
            continue
            
        if in_string:
            continue
            
        if char == '{':
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0:
                json_content = text[start:i+1]
                return json_content, block_start, i+1
    
    return None

result = find_json_block(llm_response)
if result:
    json_str, block_start, block_end = result
    print(f"Found JSON: block_start={block_start}, block_end={block_end}")
    print(f"JSON length: {len(json_str)} chars")
    
    # Parse
    data = json.loads(json_str.strip())
    print(f"Parsed data keys: {list(data.keys())}")
    
    # Check format
    if "intent_type" in data and "analysis_intent" not in data:
        print("Format: UNWRAPPED (raw AnalysisIntent)")
        intent = AnalysisIntent(**data)
        
        # Build SQL
        adapter = SQLAdapter(dialect="postgresql")
        sql = adapter.build_query(intent)
        print(f"\n=== SUCCESS! Generated SQL ===")
        print(sql)
    else:
        print("Format: WRAPPED")
else:
    print("ERROR: No JSON block found!")
