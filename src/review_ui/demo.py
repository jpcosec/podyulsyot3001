"""Interactive demo for the new HITL Review UI screens."""

from __future__ import annotations

from typing import Any

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Button, Footer, Header, Label

from src.review_ui.app import MatchReviewApp
from src.review_ui.bus import MatchBus, ReviewSurfaceData


class DemoBus(MatchBus):
    """Mock bus that returns static data for each demo stage."""

    def __init__(self, stage: str):
        super().__init__(store=None, client=None, config={})
        self.demo_stage = stage

    def _pending_review_stage(self) -> str:
        return self.demo_stage

    def load_current_review_surface(self, source: str, job_id: str) -> ReviewSurfaceData:
        if self.demo_stage == "hitl_1_match_evidence":
            return ReviewSurfaceData(
                stage="hitl_1_match_evidence",
                artifact_stage="match_edges",
                title="Match Evidence Review",
                payload={
                    "matches": [
                        {"requirement_id": "R01", "match_score": 0.95, "reasoning": "Candidate has 8 years of Python experience.", "profile_evidence_ids": ["EXP-001"]},
                        {"requirement_id": "R02", "match_score": 0.40, "reasoning": "No direct mention of Rust in the profile.", "profile_evidence_ids": []},
                        {"requirement_id": "R03", "match_score": 0.82, "reasoning": "Strong leadership evidence from Lead Dev role.", "profile_evidence_ids": ["EXP-002"]},
                    ],
                    "job_kg": {
                        "job_title_english": "Senior Python Backend Engineer",
                        "hard_requirements": [
                            {"id": "R01", "text": "Deep expertise in Python and Django"},
                            {"id": "R02", "text": "Experience with Rust or Go is a plus"},
                            {"id": "R03", "text": "Proven experience leading engineering teams"},
                        ]
                    }
                }
            )
        elif self.demo_stage == "hitl_2_blueprint_logic":
            return ReviewSurfaceData(
                stage="hitl_2_blueprint_logic",
                artifact_stage="blueprint",
                title="Blueprint Review",
                payload={
                    "sections": [
                        {"section_id": "summary", "section_intent": "Highlight 8 years of high-scale backend experience.", "logical_train_of_thought": ["R01", "Python", "Scale"]},
                        {"section_id": "experience", "section_intent": "Focus on recent lead role at TechCorp.", "logical_train_of_thought": ["R03", "Management"]},
                        {"section_id": "skills", "section_intent": "Group by Backend, Cloud, and Tooling.", "logical_train_of_thought": ["Django", "AWS", "Docker"]},
                    ]
                }
            )
        elif self.demo_stage == "hitl_3_content_style":
            return ReviewSurfaceData(
                stage="hitl_3_content_style",
                artifact_stage="markdown_bundle",
                title="Content Review",
                payload={
                    "cv_full_md": "::: {.job role=\"Senior Backend Engineer\" org=\"TechCorp\" dates=\"2018 - Present\"}\n- Led migration to microservices\n- Optimized database queries by 40%\n:::\n\n::: {.education degree=\"B.Sc. Computer Science\" institution=\"Stanford\" dates=\"2010 - 2014\"}\n- Focus on distributed systems\n:::",
                    "letter_full_md": "Dear Hiring Manager,\n\nI am excited to apply for the Senior Python Engineer position. With 8 years of experience building scalable systems, I believe I am a great fit.\n\nBest regards,\nCandidate",
                    "email_body_md": "Hi Team, attached is my application for the Backend role. Looking forward to hearing from you!"
                }
            )
        elif self.demo_stage == "hitl_4_profile_updates":
            return ReviewSurfaceData(
                stage="hitl_4_profile_updates",
                artifact_stage="profile_updater",
                title="Profile Update Review",
                payload={
                    "updates": [
                        {"field_path": "skills.languages", "old_value": ["Python", "JavaScript"], "new_value": ["Python", "JavaScript", "Rust"], "source_stage": "hitl_1"},
                        {"field_path": "owner.tagline", "old_value": "Python Developer", "new_value": "Senior Backend Architect | 8+ Years", "source_stage": "hitl_3"}
                    ]
                }
            )
        return ReviewSurfaceData("unknown", "unknown", "Unknown", {})

    def resume_with_review(self, action: str, patches: list[dict] | None = None) -> dict:
        print(f"\n[DEMO] Submitted action: {action}")
        if patches:
            print(f"[DEMO] With {len(patches)} patches:")
            for p in patches:
                print(f"  - {p['action']} on {p['target_id']}")
        return {"status": "completed"}


class DemoLauncher(App):
    """Simple menu to pick a demo screen."""
    
    CSS = """
    #menu {
        align: center middle;
        height: 1fr;
    }
    Button {
        margin: 1;
        width: 40;
    }
    Label {
        text-align: center;
        width: 100%;
        margin-bottom: 2;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="menu"):
            yield Label("[bold]Postulator 3000 Redesign Demo[/]\nSelect a screen to interact with:")
            yield Button("1. Match Evidence (HITL 1)", id="btn_1", variant="primary")
            yield Button("2. Blueprint Logic (HITL 2)", id="btn_2", variant="primary")
            yield Button("3. Content & Style (HITL 3 - Vim Mode)", id="btn_3", variant="primary")
            yield Button("4. Profile Updates (HITL 4)", id="btn_4", variant="primary")
            yield Button("Quit", id="btn_quit", variant="error")
        yield Footer()

    @on(Button.Pressed)
    def handle_choice(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_quit":
            self.exit()
            return

        stage_map = {
            "btn_1": "hitl_1_match_evidence",
            "btn_2": "hitl_2_blueprint_logic",
            "btn_3": "hitl_3_content_style",
            "btn_4": "hitl_4_profile_updates",
        }
        
        stage = stage_map[event.button.id]
        bus = DemoBus(stage)
        
        # Launch the actual app in demo mode
        demo_app = MatchReviewApp(bus=bus, source="demo", job_id="job_123")
        self.exit(demo_app)


def run_demo() -> None:
    """Entry point for the demo."""
    launcher = DemoLauncher()
    result = launcher.run()
    
    # If launcher returned an app, run it
    if isinstance(result, App):
        result.run()
