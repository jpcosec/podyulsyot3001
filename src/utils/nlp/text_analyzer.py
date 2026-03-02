import re
from datetime import datetime
from typing import Any

import spacy

SUPPORTED_MODELS: dict[str, str] = {
    "en": "en_core_web_sm",
    # Future: "de": "de_core_news_sm", "nl": "nl_core_news_sm", "es": "es_core_news_sm"
}

_SECTION_PATTERNS: dict[str, list[str]] = {
    "en": [
        r"\b(education|academic|qualification|degree)\b",
        r"\b(experience|employment|work history|professional background)\b",
        r"\b(skills|abilities|competencies|expertise)\b",
        r"\b(projects|portfolio|achievements|publications)\b",
        r"\b(contact|information|profile|summary)\b",
    ],
}

_SECTION_LABELS: dict[str, list[str]] = {
    "en": ["Education", "Experience", "Skills", "Projects/Achievements", "Contact"],
}

_ACTION_VERBS: dict[str, list[str]] = {
    "en": [
        "achieved", "improved", "developed", "managed", "created", "implemented",
        "increased", "decreased", "led", "coordinated", "designed", "launched",
        "built", "delivered", "generated", "reduced", "resolved",
    ],
}


class TextAnalyzer:
    """spaCy-based CV text analyzer. English-only; language registry ready for future expansion."""

    def __init__(self, lang: str = "en") -> None:
        if lang not in SUPPORTED_MODELS:
            raise ValueError(f"Unsupported language: {lang!r}. Supported: {list(SUPPORTED_MODELS)}")
        self.lang = lang
        self.nlp = spacy.load(SUPPORTED_MODELS[lang])

    def extract_keywords(self, text: str) -> list[str]:
        doc = self.nlp(text)
        return list({
            token.lemma_.lower()
            for token in doc
            if token.pos_ in {"NOUN", "VERB", "PROPN", "ADJ"}
            and not token.is_stop
            and len(token.text) > 2
        })

    def analyze_formatting(self, text: str) -> dict[str, Any]:
        patterns = _SECTION_PATTERNS[self.lang]
        labels = _SECTION_LABELS[self.lang]
        identified: list[str] = []
        for pattern, label in zip(patterns, labels):
            if re.search(pattern, text, re.IGNORECASE):
                identified.append(label)

        section_score = min(30, len(identified) * 6)
        has_bullets = bool(re.search(r"(^|\n)\s*[-*\u2022\uf0b7]", text))
        has_email = bool(re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text))
        has_phone = bool(re.search(r"\+?[\d\s()\-]{7,}", text))
        total = section_score + (20 if has_bullets else 0) + (10 if has_email else 0) + (10 if has_phone else 0)

        issues: list[str] = []
        if len(identified) < 3:
            issues.append("Add clear section headers: Education, Experience, Skills.")
        if not has_bullets:
            issues.append("Use bullet points in experience and skills sections.")
        if not (has_email and has_phone):
            issues.append("Include both email and phone in the header.")

        desired = ["Education", "Experience", "Skills"]
        return {
            "score": min(100, total),
            "issues": issues,
            "identified_sections": identified,
            "missing_sections": [s for s in desired if s not in identified],
        }

    def analyze_content(self, text: str) -> dict[str, Any]:
        verbs = _ACTION_VERBS[self.lang]
        verb_count = sum(len(re.findall(r"\b" + v + r"\b", text, re.IGNORECASE)) for v in verbs)
        numbers_found = len(re.findall(r"\b\d+%?\b", text))
        keywords = self.extract_keywords(text)
        verb_score = min(30, verb_count * 3)
        numbers_score = min(25, numbers_found * 5)
        keyword_score = min(25, len(keywords))

        doc = self.nlp(text)
        sentences = [s.text for s in doc.sents]
        avg_len = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
        sentence_score = 10 if 8 <= avg_len <= 20 else 5

        issues: list[str] = []
        if verb_count < 5:
            issues.append("Use more action verbs (achieved, built, designed, led).")
        if numbers_found < 3:
            issues.append("Quantify achievements with numbers or percentages.")

        return {"score": min(100, verb_score + numbers_score + keyword_score + sentence_score), "issues": issues}

    def analyze_readability(self, text: str) -> dict[str, Any]:
        word_count = len(text.split())
        if 300 <= word_count <= 700:
            length_score = 25
        elif 200 <= word_count < 300 or 700 < word_count <= 1000:
            length_score = 15
        else:
            length_score = 5

        issues: list[str] = []
        if word_count < 200:
            issues.append("CV is too short — add more detail.")
        elif word_count > 1000:
            issues.append("CV is too long — condense to key information.")

        complex_ratio = sum(1 for w in text.split() if len(w) > 12) / max(len(text.split()), 1)
        complexity_score = 25 if complex_ratio < 0.05 else (15 if complex_ratio < 0.1 else 5)

        return {"score": min(100, length_score + 25 + complexity_score + 25), "issues": issues}

    def match_keywords(self, cv_text: str, jd_text: str) -> dict[str, Any]:
        cv_kw = set(self.extract_keywords(cv_text))
        jd_kw = set(self.extract_keywords(jd_text))
        matching = sorted(cv_kw & jd_kw)
        missing = sorted(jd_kw - cv_kw)
        pct = int(len(matching) / len(jd_kw) * 100) if jd_kw else 0
        issues: list[str] = []
        if pct < 30:
            issues.append("Very low keyword match — incorporate more JD terminology.")
        elif pct < 60:
            issues.append("Moderate keyword match — add more specific JD terms.")
        return {"score": pct, "matching_keywords": matching, "missing_keywords": missing, "issues": issues}

    def analyze(self, cv_text: str, job_description: str = "") -> dict[str, Any]:
        formatting = self.analyze_formatting(cv_text)
        content = self.analyze_content(cv_text)
        readability = self.analyze_readability(cv_text)
        keyword = (
            self.match_keywords(cv_text, job_description)
            if job_description
            else {"score": 0, "matching_keywords": [], "missing_keywords": [], "issues": []}
        )

        if job_description:
            overall = int(
                0.35 * keyword["score"]
                + 0.25 * formatting["score"]
                + 0.25 * content["score"]
                + 0.15 * readability["score"]
            )
        else:
            overall = int(
                0.40 * formatting["score"]
                + 0.40 * content["score"]
                + 0.20 * readability["score"]
            )

        recommendations: list[str] = (
            formatting["issues"] + content["issues"] + readability["issues"] + keyword["issues"]
        )

        return {
            "id": f"ats_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "success": True,
            "analysis_date": datetime.now().isoformat(),
            "score": max(0, min(100, overall)),
            "score_breakdown": {
                "keyword_score": keyword["score"],
                "format_score": formatting["score"],
                "content_score": content["score"],
                "readability_score": readability["score"],
            },
            "skills_comparison": {
                "match_percentage": keyword["score"],
                "matching_keywords": keyword["matching_keywords"],
                "missing_keywords": keyword["missing_keywords"],
            },
            "recommendations": recommendations,
            "identified_sections": formatting["identified_sections"],
            "missing_sections": formatting["missing_sections"],
        }
