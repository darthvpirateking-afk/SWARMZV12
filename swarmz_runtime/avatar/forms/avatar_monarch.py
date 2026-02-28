from __future__ import annotations


class AvatarMonarch:
    form_id = "AvatarMonarch"
    base_form = "AvatarSovereign"
    aura = "shadow-cosmic"
    wing_style = "black-blue fractal"
    eye_glow = "cyan-white"
    glyph_storm = True
    summon_tier = "monarch"
    combat_multiplier = 1.35
    speed_multiplier = 1.20
    defense_multiplier = 1.15

    def profile(self) -> dict[str, object]:
        return {
            "form_id": self.form_id,
            "base_form": self.base_form,
            "aura": self.aura,
            "wing_style": self.wing_style,
            "eye_glow": self.eye_glow,
            "glyph_storm": self.glyph_storm,
            "summon_tier": self.summon_tier,
            "combat_multiplier": self.combat_multiplier,
            "speed_multiplier": self.speed_multiplier,
            "defense_multiplier": self.defense_multiplier,
        }
