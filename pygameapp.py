import json
import os
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tkinter import font as tkfont

class TodoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Todo List с приоритетами и сроками")
        self.root.geometry("1200x700")
        self.data_file = "todo_list.json"
        self.tasks = []
        self.load_tasks()
        self.setup_styles()
        self.create_widgets()
        self.refresh_task_list()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_styles(self):
        """Настройка цветов и стилей"""
        self.colors = {
            'high': '#FF6B6B',      
            'medium': '#FFD93D',    
            'low': '#6BCB77',       
            'completed': '#AAAAAA', 
            'bg': '#2C3E50',        
            'fg': '#ECF0F1',        
            'button': '#3498DB',    
            'button_hover': '#2980B9'
        }
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Custom.Treeview", 
                       background=self.colors['bg'],
                       foreground=self.colors['fg'],
                       fieldbackground=self.colors['bg'],
                       rowheight=30)
        style.map("Custom.Treeview",
                 background=[('selected', '#3498DB')])
        style.configure("Custom.Treeview.Heading",
                       background=self.colors['button'],
                       foreground='white',
                       font=('Arial', 10, 'bold'))
    def create_widgets(self):
        top_frame = tk.Frame(self.root, bg=self.colors['bg'])
        top_frame.pack(fill=tk.X, padx=10, pady=10)
        title_label = tk.Label(top_frame, text="📝 Менеджер задач", 
                               font=('Arial', 24, 'bold'),
                               bg=self.colors['bg'], fg=self.colors['fg'])
        title_label.pack(pady=10)
        add_frame = tk.Frame(top_frame, bg=self.colors['bg'])
        add_frame.pack(fill=tk.X, pady=10)
        tk.Label(add_frame, text="Задача:", bg=self.colors['bg'], 
                fg=self.colors['fg'], font=('Arial', 10)).grid(row=0, column=0, padx=5)
        self.task_entry = tk.Entry(add_frame, width=40, font=('Arial', 10))
        self.task_entry.grid(row=0, column=1, padx=5)
        self.task_entry.bind('<Return>', lambda e: self.add_task())
        tk.Label(add_frame, text="Приоритет:", bg=self.colors['bg'], 
                fg=self.colors['fg'], font=('Arial', 10)).grid(row=0, column=2, padx=5)
        self.priority_var = tk.StringVar(value="medium")
        priority_combo = ttk.Combobox(add_frame, textvariable=self.priority_var,
                                      values=["high", "medium", "low"],
                                      state="readonly", width=10)
        priority_combo.grid(row=0, column=3, padx=5)
        tk.Label(add_frame, text="Срок (ГГГГ-ММ-ДД):", bg=self.colors['bg'], 
                fg=self.colors['fg'], font=('Arial', 10)).grid(row=0, column=4, padx=5)
        self.deadline_entry = tk.Entry(add_frame, width=15, font=('Arial', 10))
        self.deadline_entry.grid(row=0, column=5, padx=5)
        self.deadline_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        add_btn = tk.Button(add_frame, text="➕ Добавить задачу", 
                           command=self.add_task,
                           bg=self.colors['button'], fg='white',
                           font=('Arial', 10, 'bold'),
                           padx=10, pady=5)
        add_btn.grid(row=0, column=6, padx=10)
        columns = ("ID", "Статус", "Задача", "Приоритет", "Срок", "Создана", "Дней до срока")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings", 
                                 style="Custom.Treeview", height=20)
        column_widths = {"ID": 40, "Статус": 80, "Задача": 400, "Приоритет": 100,
                        "Срок": 120, "Создана": 120, "Дней до срока": 120}
        
        for col in columns:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_by_column(c))
            self.tree.column(col, width=column_widths.get(col, 100), anchor='center' if col != "Задача" else 'w')
        scrollbar = ttk.Scrollbar(self.root, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10), pady=10)
        bottom_frame = tk.Frame(self.root, bg=self.colors['bg'])
        bottom_frame.pack(fill=tk.X, padx=10, pady=10)
        btn_frame = tk.Frame(bottom_frame, bg=self.colors['bg'])
        btn_frame.pack()
        
        buttons = [
            ("✅ Выполнить", self.complete_task),
            ("✏️ Редактировать", self.edit_task),
            ("🗑️ Удалить", self.delete_task),
            ("📊 Статистика", self.show_stats),
            ("💾 Сохранить", self.save_tasks),
            ("🔄 Обновить", self.refresh_task_list)
        ]
        
        for text, command in buttons:
            btn = tk.Button(btn_frame, text=text, command=command,
                           bg=self.colors['button'], fg='white',
                           font=('Arial', 10), padx=15, pady=5)
            btn.pack(side=tk.LEFT, padx=5)
            def on_enter(e, b=btn):
                b['background'] = self.colors['button_hover']
            def on_leave(e, b=btn):
                b['background'] = self.colors['button']
            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)
        filter_frame = tk.Frame(bottom_frame, bg=self.colors['bg'])
        filter_frame.pack(pady=10)
        
        tk.Label(filter_frame, text="Фильтр:", bg=self.colors['bg'], 
                fg=self.colors['fg']).pack(side=tk.LEFT, padx=5)
        
        self.filter_var = tk.StringVar(value="all")
        filters = [("Все", "all"), ("Активные", "active"), 
                  ("Выполненные", "completed"), ("Просроченные", "overdue")]
        
        for text, value in filters:
            rb = tk.Radiobutton(filter_frame, text=text, variable=self.filter_var,
                               value=value, command=self.refresh_task_list,
                               bg=self.colors['bg'], fg=self.colors['fg'],
                               selectcolor=self.colors['bg'])
            rb.pack(side=tk.LEFT, padx=10)
    
    def add_task(self):
        title = self.task_entry.get().strip()
        if not title:
            messagebox.showwarning("Внимание", "Введите название задачи!")
            return
        
        deadline_str = self.deadline_entry.get().strip()
        try:
            deadline = datetime.strptime(deadline_str, "%Y-%m-%d")
            if deadline < datetime.now():
                response = messagebox.askyesno("Предупреждение", 
                                              "Срок уже прошел. Продолжить?")
                if not response:
                    return
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат даты! Используйте ГГГГ-ММ-ДД")
            return
        
        task = {
            "id": len(self.tasks) + 1,
            "title": title,
            "priority": self.priority_var.get(),
            "deadline": deadline_str,
            "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "completed": False,
            "completed_date": None
        }
        
        self.tasks.append(task)
        self.task_entry.delete(0, tk.END)
        self.save_tasks()
        self.refresh_task_list()
        messagebox.showinfo("Успех", "Задача добавлена!")
    
    def complete_task(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите задачу!")
            return
        
        task_id = int(self.tree.item(selected[0])['values'][0])
        for task in self.tasks:
            if task["id"] == task_id and not task["completed"]:
                task["completed"] = True
                task["completed_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.save_tasks()
                self.refresh_task_list()
                messagebox.showinfo("Успех", f"Задача '{task['title']}' выполнена!")
                break
    
    def edit_task(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите задачу!")
            return
        
        task_id = int(self.tree.item(selected[0])['values'][0])
        task = next((t for t in self.tasks if t["id"] == task_id), None)
        if task:
            dialog = tk.Toplevel(self.root)
            dialog.title("Редактирование задачи")
            dialog.geometry("400x300")
            dialog.configure(bg=self.colors['bg'])
            
            tk.Label(dialog, text="Название:", bg=self.colors['bg'], 
                    fg=self.colors['fg']).pack(pady=5)
            title_entry = tk.Entry(dialog, width=40)
            title_entry.insert(0, task["title"])
            title_entry.pack(pady=5)
            
            tk.Label(dialog, text="Приоритет:", bg=self.colors['bg'], 
                    fg=self.colors['fg']).pack(pady=5)
            priority_var = tk.StringVar(value=task["priority"])
            priority_combo = ttk.Combobox(dialog, textvariable=priority_var,
                                         values=["high", "medium", "low"],
                                         state="readonly")
            priority_combo.pack(pady=5)
            
            tk.Label(dialog, text="Срок (ГГГГ-ММ-ДД):", bg=self.colors['bg'], 
                    fg=self.colors['fg']).pack(pady=5)
            deadline_entry = tk.Entry(dialog)
            deadline_entry.insert(0, task["deadline"])
            deadline_entry.pack(pady=5)
            
            def save_edit():
                new_title = title_entry.get().strip()
                if new_title:
                    task["title"] = new_title
                    task["priority"] = priority_var.get()
                    task["deadline"] = deadline_entry.get()
                    self.save_tasks()
                    self.refresh_task_list()
                    dialog.destroy()
                    messagebox.showinfo("Успех", "Задача обновлена!")
            
            tk.Button(dialog, text="Сохранить", command=save_edit,
                     bg=self.colors['button'], fg='white').pack(pady=20)
    
    def delete_task(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите задачу!")
            return
        
        if messagebox.askyesno("Подтверждение", "Удалить выбранную задачу?"):
            task_id = int(self.tree.item(selected[0])['values'][0])
            self.tasks = [t for t in self.tasks if t["id"] != task_id]
            # Перенумерация ID
            for i, task in enumerate(self.tasks, 1):
                task["id"] = i
            self.save_tasks()
            self.refresh_task_list()
    
    def show_stats(self):
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks if t["completed"])
        active = total - completed
        
        # Статистика по приоритетам
        high = sum(1 for t in self.tasks if t["priority"] == "high" and not t["completed"])
        medium = sum(1 for t in self.tasks if t["priority"] == "medium" and not t["completed"])
        low = sum(1 for t in self.tasks if t["priority"] == "low" and not t["completed"])
        
        # Просроченные
        today = datetime.now().date()
        overdue = sum(1 for t in self.tasks 
                     if not t["completed"] and datetime.strptime(t["deadline"], "%Y-%m-%d").date() < today)
        
        stats_text = f"""
📊 Статистика задач:
━━━━━━━━━━━━━━━━━━━━━━━━━
📋 Всего задач: {total}
✅ Выполнено: {completed}
🔄 Активных: {active}
⚠️ Просрочено: {overdue}

Приоритеты активных задач:
🔴 Высокий: {high}
🟡 Средний: {medium}
🟢 Низкий: {low}

Прогресс: {int((completed/total)*100 if total > 0 else 0)}%
        """
        
        messagebox.showinfo("Статистика", stats_text)
    
    def sort_by_column(self, col):
        items = [(self.tree.set(child, col), child) for child in self.tree.get_children('')]
        if col in ["Срок", "Создана"]:
            items.sort(key=lambda x: x[0])
        elif col == "Дней до срока":
            items.sort(key=lambda x: int(x[0]) if x[0].isdigit() else 999)
        else:
            items.sort()
        
        for index, (val, child) in enumerate(items):
            self.tree.move(child, '', index)
    
    def refresh_task_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        filter_type = self.filter_var.get()
        today = datetime.now().date()
        
        for task in self.tasks:
            # Применение фильтра
            if filter_type == "completed" and not task["completed"]:
                continue
            elif filter_type == "active" and task["completed"]:
                continue
            elif filter_type == "overdue":
                deadline_date = datetime.strptime(task["deadline"], "%Y-%m-%d").date()
                if task["completed"] or deadline_date >= today:
                    continue
            
            # Расчет дней до срока
            deadline_date = datetime.strptime(task["deadline"], "%Y-%m-%d").date()
            days_left = (deadline_date - today).days
            status = "✅ Выполнена" if task["completed"] else "🔄 Активна"
            priority_text = {"high": "🔴 Высокий", "medium": "🟡 Средний", "low": "🟢 Низкий"}[task["priority"]]
            item_id = self.tree.insert("", tk.END, values=(
                task["id"],
                status,
                task["title"],
                priority_text,
                task["deadline"],
                task["created"].split()[0],
                days_left if not task["completed"] else "Выполнена"
            ))
            if not task["completed"] and days_left < 0:
                self.tree.tag_configure('overdue', background='#FF4444')
                self.tree.item(item_id, tags=('overdue',))
            elif not task["completed"] and days_left <= 3:
                self.tree.tag_configure('urgent', background='#FFA500')
                self.tree.item(item_id, tags=('urgent',))
            elif task["completed"]:
                self.tree.tag_configure('completed', foreground=self.colors['completed'])
                self.tree.item(item_id, tags=('completed',))
    
    def load_tasks(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.tasks = json.load(f)
            except:
                self.tasks = []
        else:
            self.tasks = [
                {
                    "id": 1,
                    "title": "Купить продукты",
                    "priority": "high",
                    "deadline": datetime.now().strftime("%Y-%m-%d"),
                    "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "completed": False,
                    "completed_date": None
                },
                {
                    "id": 2,
                    "title": "Сделать домашнее задание",
                    "priority": "high",
                    "deadline": (datetime.now().replace(day=datetime.now().day+2)).strftime("%Y-%m-%d"),
                    "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "completed": False,
                    "completed_date": None
                },
                {
                    "id": 3,
                    "title": "Позвонить родителям",
                    "priority": "medium",
                    "deadline": (datetime.now().replace(day=datetime.now().day+1)).strftime("%Y-%m-%d"),
                    "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "completed": False,
                    "completed_date": None
                }
            ]
            self.save_tasks()
    
    def save_tasks(self):
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.tasks, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить задачи: {e}")
    
    def on_closing(self):
        self.save_tasks()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = TodoApp(root)
    root.mainloop()
