class RemixNodes:
    def __init__(self, project_id, title):
        self.project_id = project_id 
        self.title = title
        self.children = []

    def add_child(self, child_node):
        self.children.append(child_node)

    def print_tree(self, prefix="", is_last=True, depth=0, use_color=True):
        # note to later me: find a way to get color into text files without showing the rich format codes...
        DEPTH_COLORS = ["cyan", "green", "yellow", "magenta", "blue", "red", "white"]
        
        connector = "└── " if is_last else "├── "
        node_text = f"{self.title}({self.project_id})"
        
        if use_color:
            color = DEPTH_COLORS[depth % len(DEPTH_COLORS)]
            node_text = f"[{color}]{node_text}[/{color}]"
        
        print(prefix + connector + node_text)
        
        prefix += "    " if is_last else "│   "
        
        for i, child in enumerate(self.children):
            child.print_tree(prefix, i == len(self.children) - 1, depth + 1, use_color)
