APP_NAME = "Tap Miner"
APP_ICON = "⛏️"

import os
import json
import random
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.uix.popup import Popup


SAVE_PATH = "LegendaryOS/root/user-apps/AppData/TapMiner/save.json"


def load_save():
    try:
        os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)

        if not os.path.exists(SAVE_PATH):
            data = {
                "coins": 0,
                "pickaxe": 1,
                "auto": 0,
                "rebirths": 0
            }
            save_game(data)
            return data

        with open(SAVE_PATH, "r") as f:
            return json.load(f)

    except:
        return {
            "coins": 0,
            "pickaxe": 1,
            "auto": 0,
            "rebirths": 0
        }


def save_game(data):
    try:
        os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)
        with open(SAVE_PATH, "w") as f:
            json.dump(data, f, indent=4)
    except:
        pass


def run(os_api, state, save, load):

    data = load_save()

    coins = data["coins"]
    pickaxe = data["pickaxe"]
    auto = data["auto"]
    rebirths = data["rebirths"]

    layout = BoxLayout(orientation="vertical", spacing=10, padding=10)
    label = Label(font_size=28)

    # ---------------- CALCULATIONS ----------------
    def multiplier():
        return 1 + rebirths * 0.5

    def pickaxe_cost():
        return pickaxe * 10

    def auto_cost():
        return (auto + 1) * 25

    def rebirth_cost():
        return 1000 * (rebirths + 1)

    # ---------------- SAVE ----------------
    def commit():
        data["coins"] = coins
        data["pickaxe"] = pickaxe
        data["auto"] = auto
        data["rebirths"] = rebirths
        save_game(data)

    # ---------------- UI REFRESH ----------------
    def refresh():
        label.text = (
            f"⛏ Tap Miner\n"
            f"Coins: {coins}\n"
            f"Pickaxe Lv: {pickaxe}\n"
            f"Auto Lv: {auto}\n"
            f"Rebirths: {rebirths}"
        )

        # update shop button texts if they exist
        if hasattr(layout, "btn_pickaxe"):
            layout.btn_pickaxe.text = f"⛏ Upgrade Pickaxe ({pickaxe_cost()})"

        if hasattr(layout, "btn_auto"):
            layout.btn_auto.text = f"🤖 Upgrade Auto ({auto_cost()})"

        if hasattr(layout, "btn_rebirth"):
            layout.btn_rebirth.text = f"🔁 Rebirth ({rebirth_cost()})"

    # ---------------- ACTIONS ----------------
    def mine(instance):
        nonlocal coins
        gain = (pickaxe + random.randint(0, pickaxe)) * multiplier()

        if random.random() < 0.1:
            gain *= 3

        coins += int(gain)
        commit()
        refresh()

    def manual_save(instance):
        commit()
        os_api.notify("💾 Saved!")

    # ---------------- SHOP ----------------
    def open_shop(instance):

        shop = BoxLayout(orientation="vertical", spacing=10, padding=10)
        shop_label = Label(text="🛒 Shop", font_size=24)
        shop.add_widget(shop_label)

        # PICKAXE
        def buy_pickaxe(btn):
            nonlocal coins, pickaxe
            cost = pickaxe_cost()

            if coins >= cost:
                coins -= cost
                pickaxe += 1
                commit()
                refresh()

        layout.btn_pickaxe = Button()
        layout.btn_pickaxe.bind(on_press=buy_pickaxe)
        shop.add_widget(layout.btn_pickaxe)

        # AUTO
        def buy_auto(btn):
            nonlocal coins, auto
            cost = auto_cost()

            if coins >= cost:
                coins -= cost
                auto += 1
                commit()
                refresh()

        layout.btn_auto = Button()
        layout.btn_auto.bind(on_press=buy_auto)
        shop.add_widget(layout.btn_auto)

        # REBIRTH
        def rebirth(btn):
            nonlocal coins, pickaxe, auto, rebirths
            cost = rebirth_cost()

            if coins >= cost:
                rebirths += 1
                coins = 0
                pickaxe = 1
                auto = 0
                commit()
                refresh()

        layout.btn_rebirth = Button()
        layout.btn_rebirth.bind(on_press=rebirth)
        shop.add_widget(layout.btn_rebirth)

        Popup(title="Shop", content=shop, size_hint=(0.8, 0.7)).open()

        refresh()

    # ---------------- PASSIVE ----------------
    def passive(dt):
        nonlocal coins
        coins += auto * multiplier()
        commit()
        refresh()

    # ---------------- UI ----------------
    btn_mine = Button(text="⛏ MINE")
    btn_mine.bind(on_press=mine)

    btn_shop = Button(text="🛒 SHOP")
    btn_shop.bind(on_press=open_shop)

    btn_save = Button(text="💾 SAVE")
    btn_save.bind(on_press=manual_save)

    layout.add_widget(label)
    layout.add_widget(btn_mine)
    layout.add_widget(btn_shop)
    layout.add_widget(btn_save)

    Clock.schedule_interval(passive, 2)
    refresh()

    return layout