import os
import json
import numpy as np

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.label import Label

from nes_py import NESEnv

SETTINGS_FILE = "LOSnes_settings.json"

class LOSnes(BoxLayout):

    def __init__(self, api, memory, save_fn, load_fn, **kwargs):
        super().__init__(orientation="vertical", **kwargs)

        self.api = api
        self.memory = memory
        self.save_fn = save_fn
        self.load_fn = load_fn

        self.env = None
        self.clock = None
        self.rom = None
        
        # Track buttons individually as booleans
        # Format: [A, B, Select, Start, Up, Down, Left, Right]
        self.joypad_state = [False] * 8

        self.settings = self.load_settings()
        self.rom_folders = self.settings.get("rom_folders", [])

        self.build_menu()

    # ================= SETTINGS =================
    def load_settings(self):
        if not os.path.exists(SETTINGS_FILE):
            return {"rom_folders": [], "speed": 1}
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except:
            return {"rom_folders": [], "speed": 1}

    def save_settings(self):
        with open(SETTINGS_FILE, "w") as f:
            json.dump(self.settings, f)

    # ================= UI MENU =================
    def build_menu(self):
        self.clear_widgets()
        menu = BoxLayout(orientation="vertical", padding=20, spacing=10)
        menu.add_widget(Label(text="LOSnes Emulator", font_size=30))
        menu.add_widget(Button(text="Load NES ROM", on_press=self.open_picker))
        menu.add_widget(Button(text="NES Library", on_press=self.open_library))
        menu.add_widget(Button(text="Settings", on_press=self.open_settings))
        self.add_widget(menu)

    # ================= GAMEPLAY UI =================
    def build_game_ui(self):
        self.clear_widgets()

        self.screen = Image(
            size_hint=(1, 0.70),
            allow_stretch=True,
            keep_ratio=True
        )

        controls = BoxLayout(size_hint=(1, 0.30), orientation="vertical", padding=5, spacing=5)

        # D-PAD ROW
        dpad = BoxLayout(size_hint=(1, 0.4))
        self.btn_left = Button(text="LEFT")
        self.btn_up = Button(text="UP")
        self.btn_down = Button(text="DOWN")
        self.btn_right = Button(text="RIGHT")
        dpad.add_widget(self.btn_left)
        dpad.add_widget(self.btn_up)
        dpad.add_widget(self.btn_down)
        dpad.add_widget(self.btn_right)

        # ACTION BUTTONS ROW
        ab = BoxLayout(size_hint=(1, 0.3))
        self.btn_b = Button(text="B")
        self.btn_a = Button(text="A")
        ab.add_widget(self.btn_b)
        ab.add_widget(self.btn_a)

        # SYSTEM BUTTONS ROW
        sys_row = BoxLayout(size_hint=(1, 0.3))
        self.btn_select = Button(text="SELECT")
        self.btn_start = Button(text="START")
        self.btn_exit = Button(text="EXIT TO MENU", background_color=(0.8, 0.2, 0.2, 1))
        sys_row.add_widget(self.btn_select)
        sys_row.add_widget(self.btn_start)
        sys_row.add_widget(self.btn_exit)

        controls.add_widget(dpad)
        controls.add_widget(ab)
        controls.add_widget(sys_row)

        self.add_widget(self.screen)
        self.add_widget(controls)

    # ================= INPUT BINDINGS =================
    def bind_inputs(self):
        def set_button(index, is_pressed):
            self.joypad_state[index] = is_pressed

        def bind(btn, index):
            btn.bind(on_press=lambda x: set_button(index, True))
            btn.bind(on_release=lambda x: set_button(index, False))

        bind(self.btn_a, 0)
        bind(self.btn_b, 1)
        bind(self.btn_select, 2)
        bind(self.btn_start, 3)
        bind(self.btn_up, 4)
        bind(self.btn_down, 5)
        bind(self.btn_left, 6)
        bind(self.btn_right, 7)

        self.btn_exit.bind(on_press=self.exit_to_menu)

    # ================= NAVIGATION & FILE SYSTEM =================
    def open_picker(self, *_):
        picker = FileChooserIconView(filters=["*.nes"])
        pop = Popup(title="Select NES ROM", content=picker, size_hint=(0.9, 0.9))

        def sel(_, s, __):
            if s:
                pop.dismiss()
                self.start_rom(s[0])

        picker.bind(on_submit=sel)
        pop.open()

    def open_library(self, *_):
        box = BoxLayout(orientation="vertical", padding=10, spacing=5)
        found = []

        for folder in self.rom_folders:
            if os.path.isdir(folder):
                for f in os.listdir(folder):
                    if f.lower().endswith(".nes"):
                        found.append(os.path.join(folder, f))

        if not found:
            box.add_widget(Label(text="No NES ROMs found inside designated folders"))
        else:
            for rom in found:
                btn = Button(text=os.path.basename(rom), size_hint_y=None, height=50)
                btn.bind(on_press=lambda x, r=rom: self.start_rom(r))
                box.add_widget(btn)

        Popup(title="NES ROM Library", content=box, size_hint=(0.9, 0.9)).open()

    def open_settings(self, *_):
        box = BoxLayout(orientation="vertical", padding=10, spacing=10)

        def add_folder(_):
            picker = FileChooserIconView(dirselect=True)
            inner = BoxLayout(orientation="vertical")
            label = Label(text=f"Viewing: {picker.path}", size_hint_y=0.2)

            picker.bind(path=lambda instance, value: setattr(label, 'text', f"Viewing: {value}"))

            def use_folder(_):
                path = picker.path
                if path and path not in self.rom_folders:
                    self.rom_folders.append(path)
                    self.settings["rom_folders"] = self.rom_folders
                    self.save_settings()
                pop.dismiss()

            btn_use = Button(text="Choose Current Directory", size_hint_y=0.2)
            btn_use.bind(on_press=use_folder)

            inner.add_widget(picker)
            inner.add_widget(label)
            inner.add_widget(btn_use)

            pop = Popup(title="Add Search Directory Target", content=inner, size_hint=(0.95, 0.95))
            pop.open()

        box.add_widget(Button(text="Add ROM Folder Path", on_press=add_folder))
        Popup(title="LOSnes Settings Configuration", content=box, size_hint=(0.85, 0.85)).open()

    # ================= RUN CORE EMULATOR ENGINE =================
    def start_rom(self, rom_path):
        self.rom = os.path.abspath(rom_path)
        self.build_game_ui()

        if self.clock:
            self.clock.cancel()

        try:
            self.env = NESEnv(self.rom)
            state, info = self.env.reset()
            
            # Start with a safe 0 action number
            for _ in range(5):
                self.env.step(0)
                
            self.bind_inputs()
            self.clock = Clock.schedule_interval(self.update, 1 / 60.0988)
        except Exception as e:
            self.clear_widgets()
            self.add_widget(Label(text=f"Failed to load NES Core:\n{e}"))

    # ================= ENGINE TICK AND FRAME RENDER =================
    def update(self, dt):
        if not self.env:
            return

        try:
            speed = int(self.settings.get("speed", 1))
        except:
            speed = 1
            
        state = None

        # FIX: Compress the 8 boolean button states into a single raw integer number.
        # This converts our tracked state into an 8-bit standard controller bitmask (0-255).
        action_number = 0
        for i, pressed in enumerate(self.joypad_state):
            if pressed:
                action_number |= (1 << i)

        for _ in range(speed):
            # Send the clean primitive integer number down to the C++ core
            step_result = self.env.step(action_number)
            state = step_result[0] 
            
            if len(step_result) >= 4 and step_result[2]:  # Check 'done'
                self.env.reset()

        if state is None:
            return

        frame = np.copy(state[::-1, :, :])

        tex = Texture.create(
            size=(frame.shape[1], frame.shape[0]),
            colorfmt="rgb"
        )
        tex.blit_buffer(frame.tobytes(), colorfmt="rgb", bufferfmt="ubyte")
        self.screen.texture = tex

    def exit_to_menu(self, *_):
        if self.clock:
            self.clock.cancel()
        if self.env:
            self.env.close()
            self.env = None
        self.build_menu()


def run(api, memory, save_fn, load_fn):
    return LOSnes(api, memory, save_fn, load_fn)

APP_NAME = "LOSnes"
APP_ICON = "🕹"
