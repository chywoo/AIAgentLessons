from pathlib import Path
from mcp.server import MCPServer

mcp = MCPServer(
    "day15-tools",
    instructions="Tools for calculations and accessing the local project data directory."
)

DATA_DIR = Path("./data").resolve()


def safe_path(paht: str) -> Path:
    target = (DATA_DIR / paht).resolve()

    if target != DATA_DIR and DATA_DIR not in target.parents:
        raise ValueError("Access outside data directory is not allowed.")

    return target


@mcp.tool()
def calculator(a: float, b: float, operation: str) -> float:
    """
    Perform a simple arithmetic calculation.
    Operation can be one of the following:
    add, subtract, multiply, divide
    :param a:
    :param b:
    :param operation:
    :return:
    """

    if operation == "add":
        return a + b
    elif operation == "subtract":
        return a - b
    elif operation == "multiply":
        return a * b
    elif operation == "divide":
        if b == 0:
            raise ZeroDivisionError("division by zero")
        else:
            return a / b
        return a / b
    else:
        raise ValueError(f"Invalid operation: {operation}")


@mcp.tool()
def read_file(path: str) -> str:
   """
   Read a UTF-8 text file from the dat dictionary.
   :param path:
   :return:
   """
   target = safe_path(path)

   if not target.exists():
       return f"File not found: {path}"
   if not target.is_file():
       return f"File not found: {path}"

   return target.read_text(encoding="utf-8")

@mcp.tool()
def list_files() -> list[str]:
    """
    List all files in the data directory.
    """

    return [path.name for path in DATA_DIR.iterdir() if path.is_file()]

