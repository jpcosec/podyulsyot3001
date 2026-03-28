"""Spanish language bundle."""

from src.render.languages.es.common import COMMON
from src.render.languages.es.cv import CV
from src.render.languages.es.letter import LETTER

LANGUAGE = {
    "code": "es",
    "common": COMMON,
    "documents": {
        "cv": CV,
        "letter": LETTER,
    },
}
