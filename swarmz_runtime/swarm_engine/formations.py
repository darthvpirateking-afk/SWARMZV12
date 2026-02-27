class Formation:
    def __init__(self, formation_type):
        self.formation_type = formation_type

    def execute_formation(self):
        return f"Executing {self.formation_type} formation"


class LineFormation(Formation):
    def __init__(self):
        super().__init__("Line")


class GridFormation(Formation):
    def __init__(self):
        super().__init__("Grid")


class ClusterFormation(Formation):
    def __init__(self):
        super().__init__("Cluster")


class ThreadFormation(Formation):
    def __init__(self):
        super().__init__("Thread")
