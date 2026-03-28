"""English language bundle."""

from src.render.languages.en.common import COMMON
from src.render.languages.en.cv import CV
from src.render.languages.en.letter import LETTER

LANGUAGE = {
    "code": "en",
    "common": COMMON,
    "documents": {
        "cv": CV,
        "letter": LETTER,
    },
}
