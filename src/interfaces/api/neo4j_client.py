from __future__ import annotations

from dataclasses import dataclass

from src.interfaces.api.config import ApiSettings


@dataclass(frozen=True)
class Neo4jHealth:
    ok: bool
    message: str


def check_neo4j(settings: ApiSettings) -> Neo4jHealth:
    try:
        from neo4j import GraphDatabase
    except ModuleNotFoundError:
        return Neo4jHealth(ok=False, message="neo4j driver is not installed")

    try:
        with GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        ) as driver:
            result = driver.execute_query("RETURN 1 AS ok")
            records = result.records
            if records and records[0].get("ok") == 1:
                return Neo4jHealth(ok=True, message="connected")
            return Neo4jHealth(ok=False, message="unexpected neo4j response")
    except Exception as exc:
        return Neo4jHealth(ok=False, message=str(exc))
