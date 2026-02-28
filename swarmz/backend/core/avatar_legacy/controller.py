# controller.py
# Controls avatar behavior.


class AvatarController:
    def control(self, avatar, command):
        """Control the avatar."""
        return {"status": "controlled", "avatar": avatar, "command": command}
