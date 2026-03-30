"""
Chat API Routes
Endpoints untuk chat dengan AI SQL Analyst (LAM Architecture)
"""
import json
import re
from datetime import datetime
from uuid import uuid4
from fastapi import APIRouter, HTTPException
from pydantic import ValidationError

from api.app.models.chat import ChatRequest, ChatResponse
from api.app.models.analysis_intent import AnalysisIntent, AnalysisResponse
from api.app.services.llm.factory import LLMFactory
from api.app.services.adapters.factory import AdapterFactory
from api.app.services.database.factory import DatabaseFactory
from api.app.utils.prompts import LAM_ANALYST_PROMPT, build_lam_context_prompt

router = APIRouter()


def find_json_block(text: str) -> tuple[str, int, int] | None:
    """
    Finds a JSON block in text and returns (json_content, start_index, end_index).
    Uses brace counting for reliable JSON boundary detection.
    """
    # Case 1: Try Markdown Code Blocks first (most reliable)
    match = re.search(r'```\s*(?:json)?\s*([\s\S]*?)\s*```', text, re.IGNORECASE)
    if match:
        return match.group(1), match.start(), match.end()
    
    # Case 2: Find JSON object using brace counting
    # First, find where JSON likely starts (after "json" label or at first "{")
    json_label_match = re.search(r'\bjson\s*\n\s*\{', text, re.IGNORECASE)
    
    if json_label_match:
        # Start from the opening brace
        start = json_label_match.end() - 1  # -1 to include the '{'
        block_start = json_label_match.start()  # Include "json" label for removal
    else:
        # No "json" label, find first { that looks like our intent
        start = text.find('{"intent_type"')
        if start == -1:
            start = text.find("{'intent_type")
        if start == -1:
            start = text.find('{')
        if start == -1:
            return None
        block_start = start
    
    # Count braces to find matching close
    depth = 0
    in_string = False
    escape_next = False
    in_comment = False
    
    for i in range(start, len(text)):
        char = text[i]
        
        # Handle single-line comments //
        if not in_string and not in_comment and char == '/' and i + 1 < len(text) and text[i+1] == '/':
            in_comment = True
            continue
            
        if in_comment:
            if char == '\n':
                in_comment = False
            continue
        
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
                # Found complete JSON
                json_content = text[start:i+1]
                return json_content, block_start, i+1
    
    return None


