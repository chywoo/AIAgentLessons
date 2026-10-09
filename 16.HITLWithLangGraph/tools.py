from pathlib import Path

DATA_DIR = Path("./data").resolve()


def safe_path(path: str) -> Path:
    target = (
            DATA_DIR / path
    ).resolve()

    if (
            target != DATA_DIR
            and DATA_DIR
            not in target.parents
    ):
        raise ValueError(
            "Access outside data directory "
            "is not allowed."
        )

    return target


def read_file(
        path: str,
) -> str:
    target = safe_path(path)

    if not target.exists():
        return f"File not found: {path}"

    return target.read_text(
        encoding="utf-8"
    )


def write_file(
        path: str,
        content: str,
) -> str:
    target = safe_path(path)

    target.write_text(
        content,
        encoding="utf-8",
    )

    return f"File written: {path}"


def delete_file(
        path: str,
) -> str:
    target = safe_path(path)

    if not target.exists():
        return f"File not found: {path}"

    target.unlink()

    return f"File deleted: {path}"


TOOLS = {
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
            "name": "delete_file",
            "description": "Delete the file.",
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
                "required": ["path"]
            }
        }
    },
]
