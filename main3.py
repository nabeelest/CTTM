import sys

from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import (QApplication, QDialog, QGridLayout, QHBoxLayout,
                             QLineEdit, QMainWindow, QPushButton, QVBoxLayout,
                             QWidget)


class VirtualKeyboard(QDialog):
    def __init__(self, input_field, main_window):
        super().__init__()
        self.input_field = input_field
        self.main_window = main_window
        # Flag to check if Caps Lock is on (start with uppercase)
        self.is_caps = True
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Virtual Keyboard")
        self.setGeometry(100, 100, 400, 300)

        # Main layout for the dialog
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Define the keyboard layout (below the close button)
        self.keyboard_layout = QGridLayout()
        main_layout.addLayout(self.keyboard_layout)

        self.create_keys()

    def create_keys(self):
        # Clear layout if necessary (for toggling between cases)
        while self.keyboard_layout.count():
            child = self.keyboard_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Define the keys, initially in uppercase
        keys = [
            '1', '2', '3', '4', '5', '6', '7', '8', '9', '0',
            'Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P',
            'A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L',
            'Z', 'X', 'C', 'V', 'B', 'N', 'M', '<-', 'Space',
        ]

        if not self.is_caps:
            keys = [key.lower() if key.isalpha() else key for key in keys]

        row = 0
        col = 0
        for key in keys:
            button = QPushButton(key)
            button.clicked.connect(lambda _, k=key: self.key_clicked(k))
            self.keyboard_layout.addWidget(button, row, col)

            col += 1
            if col > 9:
                col = 0
                row += 1

        # Add Caps Lock button
        caps_button = QPushButton("Caps Lock")
        caps_button.clicked.connect(self.toggle_caps_lock)
        self.keyboard_layout.addWidget(caps_button, row, col)

    def toggle_caps_lock(self):
        # Toggle Caps Lock state
        self.is_caps = not self.is_caps
        self.create_keys()  # Recreate the keyboard with the updated case

    def key_clicked(self, key):
        if key == '<-':
            current_text = self.input_field.text()
            self.input_field.setText(current_text[:-1])
        elif key == 'Space':
            self.input_field.insert(' ')
        elif key == 'Enter':
            # Close the keyboard window and disable reopening until manually
            # refocused
            self.close_keyboard()
        else:
            self.input_field.insert(key)

    def close_keyboard(self):
        # Close the keyboard unconditionally
        self.main_window.keyboard_open = False  # Reset flag on close
        self.close()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Main Window with Virtual Keyboard")
        self.setGeometry(100, 100, 400, 200)

        # Create an input field
        self.input_field = QLineEdit(self)
        self.input_field.setPlaceholderText("Click to type...")

        # Create the layout
        layout = QVBoxLayout()
        layout.addWidget(self.input_field)

        # Central widget
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Flag to track if the keyboard is open
        self.keyboard_open = False

        # Connect focus event to show virtual keyboard
        self.input_field.focusInEvent = self.show_virtual_keyboard

    def show_virtual_keyboard(self, event):
        if not self.keyboard_open:
            self.keyboard = VirtualKeyboard(self.input_field, self)
            self.keyboard.show()
            self.keyboard_open = True  # Set flag when the keyboard opens
            # Connect to track when the keyboard is closed
            self.keyboard.finished.connect(self.on_keyboard_closed)
        QLineEdit.focusInEvent(self.input_field, event)

    def on_keyboard_closed(self):
        self.keyboard_open = False  # Reset the flag when keyboard is closed


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