def parse_analysis_intent(llm_response: str) -> AnalysisResponse:
    """
    Parse LLM response to extract AnalysisIntent JSON.
    Handles both:
    - Wrapped format: {"interpretation": "...", "analysis_intent": {...}, ...}
    - Unwrapped format: {"intent_type": "...", "target_entity": "...", ...}
    """
    print("[DEBUG PARSE] Starting parse_analysis_intent...")
    
    result = find_json_block(llm_response)
    if not result:
        print("[DEBUG PARSE] ERROR: No JSON block found!")
        raise ValueError("No JSON object found in response")
    
    json_str, block_start, block_end = result
    json_str = json_str.strip()
    print(f"[DEBUG PARSE] Found JSON block from {block_start} to {block_end}")
    print(f"[DEBUG PARSE] JSON preview: {json_str[:100]}...")
    
    # Cleaning common artifacts
    if json_str.lower().startswith("json"):
        json_str = json_str[4:].strip()
        print("[DEBUG PARSE] Removed 'json' prefix")
    
    # Remove JavaScript-style comments (// ...) that some LLMs add
    json_str = re.sub(r'//.*?(?=\n|$)', '', json_str)
    print("[DEBUG PARSE] Stripped JS comments")

    # Parsing
    try:
        data = json.loads(json_str)
        print(f"[DEBUG PARSE] JSON parsed successfully. Keys: {list(data.keys())}")
    except json.JSONDecodeError as e:
        print(f"[DEBUG PARSE] JSONDecodeError: {e}")
        # Try fixing common issues
        json_str_fixed = re.sub(r',\s*}', '}', json_str)
        json_str_fixed = re.sub(r',\s*]', ']', json_str_fixed)
        try:
            data = json.loads(json_str_fixed)
            print(f"[DEBUG PARSE] Fixed JSON parsed. Keys: {list(data.keys())}")
        except json.JSONDecodeError:
            # Final fallback: try ast.literal_eval for non-standard JSON (like single quotes)
            print("[DEBUG PARSE] Attempting ast.literal_eval fallback...")
            try:
                import ast
                # Convert null/true/false to Python equivalents for literal_eval
                p_text = json_str_fixed.replace('null', 'None').replace('true', 'True').replace('false', 'False')
                data = ast.literal_eval(p_text)
                if isinstance(data, dict):
                    print("[DEBUG PARSE] ast.literal_eval succeeded.")
                else:
                    raise ValueError("ast.literal_eval did not return a dict")
            except Exception as e3:
                print(f"[DEBUG PARSE] All parsing attempts failed. Last error: {e3}")
                print(f"[DEBUG PARSE] Final JSON content attempted:\n{json_str}")
                raise ValueError(f"Could not parse JSON. Error: {str(e)} (Followed by {str(e3)})")
    
    # Detect format: wrapped or unwrapped
    if "intent_type" in data and "analysis_intent" not in data:
        print("[DEBUG PARSE] Format: UNWRAPPED")
        # Unwrapped: raw AnalysisIntent
        # Wrap it into AnalysisResponse with defaults
        wrapped_data = {
            "interpretation": "Analysis request parsed from user query",
            "analysis_intent": data,
            "visualization": data.get("visualization", "table"),
            "insights": data.get("insights", "")
        }
        return AnalysisResponse(**wrapped_data)
    else:
        print("[DEBUG PARSE] Format: WRAPPED")
        # Wrapped: full AnalysisResponse
        return AnalysisResponse(**data)


