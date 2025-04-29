# File: desktop_app.py

import sys
import requests
from PyQt5.QtWidgets import (QApplication, QLabel, QPushButton, QVBoxLayout, QWidget, QLineEdit, QHBoxLayout)
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import QTimer

# Server endpoint for getting the count
data_url = "http://192.168.254.162:5000/data"  # Adjust this if needed

class PeopleCounterApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.max_capacity = 200  # Default, adjustable

    def init_ui(self):
        self.setWindowTitle("PaghiUsA Hall App - by LE SERRASPBERRY PI")
        
        # Title
        self.title_label = QLabel("PaghiUsA Hall Capacity Monitor")
        self.title_label.setFont(QFont('Arial', 24))

        # Live count label
        self.count_label = QLabel("People inside: 0")
        self.count_label.setFont(QFont('Arial', 20))

        # Status label
        self.status_label = QLabel("Status: Safe")
        self.status_label.setFont(QFont('Arial', 16))

        # Reset Button
        self.reset_button = QPushButton("Reset Count")
        self.reset_button.clicked.connect(self.reset_count)

        # Settings input
        self.max_label = QLabel("Set Maximum Capacity:")
        self.max_input = QLineEdit()
        self.max_input.setPlaceholderText("Enter max capacity...")
        self.max_input.returnPressed.connect(self.update_max_capacity)

        # Layouts
        layout = QVBoxLayout()
        layout.addWidget(self.title_label)
        layout.addWidget(self.count_label)
        layout.addWidget(self.status_label)

        hlayout = QHBoxLayout()
        hlayout.addWidget(self.max_label)
        hlayout.addWidget(self.max_input)
        layout.addLayout(hlayout)

        layout.addWidget(self.reset_button)

        self.setLayout(layout)

        # Timer for refreshing
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_count)
        self.timer.start(1000)  # Update every second

        self.resize(500, 300)
        self.show()

    def update_count(self):
        try:
            response = requests.get(data_url)
            if response.status_code == 200:
                data = response.json()
                people_count = data.get('count', 0)
                temperature = data.get('temperature', 0)
                humidity = data.get('humidity', 0)

                self.count_label.setText(f"People inside: {people_count}")

                # Update Status color
                if people_count < self.max_capacity * 0.8:
                    self.status_label.setText("Status: Safe")
                    self.status_label.setStyleSheet("color: green")
                elif people_count < self.max_capacity:
                    self.status_label.setText("Status: Warning")
                    self.status_label.setStyleSheet("color: orange")
                else:
                    self.status_label.setText("Status: Over Capacity!")
                    self.status_label.setStyleSheet("color: red")

        except Exception as e:
            print(f"Error fetching data: {e}")

    def reset_count(self):
        try:
            requests.post(f"{data_url}/reset")
        except Exception as e:
            print(f"Error resetting count: {e}")

    def update_max_capacity(self):
        try:
            new_max = int(self.max_input.text())
            if new_max > 0:
                self.max_capacity = new_max
                print(f"Max capacity updated to {self.max_capacity}")
        except ValueError:
            print("Invalid maximum capacity.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PeopleCounterApp()
    sys.exit(app.exec_())
