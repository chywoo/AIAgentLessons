from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import ast
import operator
import uuid

DATA_DIR = Path("./data").resolve()

@dataclass
class ApprovalDecision:
    approved: bool
    reason: str = ""


@dataclass
class PendingAction:
    id: str
    tool_name: str
    arguments: dict
    risk: str


def request_approval(tool_name: str, arguments: dict, risk: str, ) -> ApprovalDecision:
    print()
    print("=" * 60)
    print("HUMAN APPROVAL REQUIRED")
    print("=" * 60)

    print(f"Tool: {tool_name}")
    print(f"Risk: {risk.upper()}")
    print(f"Arguments: {arguments}")

    answer = input("Approve this action? [y/N]: ").strip().lower()

    if answer in {"y", "yes", }:
        return ApprovalDecision(approved=True)

    return ApprovalDecision(approved=False, reason="The user rejected the action.", )


def safe_path(path: str) -> Path:
    target = (DATA_DIR / path).resolve()

    if target != DATA_DIR and DATA_DIR not in target.parents:
        raise ValueError("Access outside data directory is not allowed.")

    return target


def write_file(path: str, content: str, ) -> str:
    target = safe_path(path)
    target.parent.mkdir(parents=True, exist_ok=True, )
    target.write_text(content, encoding="utf-8", )

    return f"File written: {path}"


def delete_file(path: str, ) -> str:
    target = safe_path(path)

    if not target.exists():
        return f"File not found: {path}"

    if not target.is_file():
        return f"Not a file: {path}"

    target.unlink()

    return f"File deleted: {path}"


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
    files = [p.name for p in DATA_DIR.iterdir() if p.is_file()]

    return "\n".join(files)


from memory import MemoryStore

memory_store = MemoryStore()


def save_memory(
        content: str,
        category: str = "general",
) -> str:
    memory_id = memory_store.add(
        content=content,
        category=category,
    )

    return f"Memory saved with id={memory_id}"


def search_memory(
        query: str,
) -> str:
    results = memory_store.search(
        query=query,
        limit=5,
    )

    if not results:
        return "No matching memories found."

    lines = []

    for memory in results:
        lines.append(f"[score={memory['score']:.3f}] " f"[{memory['content']}]")

    return "\n".join(lines)


TOOLS = {
    "calculator": {
        "function": calculator,
        "requires_approval": False,
        "risk": "low",
    },

    "read_file": {
        "function": read_file,
        "requires_approval": False,
        "risk": "low",
    },

    "write_file": {
        "function": write_file,
        "requires_approval": True,
        "risk": "medium",
    },

    "delete_file": {
        "function": delete_file,
        "requires_approval": True,
        "risk": "high",
    },
}

# TOOL Schemas for OpenAI API Chat Completions mode
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": (
                "Write text content to a file "
                "inside the application's data directory."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string"
                    },
                    "content": {
                        "type": "string"
                    },
                },
                "required": [
                    "path",
                    "content",
                ],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_file",
            "description": (
                "Delete a file from the application's "
                "data directory."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string"
                    }
                },
                "required": [
                    "path"
                ],
                "additionalProperties": False,
            },
        },
    },
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
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current date or time",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
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
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": (
                "List the files available " "in the application's data directory."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_memory",
            "description": (
                "Save important information into long-term memory. "
                "Use this for durable facts that may be useful in future tasks."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                    },
                    "category": {
                        "type": "string",
                    },
                },
                "required": ["content"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_memory",
            "description": (
                "Search long-term memory for information "
                "that may be relevant to the current task."
            ),
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
]