@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(request: ChatRequest):
    """
    Chat dengan AI SQL Analyst (LAM Architecture)
    
    Flow:
    1. LLM menghasilkan AnalysisIntent JSON
    2. Adapter menerjemahkan ke query spesifik database
    3. Execute query dan return hasil
    """
    try:
        # Get LLM provider based on selected model
        llm = LLMFactory.get_provider(
            model_name=request.dbContext.selectedModel,
            api_key=request.dbContext.apiKey
        )
        
        # Build LAM context prompt
        context_prompt = build_lam_context_prompt(
            db_type=request.dbContext.connection.type,
            db_name=request.dbContext.connection.database,
            model_name=request.dbContext.selectedModel,
            schema=request.dbContext.schema,
            user_query=request.message
        )
        
        # Generate AnalysisIntent from LLM
        llm_response = await llm.generate(
            prompt=context_prompt,
            system_instruction=LAM_ANALYST_PROMPT,
            temperature=0.2
        )
        
        # Parse the analysis intent
        try:
            print(f"[DEBUG] LLM Response length: {len(llm_response)}")
            print(f"[DEBUG] LLM Response preview: {llm_response[:200]}...")
            
            analysis_response = parse_analysis_intent(llm_response)
            intent = analysis_response.analysis_intent
            
            print(f"[DEBUG] Parsed intent_type: {intent.intent_type}")
            print(f"[DEBUG] Parsed target_entity: {intent.target_entity}")
            
            # Get appropriate adapter for database type
            db_type = request.dbContext.connection.type
            print(f"[DEBUG] Database type from request: '{db_type}'")
            print(f"[DEBUG] Is SQL database: {AdapterFactory.is_sql_database(db_type)}")
            
            adapter = AdapterFactory.get_adapter(db_type)
            print(f"[DEBUG] Selected adapter: {type(adapter).__name__}")
            
            # Build database-specific query
            query = adapter.build_query(intent)
            
            print(f"[DEBUG] Generated query: {query}")
            
            # Execute the query
            connector = DatabaseFactory.get_connector(request.dbContext.connection)
            
            await connector.connect()
            columns, rows = await connector.execute_query(
                query if isinstance(query, str) else json.dumps(query)
            )
            await connector.disconnect()
            
            # ============================================
            # CLEANUP: Remove "Analysis Intent" section from display
            # ============================================
            display_content = llm_response
            
            # ============================================
            # CLEANUP: Remove "Analysis Intent" section from display
            # ============================================
            display_content = llm_response
            
            # 1. Locating the JSON block is the most reliable way to remove it
            # We use find_json_block again to get the exact indices in the original string
            json_block_info = find_json_block(display_content)
            
            if json_block_info:
                _, json_start, json_end = json_block_info
                
                # Split content into before and after JSON
                prefix = display_content[:json_start]
                suffix = display_content[json_end:]
                
                # 2. Check for the "Analysis Intent" header immediately preceding the JSON
                # We look for the header at the END of the prefix
                header_pattern = r'(?:^|\n)(?:###\s*)?(?:🔧\s*)?Analysis Intent\s*(?:[:\n]|$|`|json)*\s*$'
                
                header_match = re.search(header_pattern, prefix, re.IGNORECASE)
                if header_match:
                    # If header found, cut the prefix before the header
                    # header_match.start() is relative to the start of prefix
                    # We want to keep everything BEFORE the header
                    prefix = prefix[:header_match.start()]
                
                # 3. Stitch it back together
                display_content = prefix.strip() + "\n\n" + suffix.strip()
            else:
                # Fallback: If for some reason find_json_block fails (unlikely if parsing succeeded),
                # try the aggressive regex as a backup
                cleanup_pattern = r'(?:^|\n)(?:###\s*)?(?:🔧\s*)?Analysis Intent[\s\S]*?(?=(?:\n###|\n---|(?:\n\s*$)))'
                display_content = re.sub(cleanup_pattern, '', display_content, flags=re.IGNORECASE)

            # Final safety: remove any standalone "json" labels or empty code blocks left behind
            display_content = re.sub(r'\n\s*json\s*\n', '\n', display_content, flags=re.IGNORECASE)
            display_content = re.sub(r'```\s*```', '', display_content)
            
            display_content = display_content.strip()

            # Build response with analysis + results
            response_content = f"""{display_content}

---
### 🧾 Generated Query
```{'sql' if AdapterFactory.is_sql_database(db_type) else 'mongodb'}
{query if isinstance(query, str) else json.dumps(query, indent=2)}
```

### 📊 Query Results
Found **{len(rows)}** rows.
"""
            print(f"[DEBUG] Final response_content preview (first 500 chars):")
            print(response_content[:500])
            print("---END PREVIEW---")
            
            # Return response with embedded results
            return ChatResponse(
                id=str(uuid4()),
                role="assistant",
                content=response_content,
                timestamp=datetime.now(),
                model_used=llm.model_name,
                # Include structured data for frontend
                analysis_intent=intent.model_dump() if intent else None,
                query_result={
                    "columns": columns,
                    "rows": rows[:100]  # Limit to 100 rows
                } if columns else None
            )
            
        except ValueError as parse_error:
            # Even if parsing fails, try to clean up the display content (remove JSON block)
            display_content = llm_response
            json_block_info = find_json_block(display_content)
            if json_block_info:
                _, json_start, json_end = json_block_info
                # Remove just the JSON block indices
                display_content = display_content[:json_start].strip() + "\n\n" + display_content[json_end:].strip()
            
            # Fallback: return raw LLM response but cleaned up
            return ChatResponse(
                id=str(uuid4()),
                role="assistant",
                content=f"⚠️ **Note:** Analysis intent parsing failed ({str(parse_error)}). Displaying AI interpretation only:\n\n{display_content.strip()}",
                timestamp=datetime.now(),
                model_used=llm.model_name
            )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")


@router.get("/models")
async def list_available_models():
    """List semua AI model yang tersedia beserta status konfigurasinya"""
    return {
        "models": LLMFactory.list_providers(),
        "status": LLMFactory.get_provider_status()
    }
