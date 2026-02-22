from .persona_layer import Form


class FormEvolutionMap:
    """
    FormEvolutionMap
    ----------------
    - Maps evolution stage to density + formality.
    - Higher forms = more compressed, more formal.
    """

    _MAP = {
        Form.NODE: {
            "density": "low",
            "formality": "low",
        },
        Form.SPARK: {
            "density": "medium",
            "formality": "low-medium",
        },
        Form.FLOW: {
            "density": "medium",
            "formality": "medium",
        },
        Form.SHARD: {
            "density": "medium-high",
            "formality": "medium-high",
        },
        Form.CORE: {
            "density": "high",
            "formality": "high",
        },
        Form.ASCENDANT: {
            "density": "very-high",
            "formality": "high-ceremonial",
        },
    }

    def get_style(self, form: Form) -> dict:
        return self._MAP[form]
