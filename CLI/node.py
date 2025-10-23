class RemixNodes:
    def __init__(self, project_id):
        self.project_id = project_id 
        self.children = []

    def add_child(self, child_node):
        self.children.append(child_node)

    def print_tree(self, prefix="", is_last=True):
        connector = "└── " if is_last else "├── "
        print(prefix + connector + str(self.project_id)) 

        prefix += "    " if is_last else "│   "

        for i, child in enumerate(self.children):
            child.print_tree(prefix, i == len(self.children) - 1)
