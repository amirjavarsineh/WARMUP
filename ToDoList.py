import csv
from enum import Enum
from datetime import datetime, timedelta
import os
from typing import List, Dict, Optional
import pickle
from abc import ABC, abstractmethod
import json


class Priority(Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

    @classmethod
    def from_string(cls, value: str):
        for priority in cls:
            if priority.value == value:
                return priority
        raise ValueError(f"Invalid priority: {value}")


class Category:
    def __init__(self, name: str, color: str = "#FFFFFF"):
        self.name = name
        self.color = color

    def __str__(self):
        return f"{self.name} (Color: {self.color})"

    def to_dict(self):
        return {'name': self.name, 'color': self.color}

    @classmethod
    def from_dict(cls, data: Dict):
        return cls(data['name'], data.get('color', "#FFFFFF"))


class Task:
    def __init__(self,
                 name: str,
                 description: str = "",
                 priority: Priority = Priority.MEDIUM,
                 due_date: Optional[datetime] = None,
                 category: Optional[Category] = None,
                 completed: bool = False,
                 created_at: Optional[datetime] = None,
                 completed_at: Optional[datetime] = None):
        self.name = name
        self.description = description
        self.priority = priority
        self.due_date = due_date
        self.category = category
        self.completed = completed
        self.created_at = created_at or datetime.now()
        self.completed_at = completed_at

    def __str__(self):
        status = "✅" if self.completed else "⏳"
        priority_str = f" | Priority: {self.priority.value}" if self.priority else ""
        category_str = f" | Category: {self.category.name}" if self.category else ""
        due_date_str = f" | Due: {self.due_date.strftime('%Y-%m-%d %H:%M')}" if self.due_date else ""
        return f"{status} Name: {self.name} | Desc: {self.description}{priority_str}{category_str}{due_date_str}"

    def to_dict(self):
        return {
            'name': self.name,
            'description': self.description,
            'priority': self.priority.name if self.priority else None,
            'due_date': self.due_date.timestamp() if self.due_date else None,
            'category': self.category.to_dict() if self.category else None,
            'completed': self.completed,
            'created_at': self.created_at.timestamp(),
            'completed_at': self.completed_at.timestamp() if self.completed_at else None
        }

    def complete(self):
        self.completed = True
        self.completed_at = datetime.now()

    def is_overdue(self) -> bool:
        return not self.completed and self.due_date and datetime.now() > self.due_date

    def days_until_due(self) -> Optional[int]:
        if self.due_date:
            return (self.due_date - datetime.now()).days
        return None


class TaskFilter(ABC):
    @abstractmethod
    def filter(self, task: Task) -> bool:
        pass


class PriorityFilter(TaskFilter):
    def __init__(self, priority: Priority):
        self.priority = priority

    def filter(self, task: Task) -> bool:
        return task.priority == self.priority


class CategoryFilter(TaskFilter):
    def __init__(self, category: Category):
        self.category = category

    def filter(self, task: Task) -> bool:
        return task.category and task.category.name == self.category.name


class CompletedFilter(TaskFilter):
    def __init__(self, completed: bool):
        self.completed = completed

    def filter(self, task: Task) -> bool:
        return task.completed == self.completed


class OverdueFilter(TaskFilter):
    def filter(self, task: Task) -> bool:
        return task.is_overdue()


class TaskStatistics:
    def __init__(self, tasks: List[Task]):
        self.tasks = tasks

    def total_tasks(self) -> int:
        return len(self.tasks)

    def completed_tasks(self) -> int:
        return sum(1 for task in self.tasks if task.completed)

    def completion_percentage(self) -> float:
        if not self.tasks:
            return 0.0
        return (self.completed_tasks() / self.total_tasks()) * 100

    def tasks_by_priority(self) -> Dict[Priority, int]:
        counts = {priority: 0 for priority in Priority}
        for task in self.tasks:
            if task.priority in counts:
                counts[task.priority] += 1
        return counts

    def overdue_tasks(self) -> int:
        return sum(1 for task in self.tasks if task.is_overdue())

    def recently_completed(self, days: int = 7) -> List[Task]:
        cutoff = datetime.now() - timedelta(days=days)
        return [task for task in self.tasks
                if task.completed and task.completed_at and task.completed_at >= cutoff]


class TaskExporter(ABC):
    @abstractmethod
    def export(self, tasks: List[Task], filename: str):
        pass


class CSVExporter(TaskExporter):
    def export(self, tasks: List[Task], filename: str):
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=[
                'name', 'description', 'priority', 'due_date',
                'category', 'completed', 'created_at', 'completed_at'
            ])
            writer.writeheader()
            for task in tasks:
                writer.writerow(task.to_dict())


