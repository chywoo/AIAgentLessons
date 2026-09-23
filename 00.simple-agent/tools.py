from datetime import datetime

def calculator(expression: str) -> str:
    try:
        allowed_chars = "0123456789+-*/(). "
        
        if not all(c in allowed_chars for c in expression):
            return "Invalid expression"
        
        return str(eval(expression))
    except Exception as e:
        return f"Error: {str(e)}"
    
def get_current_time() -> str:
    return datetime.now().isoformat()


TOOLS = {
    "calculator": calculator,
    "get_current_time": get_current_time,
}

# TOOL Schemas for OpenAI API Chat Completions mode
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Calculate a mathematical expression",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                    }
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current date or time",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            },
        }
    }
]