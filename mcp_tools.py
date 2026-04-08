from mcp.server.fastmcp import FastMCP
from database import SessionLocal, Task

mcp = FastMCP("CloudTools")

@mcp.tool()
def add_task(user_id: int, description: str, due_date: str) -> str:
    """Adds a new task to the user's PostgreSQL database."""
    db = SessionLocal()
    new_task = Task(user_id=user_id, description=description, due_date=due_date)
    db.add(new_task)
    db.commit()
    db.close()
    return f"Task '{description}' securely added to cloud database."
