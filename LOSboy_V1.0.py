import os
import json

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.label import Label

from pyboy.utils import WindowEvent


SETTINGS_FILE = "LOSboy_settings.json"


class LOSboy(BoxLayout):

    def __init__(self, api, memory, save_fn, load_fn, **kwargs):
        super().__init__(orientation="vertical", **kwargs)

        self.api = api
        self.memory = memory

        self.pyboy = None
        self.clock = None
        self.rom = None

        self.settings = self.load_settings()
        self.rom_folders = self.settings.get("rom_folders", [])

        self.build_menu()

    # ================= SETTINGS =================
    def load_settings(self):
        if not os.path.exists(SETTINGS_FILE):
            return {"rom_folders": [], "fps": False, "speed": 1}

        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except:
            return {"rom_folders": [], "fps": False, "speed": 1}

    def save_settings(self):
        with open(SETTINGS_FILE, "w") as f:
            json.dump(self.settings, f)

    # ================= MENU =================
    def build_menu(self):
        self.clear_widgets()

        menu = BoxLayout(orientation="vertical")

        menu.add_widget(Label(text="LOSboy Emulator", font_size=30))

        menu.add_widget(Button(text="Load ROM", on_press=self.open_picker))
        menu.add_widget(Button(text="ROM Library", on_press=self.open_library))
        menu.add_widget(Button(text="Settings", on_press=self.open_settings))

        self.add_widget(menu)

    # ================= GAME UI =================
    def build_game_ui(self):
        self.clear_widgets()

        self.screen = Image(
            size_hint=(1, 0.82),
            allow_stretch=True,
            keep_ratio=False
        )

        controls = BoxLayout(size_hint=(1, 0.18), orientation="vertical")

        # D-PAD
        dpad = BoxLayout(size_hint=(1, 0.4))

        self.btn_left = Button(text="LEFT")
        self.btn_up = Button(text="UP")
        self.btn_down = Button(text="DOWN")
        self.btn_right = Button(text="RIGHT")

        dpad.add_widget(self.btn_left)
        dpad.add_widget(self.btn_up)
        dpad.add_widget(self.btn_down)
        dpad.add_widget(self.btn_right)

        # A / B
        ab = BoxLayout(size_hint=(1, 0.3))

        self.btn_a = Button(text="A")
        self.btn_b = Button(text="B")

        ab.add_widget(self.btn_a)
        ab.add_widget(self.btn_b)

        # START / SELECT
        sys = BoxLayout(size_hint=(1, 0.3))

        self.btn_start = Button(text="START")
        self.btn_select = Button(text="SELECT")

        sys.add_widget(self.btn_start)
        sys.add_widget(self.btn_select)

        controls.add_widget(dpad)
        controls.add_widget(ab)
        controls.add_widget(sys)

        self.add_widget(self.screen)
        self.add_widget(controls)

    # ================= INPUT SYSTEM =================
    def bind_inputs(self):

        def bind(btn, press, release):
            btn.bind(
                on_press=lambda x: self.pyboy.send_input(press),
                on_release=lambda x: self.pyboy.send_input(release)
            )

        bind(self.btn_left, WindowEvent.PRESS_ARROW_LEFT, WindowEvent.RELEASE_ARROW_LEFT)
        bind(self.btn_right, WindowEvent.PRESS_ARROW_RIGHT, WindowEvent.RELEASE_ARROW_RIGHT)
        bind(self.btn_up, WindowEvent.PRESS_ARROW_UP, WindowEvent.RELEASE_ARROW_UP)
        bind(self.btn_down, WindowEvent.PRESS_ARROW_DOWN, WindowEvent.RELEASE_ARROW_DOWN)

        bind(self.btn_a, WindowEvent.PRESS_BUTTON_A, WindowEvent.RELEASE_BUTTON_A)
        bind(self.btn_b, WindowEvent.PRESS_BUTTON_B, WindowEvent.RELEASE_BUTTON_B)

        bind(self.btn_start, WindowEvent.PRESS_BUTTON_START, WindowEvent.RELEASE_BUTTON_START)
        bind(self.btn_select, WindowEvent.PRESS_BUTTON_SELECT, WindowEvent.RELEASE_BUTTON_SELECT)

    # ================= ROM PICKER =================
    def open_picker(self, *_):
        picker = FileChooserIconView()
        pop = Popup(title="Select ROM", content=picker, size_hint=(0.9, 0.9))

        def sel(_, s, __):
            if s:
                pop.dismiss()
                self.start_rom(s[0])

        picker.bind(on_submit=sel)
        pop.open()

    # ================= ROM LIBRARY =================
    def open_library(self, *_):
        box = BoxLayout(orientation="vertical")

        found = []

        for folder in self.rom_folders:
            if os.path.isdir(folder):
                for f in os.listdir(folder):
                    if f.endswith((".gb", ".gbc")):
                        found.append(os.path.join(folder, f))

        if not found:
            box.add_widget(Label(text="No ROMs found"))
        else:
            for rom in found:
                btn = Button(text=os.path.basename(rom), size_hint_y=None, height=50)
                btn.bind(on_press=lambda x, r=rom: self.start_rom(r))
                box.add_widget(btn)

        Popup(title="ROM Library", content=box, size_hint=(0.9, 0.9)).open()

    # ================= SETTINGS =================
    def open_settings(self, *_):
        box = BoxLayout(orientation="vertical")

        def add_folder(_):
            picker = FileChooserIconView(dirselect=True)
            inner = BoxLayout(orientation="vertical")

            selected = {"path": None}
            label = Label(text="No folder selected")

            def on_select(_, selection, __):
                if selection:
                    selected["path"] = selection[0]
                    label.text = selected["path"]

            picker.bind(on_submit=on_select)

            def use_folder(_):
                path = selected["path"]
                if not path:
                    return

                if path not in self.rom_folders:
                    self.rom_folders.append(path)
                    self.settings["rom_folders"] = self.rom_folders
                    self.save_settings()

                pop.dismiss()

            btn_use = Button(text="Use This Folder")
            btn_use.bind(on_press=use_folder)

            inner.add_widget(picker)
            inner.add_widget(label)
            inner.add_widget(btn_use)

            pop = Popup(title="Select ROM Folder", content=inner, size_hint=(0.95, 0.95))
            pop.open()

        box.add_widget(Button(text="Add ROM Folder", on_press=add_folder))

        Popup(title="Settings", content=box, size_hint=(0.85, 0.85)).open()

    # ================= START EMULATOR =================
    def start_rom(self, rom_path):
        from pyboy import PyBoy

        self.rom = rom_path
        self.build_game_ui()

        if self.clock:
            self.clock.cancel()

        self.pyboy = PyBoy(rom_path, window_type="headless")

        for _ in range(10):
            self.pyboy.tick()

        self.bind_inputs()

        self.clock = Clock.schedule_interval(self.update, 1 / 60)

    # ================= RENDER LOOP =================
    def update(self, dt):
        if not self.pyboy:
            return

        speed = self.settings.get("speed", 1)
        for _ in range(speed):
            self.pyboy.tick()

        frame = self.pyboy.screen.ndarray
        if frame is None:
            return

        if frame.shape[2] == 4:
            frame = frame[:, :, :3]

        tex = Texture.create(
            size=(frame.shape[1], frame.shape[0]),
            colorfmt="rgb"
        )

        tex.blit_buffer(frame.tobytes(), colorfmt="rgb", bufferfmt="ubyte")
        tex.flip_vertical()

        self.screen.texture = tex


# ================= ENTRY =================
def run(api, memory, save_fn, load_fn):
    return LOSboy(api, memory, save_fn, load_fn)


APP_NAME = "LOSboy"
APP_ICON = "🎮"