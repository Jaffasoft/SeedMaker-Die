from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
import hashlib
import os
from kivy.core.clipboard import Clipboard

# Load BIP-39 wordlist
try:
    if os.path.exists("wordlist.txt"):
        with open("wordlist.txt", "r") as f:
            bip39_words = [line.strip() for line in f.readlines()]
        if len(bip39_words) != 2048:
            raise ValueError("Wordlist must contain exactly 2048 words")
    else:
        raise FileNotFoundError("wordlist.txt not found")
except Exception as e:
    print(f"Error loading wordlist: {e}. Using fallback list.")
    bip39_words = ["abandon", "ability", "able", "about", "above", "absent", "absorb", "abstract"] + ["word"] * 2040

class SeedMakerApp(App):
    def build(self):
        self.bits = [0] * 264  # 256 entropy + 8 checksum bits
        self.word_labels = []
        self.count_labels = []
        self.checksum_buttons = []

        layout = BoxLayout(orientation='vertical', padding=10, spacing=5)

        # Header
        header = BoxLayout(orientation='vertical', size_hint=(1, 0.15), spacing=0)
        title = Label(
            text="[b]SeedMaker[/b]",
            markup=True,
            font_size=30,
            halign="center",
            valign="middle"
        )
        title.bind(size=title.setter('text_size'))
        warning = Label(
            text="WARNING: Do not use this for a real seed in a wallet. Learning only. Use print version for real seed offline.",
            font_size=20,
            halign="center",
            valign="middle"
        )
        warning.bind(size=warning.setter('text_size'))
        header.add_widget(title)
        header.add_widget(warning)

        # Grid: 25 rows (1 for titles), 13 cols (11 bits + Words + Count)
        self.grid = GridLayout(cols=13, rows=25, size_hint=(1, 0.55))
        # Title row
        for col in range(11):
            self.grid.add_widget(Label(text=""))
        self.grid.add_widget(Label(text="Words", font_size=20, halign="left"))
        self.grid.add_widget(Label(text="Count", font_size=20, halign="left"))

        # Data rows
        for row in range(24):
            for col in range(11):
                idx = row * 11 + col
                if idx < 256:  # Entropy bits
                    btn = Button(
                        text="0",
                        on_press=lambda instance, i=idx: self.toggle_bit(instance, i),
                        background_color=[0.5, 0.5, 0.5, 1]
                    )
                    self.grid.add_widget(btn)
                elif idx < 264:  # Checksum bits - Black with white text
                    btn = Button(
                        text="0",
                        on_press=lambda instance, i=idx: self.toggle_checksum_bit(instance, i) if idx < 263 else None,
                        disabled=(idx == 263),
                        background_color=[0, 0, 0, 1],
                        color=[1, 1, 1, 1],
                        disabled_color=[1, 1, 1, 1]
                    )
                    self.grid.add_widget(btn)
                    self.checksum_buttons.append(btn)
            # Word and Count labels
            word_label = Label(text="", font_size=20, halign="left")
            word_label.bind(size=word_label.setter('text_size'))
            self.grid.add_widget(word_label)
            self.word_labels.append(word_label)
            
            count_label = Label(text="", font_size=20, halign="left")
            count_label.bind(size=count_label.setter('text_size'))
            self.grid.add_widget(count_label)
            self.count_labels.append(count_label)

        # Bottom display - 3 sections with gaps
        bottom = BoxLayout(orientation='vertical', size_hint=(1, 0.30), spacing=10)

        # Binary section
        binary_box = BoxLayout(orientation='vertical', size_hint=(1, 0.33))
        binary_title = Label(text="256 Binary Bits:", font_size=20, halign="left", size_hint=(1, 0.25))
        binary_title.bind(size=binary_title.setter('text_size'))
        binary_gap = Label(text="", size_hint=(1, 0.15))  # Gap
        binary_content = BoxLayout(orientation='horizontal', size_hint=(1, 0.60))
        self.binary_label = Label(text="", font_size=20, halign="left", size_hint=(0.9, 1))
        self.binary_label.bind(size=self.binary_label.setter('text_size'))
        binary_copy_btn = Button(text="Copy", size_hint=(0.1, 1), on_press=self.copy_binary)
        binary_content.add_widget(self.binary_label)
        binary_content.add_widget(binary_copy_btn)
        binary_box.add_widget(binary_title)
        binary_box.add_widget(binary_gap)
        binary_box.add_widget(binary_content)

        # 24 Words section
        words_box = BoxLayout(orientation='vertical', size_hint=(1, 0.33))
        words_title = Label(text="BIP39 Mnemonic 24 Word Seed Phrase:", font_size=20, halign="left", size_hint=(1, 0.25))
        words_title.bind(size=words_title.setter('text_size'))
        words_gap = Label(text="", size_hint=(1, 0.15))  # Gap
        words_content = BoxLayout(orientation='horizontal', size_hint=(1, 0.60))
        self.words_label = Label(text="", font_size=20, halign="left", size_hint=(0.9, 1))
        self.words_label.bind(size=self.words_label.setter('text_size'))
        words_copy_btn = Button(text="Copy", size_hint=(0.1, 1), on_press=self.copy_words)
        words_content.add_widget(self.words_label)
        words_content.add_widget(words_copy_btn)
        words_box.add_widget(words_title)
        words_box.add_widget(words_gap)
        words_box.add_widget(words_content)

        # Checksum section
        checksum_box = BoxLayout(orientation='vertical', size_hint=(1, 0.33))
        checksum_title = Label(text="Checksum: ", font_size=20, halign="left", size_hint=(1, 0.25))
        checksum_title.bind(size=checksum_title.setter('text_size'))
        checksum_gap = Label(text="", size_hint=(1, 0.15))  # Gap
        checksum_content = BoxLayout(orientation='vertical', size_hint=(1, 0.60))
        self.checksum_label = Label(text="", font_size=20, halign="left", size_hint=(1, 0.5))
        self.checksum_label.bind(size=self.checksum_label.setter('text_size'))
        self.checksum_word_label = Label(text="", font_size=20, halign="left", size_hint=(1, 0.5))
        self.checksum_word_label.bind(size=self.checksum_word_label.setter('text_size'))
        checksum_content.add_widget(self.checksum_label)
        checksum_content.add_widget(self.checksum_word_label)
        checksum_box.add_widget(checksum_title)
        checksum_box.add_widget(checksum_gap)
        checksum_box.add_widget(checksum_content)

        bottom.add_widget(binary_box)
        bottom.add_widget(words_box)
        bottom.add_widget(checksum_box)

        layout.add_widget(header)
        layout.add_widget(self.grid)
        layout.add_widget(bottom)  # Assuming this was meant to be bottom
        return layout

    def toggle_bit(self, instance, index):
        self.bits[index] = 1 - self.bits[index]
        instance.text = str(self.bits[index])
        self.update_display()

    def toggle_checksum_bit(self, instance, index):
        self.bits[index] = 1 - self.bits[index]
        instance.text = str(self.bits[index])
        self.update_display()

    def update_display(self):
        # Binary display
        entropy = ''.join(str(bit) for bit in self.bits[:256])
        self.binary_label.text = entropy if entropy.count('1') > 0 else ""

        # Calculate checksum
        entropy_bytes = int(entropy, 2).to_bytes(32, byteorder='big')  # 256 bits = 32 bytes
        checksum = hashlib.sha256(entropy_bytes).digest()
        checksum_bits = bin(int.from_bytes(checksum, 'big'))[2:].zfill(256)[:8]  # First 8 bits
        for i, bit in enumerate(checksum_bits):
            self.bits[256 + i] = int(bit)
            self.checksum_buttons[i].text = bit
        self.checksum_label.text = checksum_bits if entropy.count('1') > 0 else ""

        # Full 264-bit sequence for 24 words
        full_bits = entropy + checksum_bits
        words = []
        checksum_word = ""
        if entropy.count('1') > 0:
            for i in range(24):
                start = i * 11
                bits11 = full_bits[start:start+11]
                if len(bits11) == 11:
                    idx = int(bits11, 2)
                    if idx < 2048:
                        word = bip39_words[idx]
                        words.append(word)
                        self.word_labels[i].text = word
                        self.count_labels[i].text = str(idx + 1)  # 1-based index
                        if i == 23:  # 24th word
                            checksum_word = f"Checksum Word: {word}"
            self.words_label.text = ' '.join(words)
            self.checksum_word_label.text = checksum_word
        else:
            for i in range(24):
                self.word_labels[i].text = ""
                self.count_labels[i].text = ""
            self.words_label.text = ""
            self.checksum_word_label.text = ""

    def copy_binary(self, instance):
        binary_str = ''.join(str(bit) for bit in self.bits[:256])
        if binary_str.count('1') > 0:
            Clipboard.copy(binary_str)
            self.binary_label.text = f"{binary_str} (Copied!)"

    def copy_words(self, instance):
        words = [self.word_labels[i].text for i in range(24) if self.word_labels[i].text]
        words_text = ' '.join(words)
        if words_text.strip():
            Clipboard.copy(words_text)
            self.words_label.text = f"{words_text} (Copied!)"

if __name__ == '__main__':
    SeedMakerApp().run()
