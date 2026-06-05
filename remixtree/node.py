from rich.markup import escape


def fmt_count(n):
    """make big numbers human, 12345 -> 12.3k (scratch projects get silly numbers sometimes)"""
    try:
        n = int(n)
    except (TypeError, ValueError):
        return "0"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}k"
    return str(n)


def extract_metadata(blob):
    """pulls the bits we care about out of a scratch project/remix blob.
    i had this copy-pasted in like 3 places before, never again"""
    stats = blob.get("stats") or {}
    history = blob.get("history") or {}
    return {
        "shared_date": history.get("shared"),
        "likes": stats.get("loves", 0),
        "favorites": stats.get("favorites", 0),
        "views": stats.get("views", 0),
        "description": blob.get("description", "") or "",
    }


class RemixNodes:
    def __init__(self, project_id, title, shared_date=None, likes=0, favorites=0, views=0, description=""):
        self.project_id = project_id
        self.title = title if title is not None else "Untitled"
        self.children = []
        self.shared_date = shared_date
        # the api loves handing back None, coerce so sorting/formatting doesnt explode
        self.likes = likes or 0
        self.views = views or 0
        self.favorites = favorites or 0
        self.description = description or ""

    @classmethod
    def from_project_data(cls, data):
        """build a node straight from a scratch api project/remix blob"""
        return cls(data["id"], data.get("title"), **extract_metadata(data))

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

    def count_nodes(self):
        """how many projects are in here including me (root + all the kids)"""
        return 1 + sum(child.count_nodes() for child in self.children)

    def max_depth(self):
        """how deep does the rabbit hole go (root is 0)"""
        if not self.children:
            return 0
        return 1 + max(child.max_depth() for child in self.children)

    def iter_nodes(self, _depth=0, _parent_id=None):
        """walk every node, handing back (node, depth, parent_id). handy for csv etc."""
        yield (self, _depth, _parent_id)
        for child in self.children:
            yield from child.iter_nodes(_depth + 1, self.project_id)

    def _stats_suffix(self):
        return f"  ♥{fmt_count(self.likes)} \U0001f441{fmt_count(self.views)} ★{fmt_count(self.favorites)}"

    def generate_tree(self, prefix="", is_last=True, depth=0, use_color=False, show_stats=False):
        """the classic ascii tree, this is what ends up in the saved .txt file"""
        # should i remove the color thing? it's somewhat useless... keeping it, off by default now
        DEPTH_COLORS = ["cyan", "green", "yellow", "magenta", "blue", "red", "white"]

        connector = "└── " if is_last else "├── "
        node_text = f"{self.title}({self.project_id})"
        if show_stats:
            node_text += self._stats_suffix()

        if use_color:
            color = DEPTH_COLORS[depth % len(DEPTH_COLORS)]
            node_text = f"[{color}]{node_text}[/{color}]"

        result = prefix + connector + node_text + "\n"

        new_prefix = prefix + ("    " if is_last else "│   ")

        for i, child in enumerate(self.children):
            result += child.generate_tree(new_prefix, i == len(self.children) - 1, depth + 1, use_color, show_stats)

        return result

    def to_rich_tree(self, color=False, show_stats=False, max_nodes=None, _budget=None, _parent=None, _depth=0):
        """build a proper rich.tree.Tree so the terminal preview actually looks nice.
        max_nodes caps how much we draw so huge trees dont nuke the scrollback"""
        from rich.tree import Tree as RichTree

        DEPTH_COLORS = ["bright_cyan", "green", "yellow", "magenta", "bright_blue", "red", "white"]
        if _budget is None:
            _budget = [0]

        # escape the title, scratch titles love using [brackets] which rich would eat
        safe_title = escape(str(self.title))
        if color:
            c = DEPTH_COLORS[_depth % len(DEPTH_COLORS)]
            label = f"[{c}]{safe_title}[/{c}] [dim]({self.project_id})[/dim]"
        else:
            label = f"{safe_title} [dim]({self.project_id})[/dim]"
        if show_stats:
            label += (
                f"  [red]♥{fmt_count(self.likes)}[/red]"
                f" [blue]\U0001f441{fmt_count(self.views)}[/blue]"
                f" [yellow]★{fmt_count(self.favorites)}[/yellow]"
            )

        if _parent is None:
            rt = RichTree(label, guide_style="grey42")
        else:
            rt = _parent.add(label)
        _budget[0] += 1

        for child in self.children:
            if max_nodes is not None and _budget[0] >= max_nodes:
                rt.add("[dim]… (more hidden, use -o to save the whole thing)[/dim]")
                break
            child.to_rich_tree(color, show_stats, max_nodes, _budget, rt, _depth + 1)

        return rt

    def to_dict(self, include_stats=True, include_description=False):
        """nested dict, this is what the web backend ships to the browser as json"""
        d = {
            "id": self.project_id,
            "title": self.title,
            "shared_date": self.shared_date,
        }
        if include_stats:
            d["likes"] = self.likes
            d["views"] = self.views
            d["favorites"] = self.favorites
            d["remix_count"] = len(self.children)
        if include_description:
            d["description"] = self.description
        d["children"] = [child.to_dict(include_stats, include_description) for child in self.children]
        return d
