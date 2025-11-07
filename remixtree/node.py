class RemixNodes:
    def __init__(self, project_id, title, shared_date=None):
        self.project_id = project_id 
        self.title = title
        self.children = []
        self.shared_date = shared_date

    def add_child(self, child_node):
        self.children.append(child_node)
        
    def sort_children_by_share_date(self, reverse=False):
        """sort the kids by share date, oldest first by default"""
        self.children.sort(
            key=lambda node: node.shared_date or "", 
            reverse=reverse
        )
        
        for child in self.children:
            child.sort_children_by_share_date(reverse)
            

    def generate_tree(self, prefix="", is_last=True, depth=0, use_color=True):
        # should i remove the color thing? it's somewhat useless
        DEPTH_COLORS = ["cyan", "green", "yellow", "magenta", "blue", "red", "white"]
        
        connector = "└── " if is_last else "├── "
        node_text = f"{self.title}({self.project_id})"
        
        if use_color:
            color = DEPTH_COLORS[depth % len(DEPTH_COLORS)]
            node_text = f"[{color}]{node_text}[/{color}]"
        
        result = prefix + connector + node_text + "\n"
        
        new_prefix = prefix + ("    " if is_last else "│   ")
        
        for i, child in enumerate(self.children):
            result += child.generate_tree(new_prefix, i == len(self.children) - 1, depth + 1, use_color)
        
        return result
