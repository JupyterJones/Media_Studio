import ast
import os
from icecream import ic

class FlaskInspector(ast.NodeVisitor):
    def __init__(self):
        self.routes = []
        self.templates = []

    def visit_FunctionDef(self, node):
        # Look for @app.route decorators
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call) and getattr(decorator.func, 'attr', None) == 'route':
                if decorator.args:
                    route = self._get_constant(decorator.args[0])
                    self.routes.append((route, node.name))
        # Look for render_template calls in the function body
        for child in ast.walk(node):
            if isinstance(child, ast.Call) and getattr(child.func, 'id', None) == 'render_template':
                if child.args:
                    template = self._get_constant(child.args[0])
                    self.templates.append((node.name, template))
        self.generic_visit(node)

    def _get_constant(self, node):
        if isinstance(node, ast.Constant):  # Python 3.8+
            return node.value
        elif isinstance(node, ast.Str):  # Python < 3.8
            return node.s
        return None

def analyze_flask_app(filepath, templates_dir="templates"):
    with open(filepath, "r") as f:
        tree = ast.parse(f.read(), filename=filepath)

    inspector = FlaskInspector()
    inspector.visit(tree)

    ic("Routes", inspector.routes)
    ic("Templates", inspector.templates)

    print("\n=== Flask Routes Found ===")
    for route, func in inspector.routes:
        print(f"  {route} -> {func}()")

    print("\n=== Templates Used ===")
    for func, template in inspector.templates:
        exists = os.path.exists(os.path.join(templates_dir, template))
        status = "✅ Found" if exists else "❌ Missing"
        print(f"  {func} -> {template} [{status}]")

if __name__ == "__main__":
    # Adjust this to point at your Flask app
    analyze_flask_app("studio_flask.py")