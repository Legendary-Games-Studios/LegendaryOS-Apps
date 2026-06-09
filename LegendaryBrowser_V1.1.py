APP_NAME = "Browser"
APP_ICON = "🌐"

def run(os_api, state, save, load):
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.textinput import TextInput
    from kivy.uix.button import Button
    from kivy.uix.widget import Widget
    from kivy.clock import Clock
    from kivy.graphics import Color, Rectangle, Line
    from kivy.core.text import Label as CoreLabel
    from kivy.uix.label import Label

    import urllib.request
    import urllib.parse
    import json
    import collections

    # -------------------------------------------------------------------------
    # DOM NODE
    # -------------------------------------------------------------------------
    class DOMNode:
        def __init__(self, tag_name, parent=None):
            self.tag_name = tag_name.lower()
            self.parent = parent
            self.children = []
            self.attributes = {}
            self.text_content = ""
            self.computed_style = {
                "display": "block",
                "font-size": 14,
                "color": (0.1, 0.1, 0.1, 1),
                "background-color": (1, 1, 1, 0),
                "border-color": (0, 0, 0, 0),
            }

        def append_child(self, child):
            child.parent = self
            self.children.append(child)

    # -------------------------------------------------------------------------
    # SIMPLE LAYOUT ENGINE
    # -------------------------------------------------------------------------
    class LayoutEngine:
        @staticmethod
        def resolve_styles(node):
            if node.tag_name in ["h1"]:
                node.computed_style["font-size"] = 22
            elif node.tag_name in ["a"]:
                node.computed_style["color"] = (0.1, 0.3, 0.9, 1)

            for c in node.children:
                LayoutEngine.resolve_styles(c)

        @staticmethod
        def compute_layout(node, x, y, max_width, out):
            cursor_y = y

            for child in node.children:
                if child.tag_name in ["script", "style"]:
                    continue

                text = child.text_content.strip()
                font_size = child.computed_style["font-size"]

                box_height = font_size + 20
                box_width = max_width - 20

                pos = (x + 10, cursor_y - box_height)
                size = (box_width, box_height)

                out.append({
                    "node": child,
                    "text": text,
                    "pos": pos,
                    "size": size,
                    "style": child.computed_style
                })

                cursor_y -= (box_height + 10)

            return cursor_y

    # -------------------------------------------------------------------------
    # VIEWPORT
    # -------------------------------------------------------------------------
    class Viewport(Widget):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.dom_root = None
            self.layout = []

        def render_dom(self, root):
            self.dom_root = root
            self.draw()

        def draw(self):
            self.canvas.clear()
            self.layout = []

            if not self.dom_root:
                return

            LayoutEngine.resolve_styles(self.dom_root)
            LayoutEngine.compute_layout(
                self.dom_root,
                self.x,
                self.top,
                self.width,
                self.layout
            )

            with self.canvas:
                Color(0.97, 0.97, 0.98, 1)
                Rectangle(pos=self.pos, size=self.size)

            for item in self.layout:
                pos = item["pos"]
                size = item["size"]
                text = item["text"]
                style = item["style"]
                node = item["node"]

                with self.canvas:
                    if text:
                        label = CoreLabel(text=text, font_size=style["font-size"], color=style["color"])
                        label.refresh()
                        tex = label.texture

                        Color(*style["color"])
                        Rectangle(texture=tex, pos=(pos[0], pos[1]), size=tex.size)

    # -------------------------------------------------------------------------
    # DUCKDUCKGO SEARCH ENGINE
    # -------------------------------------------------------------------------
    def fetch_and_compile(query):
        status.text = "Searching DuckDuckGo..."

        try:
            q = urllib.parse.quote(query)
            url = f"https://api.duckduckgo.com/?q={q}&format=json&no_html=1&skip_disambig=1"

            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0"
            })

            with urllib.request.urlopen(req, timeout=6) as r:
                data = json.loads(r.read().decode("utf-8"))

            root = DOMNode("document")

            heading = data.get("Heading", "")
            abstract = data.get("AbstractText", "")
            link = data.get("AbstractURL", "")

            if heading:
                h = DOMNode("h1")
                h.text_content = heading
                root.append_child(h)

            if abstract:
                p = DOMNode("p")
                p.text_content = abstract
                root.append_child(p)

            if link:
                a = DOMNode("a")
                a.text_content = "Open Source Link"
                a.attributes["href"] = link
                root.append_child(a)

            if not heading and not abstract:
                p = DOMNode("p")
                p.text_content = "No results found."
                root.append_child(p)

            viewport.render_dom(root)
            status.text = "Results loaded."

            save("last_query", query)

        except Exception as e:
            err = DOMNode("document")
            h = DOMNode("h1")
            h.text_content = "Search Error"
            p = DOMNode("p")
            p.text_content = str(e)
            err.append_child(h)
            err.append_child(p)
            viewport.render_dom(err)

    # -------------------------------------------------------------------------
    # UI
    # -------------------------------------------------------------------------
    layout = BoxLayout(orientation="vertical")

    top = BoxLayout(size_hint_y=0.1)

    url_input = TextInput(text="Search something...", multiline=False)

    def go(instance):
        query = url_input.text.strip()
        fetch_and_compile(query)

    go_btn = Button(text="Search", on_release=go)

    top.add_widget(url_input)
    top.add_widget(go_btn)

    viewport = Viewport()

    status = Label(text="Ready", size_hint_y=0.05)

    layout.add_widget(top)
    layout.add_widget(viewport)
    layout.add_widget(status)

    Clock.schedule_once(lambda dt: fetch_and_compile(load("last_query") or "hello"), 0.2)

    return layout