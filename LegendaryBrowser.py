APP_NAME = "Browser"
APP_ICON = "🌐"

def run(os_api, state, save, load):
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.textinput import TextInput
    from kivy.uix.button import Button
    from kivy.uix.label import Label
    from kivy.clock import Clock

    layout = BoxLayout(orientation="vertical")

    url = TextInput(
        text=load("last_url") or "https://google.com",
        size_hint_y=0.1,
        multiline=False
    )

    status = Label(text="Ready", size_hint_y=0.1)

    web = {"view": None}

    def init_webview():
        try:
            from jnius import autoclass

            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            WebView = autoclass("android.webkit.WebView")

            activity = PythonActivity.mActivity

            wv = WebView(activity)
            wv.getSettings().setJavaScriptEnabled(True)
            wv.getSettings().setDomStorageEnabled(True)

            activity.setContentView(wv)

            web["view"] = wv
            status.text = "WebView active"

        except Exception as e:
            status.text = f"WebView error: {e}"

    def go(instance):
        link = url.text.strip()

        if not link.startswith("http"):
            link = "https://" + link

        save("last_url", link)

        if web["view"]:
            web["view"].loadUrl(link)

    def back(instance):
        if web["view"] and web["view"].canGoBack():
            web["view"].goBack()

    def forward(instance):
        if web["view"] and web["view"].canGoForward():
            web["view"].goForward()

    def reload(instance):
        if web["view"]:
            web["view"].reload()

    def exit_browser(instance):
        try:
            from kivy.app import App
            from jnius import autoclass

            app = App.get_running_app()
            PythonActivity = autoclass("org.kivy.android.PythonActivity")

            activity = PythonActivity.mActivity
            activity.setContentView(app.root)

        except:
            pass

    # UI controls
    top = BoxLayout(size_hint_y=0.1)
    top.add_widget(url)
    top.add_widget(Button(text="Go", on_release=go))

    nav = BoxLayout(size_hint_y=0.1)
    nav.add_widget(Button(text="⬅", on_release=back))
    nav.add_widget(Button(text="➡", on_release=forward))
    nav.add_widget(Button(text="⟳", on_release=reload))
    nav.add_widget(Button(text="Exit", on_release=exit_browser))

    layout.add_widget(top)
    layout.add_widget(nav)
    layout.add_widget(status)

    Clock.schedule_once(lambda dt: init_webview(), 0.2)

    return layout