class JSONExporter(TaskExporter):
    def export(self, tasks: List[Task], filename: str):
        with open(filename, mode='w', encoding='utf-8') as file:
            json.dump([task.to_dict() for task in tasks], file, indent=2)


class TextExporter(TaskExporter):
    def export(self, tasks: List[Task], filename: str):
        with open(filename, mode='w', encoding='utf-8') as file:
            for task in tasks:
                file.write(str(task) + "\n")


class ToDoList:
    def __init__(self, data_dir='todo_data'):
        self.tasks: List[Task] = []
        self.categories: List[Category] = []
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self.load_data()

    def add_task(self, task: Task):
        self.tasks.append(task)
        self.save_data()

    def remove_task(self, index: int) -> Optional[Task]:
        if 0 <= index < len(self.tasks):
            removed_task = self.tasks.pop(index)
            self.save_data()
            return removed_task
        return None

    def complete_task(self, index: int) -> bool:
        if 0 <= index < len(self.tasks):
            self.tasks[index].complete()
            self.save_data()
            return True
        return False

    def edit_task(self, index: int, **kwargs):
        if 0 <= index < len(self.tasks):
            task = self.tasks[index]
            for key, value in kwargs.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            self.save_data()
            return True
        return False

    def view_tasks(self, filters: Optional[List[TaskFilter]] = None):
        filtered_tasks = self.tasks
        if filters:
            for task_filter in filters:
                filtered_tasks = [task for task in filtered_tasks if task_filter.filter(task)]

        if not filtered_tasks:
            print("No tasks found.")
            return

        print("\nTask List:")
        for i, task in enumerate(filtered_tasks, 1):
            print(f"{i}. {task}")

    def add_category(self, category: Category):
        self.categories.append(category)
        self.save_data()

    def remove_category(self, index: int) -> Optional[Category]:
        if 0 <= index < len(self.categories):
            removed_category = self.categories.pop(index)
            # Remove this category from all tasks
            for task in self.tasks:
                if task.category and task.category.name == removed_category.name:
                    task.category = None
            self.save_data()
            return removed_category
        return None

    def view_categories(self):
        if not self.categories:
            print("No categories defined.")
            return

        print("\nCategories:")
        for i, category in enumerate(self.categories, 1):
            print(f"{i}. {category}")

    def get_statistics(self) -> TaskStatistics:
        return TaskStatistics(self.tasks)

    def export_tasks(self, exporter: TaskExporter, filename: str):
        exporter.export(self.tasks, filename)
        print(f"Tasks successfully exported to {filename}")

    def save_data(self):
        # Save tasks
        with open(os.path.join(self.data_dir, 'tasks.pkl'), 'wb') as f:
            pickle.dump(self.tasks, f)

        # Save categories
        with open(os.path.join(self.data_dir, 'categories.pkl'), 'wb') as f:
            pickle.dump(self.categories, f)

    def load_data(self):
        # Load tasks
        try:
            with open(os.path.join(self.data_dir, 'tasks.pkl'), 'rb') as f:
                self.tasks = pickle.load(f)
        except (FileNotFoundError, EOFError):
            self.tasks = []

        # Load categories
        try:
            with open(os.path.join(self.data_dir, 'categories.pkl'), 'rb') as f:
                self.categories = pickle.load(f)
        except (FileNotFoundError, EOFError):
            self.categories = []


def display_menu():
    print("\nTo-Do List Manager:")
    print("1. View tasks")
    print("2. Add new task")
    print("3. Edit task")
    print("4. Delete task")
    print("5. Mark task as complete")
    print("6. Manage categories")
    print("7. View statistics")
    print("8. Export tasks")
    print("9. Exit")


