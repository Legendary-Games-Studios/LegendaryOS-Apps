import os
import json
import threading
import queue
import time
import numpy as np

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
        
        # Audio streaming communication pipeline
        self.audio_queue = queue.Queue(maxsize=100)
        self.audio_thread = None
        self.audio_running = False

        # DIAGNOSTIC: Track real delta times to measure host frame variance
        self.last_time = 0.0

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
                on_press=lambda x: self.pyboy.send_input(press) if self.pyboy else None,
                on_release=lambda x: self.pyboy.send_input(release) if self.pyboy else None
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

        self.audio_running = False
        if self.audio_thread and self.audio_thread.is_alive():
            self.audio_thread.join()

        self.pyboy = PyBoy(
            rom_path, 
            window_type="headless", 
            sound_emulated=True
        )

        # Force internal PyBoy emulation speed rule to match actual 1x execution limits
        try:
            self.pyboy.set_emulation_speed(1)
        except AttributeError:
            pass

        for _ in range(10):
            self.pyboy.tick()

        self.bind_inputs()

        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break

        self.audio_running = True
        self.audio_thread = threading.Thread(target=self._bg_audio_loop, daemon=True)
        self.audio_thread.start()

        # Initialize tracking clock step right before scheduling the update loop
        self.last_time = time.time()
        
        # Use precise Game Boy hardware timing frame rate rule (approx 59.73 Hz)
        self.clock = Clock.schedule_interval(self.update, 1 / 59.7275)

    # ================= BACKGROUND AUDIO THREAD =================
    def _bg_audio_loop(self):
        try:
            import pygame
            target_freq = 44100
            if self.pyboy and hasattr(self.pyboy.sound, 'sample_rate'):
                target_freq = self.pyboy.sound.sample_rate

            pygame.mixer.init(frequency=target_freq, size=-16, channels=2, buffer=2048)
            channel = pygame.mixer.Channel(0)
        except Exception:
            return

        byte_accumulator = bytearray()
        BLOCK_SIZE = 4096 

        while self.audio_running:
            try:
                raw_bytes = self.audio_queue.get(timeout=0.1)
                if raw_bytes:
                    byte_accumulator.extend(raw_bytes)
                
                while len(byte_accumulator) >= BLOCK_SIZE:
                    play_chunk = bytes(byte_accumulator[:BLOCK_SIZE])
                    del byte_accumulator[:BLOCK_SIZE]
                    
                    sound_obj = pygame.mixer.Sound(buffer=play_chunk)
                    
                    if not channel.get_queue():
                        channel.queue(sound_obj)
                    else:
                        time.sleep(0.002)
                        
            except queue.Empty:
                continue
            except Exception:
                pass

    # ================= RENDER LOOP =================
    def update(self, dt):
        if not self.pyboy:
            return

        # DIAGNOSTIC: Calculate actual, raw loop execution speeds
        now = time.time()
        dt_real = now - self.last_time
        self.last_time = now
        if dt_real > 0:
            print("FPS:", 1.0 / dt_real)

        speed = self.settings.get("speed", 1)

        for _ in range(speed):
            # FIX: Execute tick with frame boundary constraints if supported by core build
            self.pyboy.tick()

            if self.audio_running:
                try:
                    raw_sound = self.pyboy.sound.ndarray
                    if raw_sound is not None and raw_sound.size > 0:
                        converted_bytes = (raw_sound.astype(np.int16) * 256).tobytes()
                        if not self.audio_queue.full():
                            self.audio_queue.put_nowait(converted_bytes)
                except Exception:
                    pass

        frame = self.pyboy.screen.ndarray
        if frame is None:
            return

        if frame.shape[2] == 4:
            frame = frame[:, :, :3]

        frame = frame[::-1, :, :]

        tex = Texture.create(
            size=(frame.shape[1], frame.shape[0]),
            colorfmt="rgb"
        )

        tex.blit_buffer(frame.tobytes(), colorfmt="rgb", bufferfmt="ubyte")
        self.screen.texture = tex


# ================= ENTRY =================
def run(api, memory, save_fn, load_fn):
    return LOSboy(api, memory, save_fn, load_fn)


APP_NAME = "LOSboy"
APP_ICON = "🎮"
