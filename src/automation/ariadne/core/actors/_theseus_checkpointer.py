"""Theseus checkpointer helpers."""

from pathlib import Path

from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver


async def create_sqlite_checkpointer(checkpoint_path: Path | str | None):
    """Yield the sqlite checkpointer."""
    resolved_path = Path(checkpoint_path or "data/ariadne/checkpoints.db")
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    async with AsyncSqliteSaver.from_conn_string(str(resolved_path)) as checkpointer:
        yield checkpointer


def compile_with_memory(workflow) -> Any:
    """Compile workflow with memory checkpointer."""
    from langgraph.graph import StateGraph

    return workflow.compile(
        checkpointer=MemorySaver(),
        interrupt_before=["human_in_the_loop"],
    )


async def compile_with_sqlite(workflow, checkpoint_path: Path | str | None) -> Any:
    """Compile workflow with sqlite checkpointer."""
    async with create_sqlite_checkpointer(checkpoint_path) as checkpointer:
        return workflow.compile(
            checkpointer=checkpointer,
            interrupt_before=["human_in_the_loop"],
        )