def get_priority_input() -> Priority:
    print("\nPriority level:")
    for i, priority in enumerate(Priority, 1):
        print(f"{i}. {priority.value}")
    while True:
        try:
            choice = int(input("Select priority (1-3): "))
            if 1 <= choice <= 3:
                return list(Priority)[choice - 1]
            print("Please enter a number between 1 and 3.")
        except ValueError:
            print("Please enter a valid number.")


def get_date_input(prompt: str) -> Optional[datetime]:
    while True:
        date_str = input(prompt + " (YYYY-MM-DD or empty for no date): ")
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD.")


def get_category_input(todo_list: ToDoList) -> Optional[Category]:
    if not todo_list.categories:
        return None

    todo_list.view_categories()
    print(f"{len(todo_list.categories) + 1}. Create new category")
    print(f"{len(todo_list.categories) + 2}. No category")

    while True:
        try:
            choice = int(input("Select category: "))
            if 1 <= choice <= len(todo_list.categories):
                return todo_list.categories[choice - 1]
            elif choice == len(todo_list.categories) + 1:
                name = input("New category name: ")
                color = input("Category color (HEX code like #FF0000): ")
                new_category = Category(name, color)
                todo_list.add_category(new_category)
                return new_category
            elif choice == len(todo_list.categories) + 2:
                return None
            else:
                print("Invalid number. Please try again.")
        except ValueError:
            print("Please enter a valid number.")


def manage_categories(todo_list: ToDoList):
    while True:
        print("\nCategory Management:")
        print("1. View categories")
        print("2. Add new category")
        print("3. Delete category")
        print("4. Return to main menu")

        choice = input("Select option: ")

        if choice == '1':
            todo_list.view_categories()
        elif choice == '2':
            name = input("New category name: ")
            color = input("Category color (HEX code like #FF0000): ")
            new_category = Category(name, color)
            todo_list.add_category(new_category)
            print("Category added successfully.")
        elif choice == '3':
            todo_list.view_categories()
            if todo_list.categories:
                try:
                    cat_num = int(input("Enter category number to delete: "))
                    removed_category = todo_list.remove_category(cat_num - 1)
                    if removed_category:
                        print(f"Category '{removed_category.name}' deleted.")
                    else:
                        print("Invalid category number.")
                except ValueError:
                    print("Please enter a valid number.")
        elif choice == '4':
            break
        else:
            print("Invalid option. Please try again.")


def view_statistics(todo_list: ToDoList):
    stats = todo_list.get_statistics()

    print("\nStatistics:")
    print(f"Total tasks: {stats.total_tasks()}")
    print(f"Completed tasks: {stats.completed_tasks()} ({stats.completion_percentage():.1f}%)")
    print(f"Overdue tasks: {stats.overdue_tasks()}")

    print("\nTasks by priority:")
    for priority, count in stats.tasks_by_priority().items():
        print(f"{priority.value}: {count}")

    recent_completed = stats.recently_completed()
    if recent_completed:
        print(f"\nRecently completed tasks (last 7 days): {len(recent_completed)}")
        for task in recent_completed:
            print(f"- {task.name} (completed on {task.completed_at.strftime('%Y-%m-%d')})")


def export_tasks_menu(todo_list: ToDoList):
    print("\nExport Tasks:")
    print("1. Export to CSV")
    print("2. Export to JSON")
    print("3. Export to Text")
    print("4. Cancel")

    choice = input("Select export format: ")

    if choice == '1':
        filename = input("Output filename (e.g., tasks.csv): ")
        exporter = CSVExporter()
        todo_list.export_tasks(exporter, filename)
    elif choice == '2':
        filename = input("Output filename (e.g., tasks.json): ")
        exporter = JSONExporter()
        todo_list.export_tasks(exporter, filename)
    elif choice == '3':
        filename = input("Output filename (e.g., tasks.txt): ")
        exporter = TextExporter()
        todo_list.export_tasks(exporter, filename)
    elif choice == '4':
        return
    else:
        print("Invalid option.")


