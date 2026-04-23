APP_NAME = "Tap Miner"
APP_ICON = "⛏️"

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock


def run(os_api, state, save, load):

    # ---------------- STATE ----------------
    coins = load("coins")
    if coins is None:
        coins = 0

    layout = BoxLayout(orientation="vertical")

    label = Label(text=f"⛏️ Tap Miner\nCoins: {coins}", font_size=28)
    layout.add_widget(label)

    # ---------------- GAME ACTION ----------------
    def mine(instance):
        nonlocal coins
        coins += 1
        save("coins", coins)
        label.text = f"⛏️ Tap Miner\nCoins: {coins}"

    # ---------------- BUTTON ----------------
    btn = Button(text="TAP TO MINE", font_size=32)
    btn.bind(on_press=mine)
    layout.add_widget(btn)

    # ---------------- AUTO INCOME ----------------
    def passive(dt):
        nonlocal coins
        coins += 1
        save("coins", coins)
        label.text = f"⛏️ Tap Miner\nCoins: {coins}"

    Clock.schedule_interval(passive, 3)

    return layout