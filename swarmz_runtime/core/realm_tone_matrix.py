from .persona_layer import Realm


class RealmToneMatrix:
    """
    RealmToneMatrix
    ----------------
    - Maps realms to tone + metaphor profile.
    - Expression only, no emotion.
    """

    _MATRIX = {
        Realm.MATRIX: {
            "tone": "neutral-structured",
            "metaphor_level": "low",
        },
        Realm.AETHER: {
            "tone": "elevated-reflective",
            "metaphor_level": "medium",
        },
        Realm.FORGE: {
            "tone": "sharp-direct",
            "metaphor_level": "low",
        },
        Realm.PRISM: {
            "tone": "creative-fluid",
            "metaphor_level": "high",
        },
        Realm.ABYSS: {
            "tone": "cold-analytical",
            "metaphor_level": "minimal",
        },
        Realm.COSMOS: {
            "tone": "grand-ceremonial",
            "metaphor_level": "medium-high",
        },
    }

    def get_style(self, realm: Realm) -> dict:
        return self._MATRIX[realm]
