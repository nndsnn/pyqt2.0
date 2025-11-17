import sys
import json
import os
from datetime import datetime, date
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QCheckBox, QMessageBox, QFrame, QLineEdit,
    QTextEdit, QDateEdit, QScrollArea, QDialog, QComboBox
)
from PyQt6.QtCore import Qt, QDate


class TaskDialog(QDialog):
    """Диалог добавления задачи"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Новая задача")
        self.setFixedSize(400, 300)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Название
        layout.addWidget(QLabel("Название:"))
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Введите название задачи...")
        layout.addWidget(self.title_input)

        # Описание
        layout.addWidget(QLabel("Описание:"))
        self.desc_input = QTextEdit()
        self.desc_input.setMaximumHeight(60)
        self.desc_input.setPlaceholderText("Необязательное описание...")
        layout.addWidget(self.desc_input)

        # Дедлайн
        deadline_layout = QHBoxLayout()
        deadline_layout.addWidget(QLabel("Дедлайн:"))
        self.deadline_date = QDateEdit()
        self.deadline_date.setDate(QDate.currentDate().addDays(1))
        deadline_layout.addWidget(self.deadline_date)
        deadline_layout.addStretch()
        layout.addLayout(deadline_layout)

        # Кнопки
        button_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("Отмена")
        self.save_btn = QPushButton("Сохранить")
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.save_btn)
        layout.addLayout(button_layout)

        # Подключения
        self.cancel_btn.clicked.connect(self.reject)
        self.save_btn.clicked.connect(self.save_task)

    def save_task(self):
        if not self.title_input.text().strip():
            QMessageBox.warning(self, "Ошибка", "Введите название задачи!")
            return
        self.accept()

    def get_task_data(self):
        deadline = datetime(
            self.deadline_date.date().year(),
            self.deadline_date.date().month(),
            self.deadline_date.date().day(),
            23, 59  # Конец дня
        )

        return {
            'id': datetime.now().timestamp(),
            'title': self.title_input.text().strip(),
            'description': self.desc_input.toPlainText().strip(),
            'deadline': deadline.isoformat(),
            'created_date': datetime.now().isoformat(),
            'is_completed': False
        }


class TaskCard(QFrame):
    """Карточка задачи"""

    def __init__(self, task_data, update_callback):
        super().__init__()
        self.task_data = task_data
        self.update_callback = update_callback
        self.setup_ui()

    def setup_ui(self):
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Верхняя строка
        top_layout = QHBoxLayout()
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.task_data['is_completed'])
        self.checkbox.stateChanged.connect(self.toggle_complete)

        self.title_label = QLabel(self.task_data['title'])
        self.title_label.setStyleSheet("font-size: 14px;")

        top_layout.addWidget(self.checkbox)
        top_layout.addWidget(self.title_label)
        top_layout.addStretch()
        layout.addLayout(top_layout)

        # Описание
        if self.task_data['description']:
            desc_label = QLabel(self.task_data['description'])
            desc_label.setStyleSheet("color: #666; font-size: 12px;")
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)

        # Нижняя строка
        bottom_layout = QHBoxLayout()

        # Дедлайн
        deadline = datetime.fromisoformat(self.task_data['deadline'])
        days_left = (deadline.date() - date.today()).days

        if days_left < 0:
            time_text = "Просрочено"
            time_style = "color: #e74c3c; font-size: 11px;"
        elif days_left == 0:
            time_text = "Сегодня"
            time_style = "color: #f39c12; font-size: 11px;"
        elif days_left == 1:
            time_text = "Завтра"
            time_style = "color: #f39c12; font-size: 11px;"
        else:
            time_text = f"Осталось {days_left} дней"
            time_style = "color: #7f8c8d; font-size: 11px;"

        deadline_label = QLabel(time_text)
        deadline_label.setStyleSheet(time_style)
        bottom_layout.addWidget(deadline_label)

        bottom_layout.addStretch()

        # Кнопка удаления
        delete_btn = QPushButton("×")
        delete_btn.setFixedSize(30, 30)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #fee2e2;
                color: #dc2626;
                border: none;
                border-radius: 4px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #fecaca;
            }
        """)
        delete_btn.clicked.connect(self.delete_task)
        bottom_layout.addWidget(delete_btn)

        layout.addLayout(bottom_layout)
        self.update_style()

    def toggle_complete(self):
        self.task_data['is_completed'] = self.checkbox.isChecked()
        self.update_style()
        self.update_callback()

    def delete_task(self):
        reply = QMessageBox.question(
            self, "Удаление",
            f"Удалить '{self.task_data['title']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.update_callback(delete_id=self.task_data['id'])

    def update_style(self):
        if self.task_data['is_completed']:
            self.setStyleSheet("""
                QFrame {
                    background-color: #f8f9fa;
                    border: 1px solid #e9ecef;
                    border-radius: 8px;
                    padding: 12px;
                    margin: 4px;
                }
            """)
            self.title_label.setStyleSheet("""
                color: #95a5a6;
                text-decoration: line-through;
                font-size: 14px;
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border: 1px solid #e9ecef;
                    border-radius: 8px;
                    padding: 12px;
                    margin: 4px;
                }
            """)
            self.title_label.setStyleSheet("""
                color: #2c3e50;
                font-size: 14px;
            """)


class SimpleTaskManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.tasks = []
        self.data_file = 'tasks.json'
        self.load_tasks()
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Менеджер задач")
        self.setGeometry(100, 100, 500, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Заголовок
        title_label = QLabel("Задачи")
        title_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Панель управления
        control_layout = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск...")
        self.search_input.textChanged.connect(self.filter_tasks)

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Все", "Активные", "Выполненные"])
        self.filter_combo.currentTextChanged.connect(self.filter_tasks)

        self.add_btn = QPushButton("+ Новая")
        self.add_btn.clicked.connect(self.add_task)

        control_layout.addWidget(self.search_input)
        control_layout.addWidget(self.filter_combo)
        control_layout.addWidget(self.add_btn)
        layout.addLayout(control_layout)

        # Область задач
        self.scroll_area = QScrollArea()
        self.scroll_widget = QWidget()
        self.tasks_layout = QVBoxLayout(self.scroll_widget)
        self.tasks_layout.setSpacing(8)
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)
        layout.addWidget(self.scroll_area)

        # Статистика
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("""
            color: #7f8c8d;
            font-size: 12px;
        """)
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.stats_label)

        self.apply_styles()
        self.filter_tasks()

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ecf0f1;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                font-size: 14px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QComboBox {
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                background-color: white;
                font-size: 14px;
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
            QCheckBox {
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #bdc3c7;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #27ae60;
                border-color: #27ae60;
            }
        """)

    def load_tasks(self):
        """Загрузка задач из файла"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.tasks = json.load(f)
            except Exception as e:
                print(f"Ошибка загрузки задач: {e}")
                self.tasks = []

    def save_tasks(self):
        """Сохранение задач в файл"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.tasks, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения: {e}")

    def add_task(self):
        """Добавление новой задачи"""
        dialog = TaskDialog(self)
        if dialog.exec():
            task_data = dialog.get_task_data()
            self.tasks.append(task_data)
            self.save_tasks()
            self.filter_tasks()

    def filter_tasks(self):
        """Фильтрация и отображение задач"""
        # Очистка
        while self.tasks_layout.count():
            child = self.tasks_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        search_text = self.search_input.text().lower()
        filter_type = self.filter_combo.currentText()

        filtered_tasks = []
        for task in self.tasks:
            # Поиск
            if search_text and search_text not in task['title'].lower():
                continue

            # Фильтрация по статусу
            if filter_type == "Активные" and task['is_completed']:
                continue
            elif filter_type == "Выполненные" and not task['is_completed']:
                continue

            filtered_tasks.append(task)

        # Сортировка по дате создания (новые сверху)
        filtered_tasks.sort(key=lambda x: x['created_date'], reverse=True)

        # Отображение
        if not filtered_tasks:
            label = QLabel("Задачи не найдены")
            label.setStyleSheet("""
                font-size: 16px;
                color: #bdc3c7;
                text-align: center;
                padding: 40px;
            """)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tasks_layout.addWidget(label)
        else:
            for task in filtered_tasks:
                task_card = TaskCard(task, self.update_tasks)
                self.tasks_layout.addWidget(task_card)

        self.update_stats()

    def update_tasks(self, delete_id=None):
        """Обновление списка задач"""
        if delete_id is not None:
            self.tasks = [t for t in self.tasks if t['id'] != delete_id]
            self.save_tasks()
        self.filter_tasks()

    def update_stats(self):
        """Обновление статистики"""
        total = len(self.tasks)
        completed = len([t for t in self.tasks if t['is_completed']])
        active = total - completed
        stats_text = f"Всего: {total} | Актив.: {active} | Выпол.: {completed}"
        self.stats_label.setText(stats_text)

    def closeEvent(self, event):
        """Сохранение при закрытии"""
        self.save_tasks()
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = SimpleTaskManager()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
