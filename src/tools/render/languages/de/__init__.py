"""German language bundle."""

from src.render.languages.de.common import COMMON
from src.render.languages.de.cv import CV
from src.render.languages.de.letter import LETTER

LANGUAGE = {
    "code": "de",
    "common": COMMON,
    "documents": {
        "cv": CV,
        "letter": LETTER,
    },
}
