"""Tests for match contract normalization behavior."""

from __future__ import annotations

from src.nodes.match.contract import MatchEnvelope


def test_decision_recommendation_normalizes_spanish_label() -> None:
    out = MatchEnvelope.model_validate(
        {
            "matches": [
                {
                    "req_id": "R1",
                    "match_score": 0.0,
                    "evidence_id": None,
                    "reasoning": "No evidence",
                }
            ],
            "total_score": 0.0,
            "decision_recommendation": "Rechazar",
            "summary_notes": "low fit",
        }
    )
    assert out.decision_recommendation == "reject"


def test_decision_recommendation_normalizes_sentence_value() -> None:
    out = MatchEnvelope.model_validate(
        {
            "matches": [
                {
                    "req_id": "R1",
                    "match_score": 0.2,
                    "evidence_id": None,
                    "reasoning": "Weak fit",
                }
            ],
            "total_score": 0.2,
            "decision_recommendation": "Reject. Many requirements remain unaddressed.",
            "summary_notes": "low fit",
        }
    )
    assert out.decision_recommendation == "reject"


def test_decision_recommendation_normalizes_no_recomendado_phrase() -> None:
    out = MatchEnvelope.model_validate(
        {
            "matches": [
                {
                    "req_id": "R1",
                    "match_score": 0.2,
                    "evidence_id": None,
                    "reasoning": "Weak fit",
                }
            ],
            "total_score": 0.2,
            "decision_recommendation": "No recomendado. El perfil no cumple requisitos clave.",
            "summary_notes": "low fit",
        }
    )
    assert out.decision_recommendation == "reject"


def test_evidence_id_normalizes_list_to_comma_string() -> None:
    out = MatchEnvelope.model_validate(
        {
            "matches": [
                {
                    "req_id": "R1",
                    "match_score": 0.9,
                    "evidence_id": ["P1", "P2"],
                    "reasoning": "Strong fit",
                }
            ],
            "total_score": 0.9,
            "decision_recommendation": "proceed",
            "summary_notes": "ok",
        }
    )
    assert out.matches[0].evidence_id == "P1, P2"