def main():
    todo_list = ToDoList()

    while True:
        display_menu()
        choice = input("Select option: ")

        if choice == '1':
            print("\nView Filters:")
            print("1. All tasks")
            print("2. Completed tasks")
            print("3. Pending tasks")
            print("4. Overdue tasks")
            print("5. Tasks by priority")
            print("6. Tasks by category")
            print("7. Recently completed")

            filter_choice = input("Select filter (empty for all tasks): ")

            filters = []
            if filter_choice == '2':
                filters.append(CompletedFilter(True))
            elif filter_choice == '3':
                filters.append(CompletedFilter(False))
            elif filter_choice == '4':
                filters.append(OverdueFilter())
            elif filter_choice == '5':
                priority = get_priority_input()
                filters.append(PriorityFilter(priority))
            elif filter_choice == '6':
                category = get_category_input(todo_list)
                if category:
                    filters.append(CategoryFilter(category))
            elif filter_choice == '7':
                recent_tasks = todo_list.get_statistics().recently_completed()
                if recent_tasks:
                    print("\nRecently Completed Tasks:")
                    for i, task in enumerate(recent_tasks, 1):
                        print(f"{i}. {task}")
                    continue
                else:
                    print("No recently completed tasks.")
                    continue

            todo_list.view_tasks(filters)

        elif choice == '2':
            name = input("Task name: ")
            description = input("Task description: ")
            priority = get_priority_input()
            due_date = get_date_input("Due date")
            category = get_category_input(todo_list)

            new_task = Task(
                name=name,
                description=description,
                priority=priority,
                due_date=due_date,
                category=category
            )
            todo_list.add_task(new_task)
            print("Task added successfully.")

        elif choice == '3':
            todo_list.view_tasks()
            if todo_list.tasks:
                try:
                    task_num = int(input("Enter task number to edit: "))
                    if 1 <= task_num <= len(todo_list.tasks):
                        task = todo_list.tasks[task_num - 1]

                        print("\nEdit Task:")
                        print(f"1. Current name: {task.name}")
                        print(f"2. Current description: {task.description}")
                        print(f"3. Current priority: {task.priority.value if task.priority else 'None'}")
                        print(f"4. Current due date: {task.due_date.strftime('%Y-%m-%d') if task.due_date else 'None'}")
                        print(f"5. Current category: {task.category.name if task.category else 'None'}")
                        print("6. Cancel")

                        edit_choice = input("What would you like to edit? ")

                        if edit_choice == '1':
                            new_name = input("New name: ")
                            todo_list.edit_task(task_num - 1, name=new_name)
                            print("Name updated successfully.")
                        elif edit_choice == '2':
                            new_desc = input("New description: ")
                            todo_list.edit_task(task_num - 1, description=new_desc)
                            print("Description updated successfully.")
                        elif edit_choice == '3':
                            new_priority = get_priority_input()
                            todo_list.edit_task(task_num - 1, priority=new_priority)
                            print("Priority updated successfully.")
                        elif edit_choice == '4':
                            new_due_date = get_date_input("New due date")
                            todo_list.edit_task(task_num - 1, due_date=new_due_date)
                            print("Due date updated successfully.")
                        elif edit_choice == '5':
                            new_category = get_category_input(todo_list)
                            todo_list.edit_task(task_num - 1, category=new_category)
                            print("Category updated successfully.")
                        elif edit_choice == '6':
                            continue
                        else:
                            print("Invalid option.")
                    else:
                        print("Invalid task number.")
                except ValueError:
                    print("Please enter a valid number.")

        elif choice == '4':
            todo_list.view_tasks()
            if todo_list.tasks:
                try:
                    task_num = int(input("Enter task number to delete: "))
                    removed_task = todo_list.remove_task(task_num - 1)
                    if removed_task:
                        print(f"Task '{removed_task.name}' deleted.")
                    else:
                        print("Invalid task number.")
                except ValueError:
                    print("Please enter a valid number.")

        elif choice == '5':
            todo_list.view_tasks([CompletedFilter(False)])
            if any(not task.completed for task in todo_list.tasks):
                try:
                    task_num = int(input("Enter task number to mark as complete: "))
                    if todo_list.complete_task(task_num - 1):
                        print("Task marked as complete.")
                    else:
                        print("Invalid task number.")
                except ValueError:
                    print("Please enter a valid number.")

        elif choice == '6':
            manage_categories(todo_list)

        elif choice == '7':
            view_statistics(todo_list)

        elif choice == '8':
            export_tasks_menu(todo_list)

        elif choice == '9':
            print("Exiting application...")
            break

        else:
            print("Invalid option. Please enter a number between 1 and 9.")


if __name__ == "__main__":
    main()