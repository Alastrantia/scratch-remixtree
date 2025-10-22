class RemixNodes:
    def __init__(self, value):
        self.value = value
        self.children = []

    def add_child(self, child_node):
        self.children += child_node
