import kivy
kivy.require('2.3.0')
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.properties import StringProperty, NumericProperty, DictProperty, ListProperty
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.animation import Animation
import random
import itertools

Builder.load_string("""
<SlotCell>:
    font_size: '24sp'
    background_normal: ''
    background_color: (0.8, 0.8, 0.8, 1)
    color: (1, 0, 0, 1) if self.text == '7' else (0, 0, 0, 1)

<SlotMachineLogic>:
    orientation: 'vertical'
    padding: 10
    spacing: 10
    canvas.before:
        Color:
            rgb: (0.9, 0.9, 0.9, 1)
        Rectangle:
            pos: self.pos
            size: self.size
    
    BoxLayout:
        size_hint_y: None
        height: 40
        Label:
            text: f"Balance: {root.balance}pt"
            color: (0, 0, 0, 1)
        Label:
            text: f"Spins: {root.spins}"
            color: (0, 0, 0, 1)
        Label:
            text: f"Traits: {len(root.owned_traits)}"
            color: (0, 0, 1, 1)

    GridLayout:
        id: grid_layout
        cols: 5
        spacing: 5

    Label:
        text: root.message_text
        size_hint_y: None
        height: 60
        text_size: self.width, None
        halign: 'center'
        color: (0.2, 0.2, 0.8, 1)

    TextInput:
        id: cmd_input
        hint_text: "Type: 's', 'buy', 'shop', or 'buy [TraitName]'"
        multiline: False
        size_hint_y: None
        height: 50

    Button:
        text: "EXECUTE ACTION"
        size_hint_y: None
        height: 70
        on_press: root.process_action()
        background_color: (0.2, 0.7, 0.2, 1)
""")

class SlotCell(Button):
    pass

class SlotMachineLogic(BoxLayout):
    balance = NumericProperty(100)
    spins = NumericProperty(10)
    message_text = StringProperty("Welcome to Freestyle 2026!")
    owned_traits = ListProperty([])
    
    # 2026 Game Data
    game_traits = {
        "Bible": {"cost": 2500, "target": "6", "chance": 1.0, "payout": 0},
        "AI Overlord": {"cost": 5000, "target": "A", "chance": 0.2, "payout": 500},
        "Quantum Spin": {"cost": 8000, "target": "ABCDE7", "chance": 0.1, "payout": 1000},
        "Cyber-Jackpot": {"cost": 15000, "target": "7", "chance": 0.05, "payout": 5000}
    }
    base_values = {'A': 7, 'B': 10, 'C': 10, 'D': 10, 'E': 10, '7': 777, '6': 0}
    weights = {'A': 20, 'B': 20, 'C': 20, 'D': 20, 'E': 20, '7': 2, '6': 10}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.grid_labels = []
        self.shop_items = random.sample(list(self.game_traits.keys()), 3)
        Clock.schedule_once(self.build_grid_ui, 0)

    def build_grid_ui(self, dt):
        grid = self.ids.grid_layout
        grid.clear_widgets()
        self.grid_labels = [SlotCell(text="-") for _ in range(25)]
        for label in self.grid_labels:
            grid.add_widget(label)

    def process_action(self):
        cmd = self.ids.cmd_input.text.strip().lower()
        self.ids.cmd_input.text = ""
        
        if cmd.startswith("buy "):
            trait_name = cmd.replace("buy ", "").title()
            if trait_name in self.game_traits:
                cost = self.game_traits[trait_name]['cost']
                if self.balance >= cost:
                    self.balance -= cost
                    self.owned_traits.append(trait_name)
                    self.message_text = f"✅ Acquired {trait_name}!"
                else: self.message_text = "❌ Insufficient points!"
            return

        if cmd == "buy":
            if self.balance >= 50:
                self.balance -= 50
                self.spins += 5
                self.message_text = "✅ +5 Spins!"
        elif cmd == "shop":
            self.message_text = "SHOP: " + ", ".join([f"{n}({self.game_traits[n]['cost']}pt)" for n in self.shop_items])
        elif cmd in ["s", ""]:
            self.start_spin()

    def start_spin(self):
        if self.spins <= 0:
            self.message_text = "Out of spins! Type 'buy'"
            return
        self.spins -= 1
        for lbl in self.grid_labels: 
            Animation.cancel_all(lbl)
            lbl.background_color = (0.8, 0.8, 0.8, 1)
        
        Clock.schedule_interval(self.animate_reels, 0.05)
        Clock.schedule_once(self.finalize_spin, 1.0)

    def animate_reels(self, dt):
        syms = list(self.weights.keys())
        for lbl in self.grid_labels: lbl.text = random.choice(syms)

    def finalize_spin(self, dt):
        Clock.unschedule(self.animate_reels)
        s_l = list(self.weights.keys())
        w_l = list(self.weights.values())

        if "Bible" in self.owned_traits and '6' in s_l:
            idx = s_l.index('6'); s_l.pop(idx); w_l.pop(idx)

        final_res = []
        for i in range(25):
            char = random.choices(s_l, weights=w_l, k=1)[0] # [0] extracts string
            self.grid_labels[i].text = char
            final_res.append(char)

        grid_2d = [final_res[i*5:(i+1)*5] for i in range(5)]
        win_amount, win_indices = self.calculate_wins(grid_2d)

        for t_name in self.owned_traits:
            t = self.game_traits[t_name]
            if any(c in t['target'] for c in final_res) and random.random() < t['chance']:
                win_amount += t['payout']
                self.message_text = f"🔥 {t_name} TRIGGER: +{t['payout']}pt!"

        if win_amount > 0:
            self.balance += win_amount
            if not self.message_text.startswith("🔥"):
                self.message_text = f"🎉 WIN: {win_amount}pt 🎉"
            self.apply_glow(win_indices)

    def calculate_wins(self, grid_2d):
        total = 0
        indices = set()
        # Row Check
        for r in range(5):
            for char, group in itertools.groupby(grid_2d[r]):
                count = len(list(group))
                if char != '6' and count >= 3:
                    total += self.base_values[char] * (count - 2)
                    for c in range(5): indices.add(r * 5 + c)
        return total, list(indices)

    def apply_glow(self, indices):
        anim = Animation(background_color=(1, 1, 0, 1), duration=0.2) + Animation(background_color=(0.8, 0.8, 0.8, 1), duration=0.2)
        anim.repeat = True
        for i in indices: anim.start(self.grid_labels[i])

class SlotMachineApp(App):
    def build(self): return SlotMachineLogic()

if __name__ == "__main__":
    SlotMachineApp().run()
