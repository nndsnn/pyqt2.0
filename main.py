import sys
import sqlite3
from datetime import datetime, date
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QCheckBox, QMessageBox, QFrame, QLineEdit,
    QTextEdit, QDateEdit, QScrollArea, QDialog, QComboBox
)
from PyQt6.QtCore import Qt, QDate


class Database:
    def __init__(self, db_file='task_todo.db'):
        self.db_file = db_file
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                title        TEXT    NOT NULL,
                description  TEXT,
                deadline     TEXT    NOT NULL,
                created_date TEXT    NOT NULL,
                is_completed BOOLEAN NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

    def get_all_tasks(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM tasks')
        tasks = []
        for row in cursor.fetchall():
            tasks.append({
                'id': row[0],
                'title': row[1],
                'description': row[2],
                'deadline': row[3],
                'created_date': row[4],
                'is_completed': bool(row[5])
            })
        conn.close()
        return tasks

    def add_task(self, task_data):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO tasks (title, description, deadline, created_date, is_completed)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            task_data['title'],
            task_data['description'],
            task_data['deadline'],
            task_data['created_date'],
            task_data['is_completed']
        ))
        conn.commit()
        conn.close()

    def update_task(self, task_data):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE tasks
            SET title=?, description=?, deadline=?, created_date=?, is_completed=?
            WHERE id=?
        ''', (
            task_data['title'],
            task_data['description'],
            task_data['deadline'],
            task_data['created_date'],
            task_data['is_completed'],
            task_data['id']
        ))
        conn.commit()
        conn.close()

    def delete_task(self, task_id):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM tasks WHERE id=?', (task_id,))
        conn.commit()
        conn.close()


class TaskDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Новая задача")
        self.setFixedSize(400, 300)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        layout.addWidget(QLabel("Название:"))
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Введите название задачи...")
        layout.addWidget(self.title_input)

        layout.addWidget(QLabel("Описание:"))
        self.desc_input = QTextEdit()
        self.desc_input.setMaximumHeight(60)
        self.desc_input.setPlaceholderText("Необязательное описание...")
        layout.addWidget(self.desc_input)

        deadline_layout = QHBoxLayout()
        deadline_layout.addWidget(QLabel("Дедлайн:"))
        self.deadline_date = QDateEdit()
        self.deadline_date.setDate(QDate.currentDate().addDays(1))
        deadline_layout.addWidget(self.deadline_date)
        deadline_layout.addStretch()
        layout.addLayout(deadline_layout)

        button_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("Отмена")
        self.save_btn = QPushButton("Сохранить")
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.save_btn)
        layout.addLayout(button_layout)

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
            23, 59
        )

        return {
            'title': self.title_input.text().strip(),
            'description': self.desc_input.toPlainText().strip(),
            'deadline': deadline.isoformat(),
            'created_date': datetime.now().isoformat(),
            'is_completed': False
        }


class TaskCard(QFrame):
    def __init__(self, task_data, update_callback, db):
        super().__init__()
        self.task_data = task_data
        self.update_callback = update_callback
        self.db = db
        self.setup_ui()

    def setup_ui(self):
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

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

        if self.task_data['description']:
            desc_label = QLabel(self.task_data['description'])
            desc_label.setStyleSheet("color: #666; font-size: 12px;")
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)

        bottom_layout = QHBoxLayout()

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
        self.db.update_task(self.task_data)
        self.update_style()
        self.update_callback()

    def delete_task(self):
        reply = QMessageBox.question(
            self, "Удаление",
            f"Удалить '{self.task_data['title']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_task(self.task_data['id'])
            self.update_callback()

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
        self.db = Database('task_todo.db')  # Подключение к вашей БД
        self.tasks = []
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

        title_label = QLabel("Задачи")
        title_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

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

        self.scroll_area = QScrollArea()
        self.scroll_widget = QWidget()
        self.tasks_layout = QVBoxLayout(self.scroll_widget)
        self.tasks_layout.setSpacing(8)
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)
        layout.addWidget(self.scroll_area)

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
        self.tasks = self.db.get_all_tasks()

    def add_task(self):
        dialog = TaskDialog(self)
        if dialog.exec():
            task_data = dialog.get_task_data()
            self.db.add_task(task_data)
            self.load_tasks()
            self.filter_tasks()

    def filter_tasks(self):
        while self.tasks_layout.count():
            child = self.tasks_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        search_text = self.search_input.text().lower()
        filter_type = self.filter_combo.currentText()

        filtered_tasks = []
        for task in self.tasks:
            if search_text and search_text not in task['title'].lower():
                continue

            if filter_type == "Активные" and task['is_completed']:
                continue
            elif filter_type == "Выполненные" and not task['is_completed']:
                continue

            filtered_tasks.append(task)

        filtered_tasks.sort(key=lambda x: x['created_date'], reverse=True)

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
                task_card = TaskCard(task, self.filter_tasks, self.db)
                self.tasks_layout.addWidget(task_card)

        self.update_stats()

    def update_stats(self):
        total = len(self.tasks)
        completed = len([t for t in self.tasks if t['is_completed']])
        active = total - completed
        stats_text = f"Всего: {total} | Актив: {active} | Выпол: {completed}"
        self.stats_label.setText(stats_text)


def main():
    app = QApplication(sys.argv)
    window = SimpleTaskManager()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
