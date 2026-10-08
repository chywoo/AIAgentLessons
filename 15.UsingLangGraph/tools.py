from datetime import datetime
from pathlib import Path
import ast
import operator


DATA_DIR = Path("./data").resolve()


def calculator(expression: str) -> str:
    operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    def evaluate(node):
        if isinstance(node, ast.Expression):
            return evaluate(node.body)

        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("Only numbers are allowed.")

        if isinstance(node, ast.BinOp):
            op = operators.get(type(node.op))

            if op is None:
                raise ValueError("Unsupported operator.")

            return op(
                evaluate(node.left),
                evaluate(node.right),
            )

        if isinstance(node, ast.UnaryOp):
            op = operators.get(type(node.op))

            if op is None:
                raise ValueError("Unsupported unary operator.")

            return op(evaluate(node.operand))

        raise ValueError("Unsupported expression.")

    try:
        tree = ast.parse(expression, mode="eval")
        return str(evaluate(tree))

    except Exception as e:
        return f"Calculation error: {e}"


def get_current_time() -> str:
    return datetime.now().isoformat()


def text_length(text: str) -> str:
    return str(len(text))


def read_file(path: str) -> str:
    try:
        target = (DATA_DIR / path).resolve()

        # Prevent ../ style directory traversal
        if target != DATA_DIR and DATA_DIR not in target.parents:
            return "Access denied"

        if not target.exists():
            return f"File not found: {path}"

        if not target.is_file():
            return f"Not a file: {path}"

        return target.read_text(encoding="utf-8")

    except Exception as e:
        return f"File read error: {e}"

def list_files() -> str:
    files = [
        p.name
        for p in DATA_DIR.iterdir()
        if p.is_file()
    ]

    return "\n".join(files)

TOOLS = {
    "calculator": calculator,
    "get_current_time": get_current_time,
    "text_length": text_length,
    "read_file": read_file,
    "list_files": list_files,
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
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": (
                "Read a text file from the application's data directory. "
                "Use this tool when information needed to answer the user "
                "is stored in a file."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": (
                            "Relative file path inside the data directory, "
                            "for example sales.txt"
                        ),
                    }
                },
                "required": ["path"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "text_length",
            "description": "Get how many text is in text",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                    }
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": (
                "List the files available "
                "in the application's data directory."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
    },
]