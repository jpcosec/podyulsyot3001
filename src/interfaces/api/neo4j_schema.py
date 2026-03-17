from __future__ import annotations

from dataclasses import dataclass

from src.interfaces.api.config import ApiSettings

CONSTRAINTS: tuple[str, ...] = (
    "CREATE CONSTRAINT profile_id IF NOT EXISTS FOR (n:Profile) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT experience_id IF NOT EXISTS FOR (n:Experience) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT skill_id IF NOT EXISTS FOR (n:Skill) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT education_id IF NOT EXISTS FOR (n:Education) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT language_id IF NOT EXISTS FOR (n:Language) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT job_posting_id IF NOT EXISTS FOR (n:JobPosting) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT requirement_id IF NOT EXISTS FOR (n:Requirement) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT institution_id IF NOT EXISTS FOR (n:Institution) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT org_unit_id IF NOT EXISTS FOR (n:OrganizationalUnit) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT person_id IF NOT EXISTS FOR (n:Person) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT research_context_id IF NOT EXISTS FOR (n:ResearchContext) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT research_topic_id IF NOT EXISTS FOR (n:ResearchTopic) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT research_project_id IF NOT EXISTS FOR (n:ResearchProject) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT teaching_duty_id IF NOT EXISTS FOR (n:TeachingDuty) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT application_id IF NOT EXISTS FOR (n:Application) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT comment_id IF NOT EXISTS FOR (n:Comment) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT text_span_id IF NOT EXISTS FOR (n:TextSpan) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT source_doc_id IF NOT EXISTS FOR (n:SourceDocument) REQUIRE n.id IS UNIQUE",
)


@dataclass(frozen=True)
class SchemaBootstrapResult:
    applied: int
    ok: bool
    message: str


def apply_schema_constraints(settings: ApiSettings) -> SchemaBootstrapResult:
    try:
        from neo4j import GraphDatabase
    except ModuleNotFoundError:
        return SchemaBootstrapResult(
            applied=0, ok=False, message="neo4j driver is not installed"
        )

    try:
        with GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        ) as driver:
            for statement in CONSTRAINTS:
                driver.execute_query(statement)
        return SchemaBootstrapResult(
            applied=len(CONSTRAINTS),
            ok=True,
            message="constraints applied",
        )
    except Exception as exc:
        return SchemaBootstrapResult(applied=0, ok=False, message=str(exc))
