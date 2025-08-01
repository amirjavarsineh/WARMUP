import os
import shutil
import hashlib
import time
import stat
import subprocess
import sys
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, simpledialog


class AdvancedFileManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Python File Manager")
        self.root.geometry("900x600")

        # Dark theme settings
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TFrame', background='#333')
        self.style.configure('TLabel', background='#333', foreground='white')
        self.style.configure('TButton', background='#444', foreground='white')
        self.style.configure('Treeview', background='#444', foreground='white', fieldbackground='#444')
        self.style.map('Treeview', background=[('selected', '#0066cc')])

        self.current_path = os.path.expanduser("~")
        self.create_widgets()
        self.update_file_list()

    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Address bar
        path_frame = ttk.Frame(main_frame)
        path_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(path_frame, text="Path:").pack(side=tk.LEFT)
        self.path_entry = ttk.Entry(path_frame)
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.path_entry.insert(0, self.current_path)
        self.path_entry.bind("<Return>", self.on_path_changed)

        # Navigation buttons
        nav_frame = ttk.Frame(main_frame)
        nav_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(nav_frame, text="Back", command=self.go_back).pack(side=tk.LEFT, padx=2)
        ttk.Button(nav_frame, text="Up", command=self.go_up).pack(side=tk.LEFT, padx=2)
        ttk.Button(nav_frame, text="Refresh", command=self.update_file_list).pack(side=tk.LEFT, padx=2)
        ttk.Button(nav_frame, text="New Folder", command=self.create_folder).pack(side=tk.LEFT, padx=2)

        # File tree
        self.tree = ttk.Treeview(main_frame, columns=('name', 'size', 'type', 'modified'), selectmode='browse')
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.tree.heading('#0', text='Name')
        self.tree.heading('name', text='Name')
        self.tree.heading('size', text='Size')
        self.tree.heading('type', text='Type')
        self.tree.heading('modified', text='Modified')

        self.tree.column('#0', width=300)
        self.tree.column('name', width=300)
        self.tree.column('size', width=100)
        self.tree.column('type', width=100)
        self.tree.column('modified', width=150)

        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<Button-3>", self.show_context_menu)

        # Status bar
        self.status_bar = ttk.Label(main_frame, text="Ready", relief=tk.SUNKEN)
        self.status_bar.pack(fill=tk.X, padx=5, pady=5)

        # Right-click menu
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Open", command=self.open_selected)
        self.context_menu.add_command(label="Properties", command=self.show_properties)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Delete", command=self.delete_selected)
        self.context_menu.add_command(label="Rename", command=self.rename_selected)
        self.context_menu.add_command(label="Copy", command=self.copy_selected)
        self.context_menu.add_command(label="Move", command=self.move_selected)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Calculate Hash", command=self.calculate_hash)
        self.context_menu.add_command(label="Change Permissions", command=self.change_permissions)

    def update_file_list(self):
        self.tree.delete(*self.tree.get_children())

        try:
            # Add parent folder (if not root)
            if self.current_path != os.path.sep:
                parent_path = os.path.dirname(self.current_path)
                self.tree.insert('', 'end', text="..", values=("..", "", "Folder", ""), iid="..")

            # List files and folders
            for item in os.listdir(self.current_path):
                full_path = os.path.join(self.current_path, item)
                item_stat = os.stat(full_path)

                if os.path.isdir(full_path):
                    item_type = "Folder"
                    size = ""
                else:
                    item_type = "File"
                    size = self.format_size(item_stat.st_size)

                modified = datetime.fromtimestamp(item_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                self.tree.insert('', 'end', text=item, values=(item, size, item_type, modified), iid=full_path)

            self.status_bar.config(text=f"Items: {len(os.listdir(self.current_path))}")
        except PermissionError:
            messagebox.showerror("Error", "Permission denied for this folder")

    def format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"

    def on_double_click(self, event):
        item = self.tree.selection()[0]
        if item == "..":
            self.go_up()
        else:
            if os.path.isdir(item):
                self.current_path = item
                self.path_entry.delete(0, tk.END)
                self.path_entry.insert(0, self.current_path)
                self.update_file_list()
            else:
                self.open_file(item)

    def on_path_changed(self, event):
        new_path = self.path_entry.get()
        if os.path.exists(new_path):
            self.current_path = new_path
            self.update_file_list()
        else:
            messagebox.showerror("Error", "The specified path does not exist")
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, self.current_path)

    def go_back(self):
        # This function could implement navigation history
        pass

    def go_up(self):
        parent_path = os.path.dirname(self.current_path)
        if os.path.exists(parent_path):
            self.current_path = parent_path
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, self.current_path)
            self.update_file_list()

    def create_folder(self):
        folder_name = simpledialog.askstring("New Folder", "Enter new folder name:")
        if folder_name:
            try:
                os.mkdir(os.path.join(self.current_path, folder_name))
                self.update_file_list()
            except OSError as e:
                messagebox.showerror("Error", f"Error creating folder: {e}")

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def open_selected(self):
        item = self.tree.selection()[0]
        if item == "..":
            self.go_up()
        else:
            if os.path.isdir(item):
                self.current_path = item
                self.path_entry.delete(0, tk.END)
                self.path_entry.insert(0, self.current_path)
                self.update_file_list()
            else:
                self.open_file(item)

    def open_file(self, file_path):
        try:
            if os.name == 'nt':  # Windows
                os.startfile(file_path)
            elif os.name == 'posix':  # Linux and Mac
                opener = "open" if sys.platform == "darwin" else "xdg-open"
                subprocess.call([opener, file_path])
        except Exception as e:
            messagebox.showerror("Error", f"Cannot open file: {e}")

    def show_properties(self):
        item = self.tree.selection()[0]
        if item == "..":
            return

        full_path = item
        stat_info = os.stat(full_path)

        properties = f"Name: {os.path.basename(full_path)}\n"
        properties += f"Path: {full_path}\n"
        properties += f"Type: {'Folder' if os.path.isdir(full_path) else 'File'}\n"
        properties += f"Size: {self.format_size(stat_info.st_size)}\n"
        properties += f"Created: {datetime.fromtimestamp(stat_info.st_ctime)}\n"
        properties += f"Modified: {datetime.fromtimestamp(stat_info.st_mtime)}\n"
        properties += f"Permissions: {stat.filemode(stat_info.st_mode)}\n"
        properties += f"Owner: {stat_info.st_uid}\n"
        properties += f"Group: {stat_info.st_gid}\n"

        if not os.path.isdir(full_path):
            properties += f"Extension: {os.path.splitext(full_path)[1]}\n"

        messagebox.showinfo("Properties", properties)

    def delete_selected(self):
        item = self.tree.selection()[0]
        if item == "..":
            return

        full_path = item
        if messagebox.askyesno("Delete", f"Are you sure you want to delete '{os.path.basename(full_path)}'?"):
            try:
                if os.path.isdir(full_path):
                    shutil.rmtree(full_path)
                else:
                    os.remove(full_path)
                self.update_file_list()
            except Exception as e:
                messagebox.showerror("Error", f"Error deleting: {e}")

    def rename_selected(self):
        item = self.tree.selection()[0]
        if item == "..":
            return

        full_path = item
        new_name = simpledialog.askstring("Rename", "Enter new name:", initialvalue=os.path.basename(full_path))
        if new_name and new_name != os.path.basename(full_path):
            try:
                new_path = os.path.join(os.path.dirname(full_path), new_name)
                os.rename(full_path, new_path)
                self.update_file_list()
            except Exception as e:
                messagebox.showerror("Error", f"Error renaming: {e}")

    def copy_selected(self):
        item = self.tree.selection()[0]
        if item == "..":
            return

        self.clipboard = {'operation': 'copy', 'path': item}
        self.status_bar.config(text=f"Ready to copy: {os.path.basename(item)}")

    def move_selected(self):
        item = self.tree.selection()[0]
        if item == "..":
            return

        self.clipboard = {'operation': 'move', 'path': item}
        self.status_bar.config(text=f"Ready to move: {os.path.basename(item)}")

    def paste(self):
        if hasattr(self, 'clipboard'):
            dest = self.current_path
            src = self.clipboard['path']

            try:
                if self.clipboard['operation'] == 'copy':
                    if os.path.isdir(src):
                        shutil.copytree(src, os.path.join(dest, os.path.basename(src)))
                    else:
                        shutil.copy2(src, dest)
                elif self.clipboard['operation'] == 'move':
                    shutil.move(src, dest)

                self.update_file_list()
                self.status_bar.config(text="Operation completed successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Operation error: {e}")

    def calculate_hash(self):
        item = self.tree.selection()[0]
        if item == ".." or os.path.isdir(item):
            messagebox.showerror("Error", "This operation is only available for files")
            return

        hash_window = tk.Toplevel(self.root)
        hash_window.title("Calculate File Hash")
        hash_window.geometry("400x300")

        ttk.Label(hash_window, text=f"Calculating hash for: {os.path.basename(item)}").pack(pady=5)

        hash_types = ['MD5', 'SHA1', 'SHA256', 'SHA512']
        self.hash_var = tk.StringVar(value=hash_types[0])

        hash_frame = ttk.Frame(hash_window)
        hash_frame.pack(pady=5)

        for htype in hash_types:
            ttk.Radiobutton(hash_frame, text=htype, variable=self.hash_var, value=htype).pack(side=tk.LEFT, padx=5)

        self.hash_result = scrolledtext.ScrolledText(hash_window, height=8, width=50)
        self.hash_result.pack(pady=5, padx=5, fill=tk.BOTH, expand=True)

        ttk.Button(hash_window, text="Calculate", command=lambda: self.do_calculate_hash(item)).pack(pady=5)

    def do_calculate_hash(self, file_path):
        hash_type = self.hash_var.get()
        buffer_size = 65536

        try:
            if hash_type == 'MD5':
                hasher = hashlib.md5()
            elif hash_type == 'SHA1':
                hasher = hashlib.sha1()
            elif hash_type == 'SHA256':
                hasher = hashlib.sha256()
            elif hash_type == 'SHA512':
                hasher = hashlib.sha512()

            with open(file_path, 'rb') as f:
                while True:
                    data = f.read(buffer_size)
                    if not data:
                        break
                    hasher.update(data)

            self.hash_result.delete(1.0, tk.END)
            self.hash_result.insert(tk.END, f"{hash_type} hash:\n{hasher.hexdigest()}")
        except Exception as e:
            messagebox.showerror("Error", f"Hash calculation error: {e}")

    def change_permissions(self):
        item = self.tree.selection()[0]
        if item == "..":
            return

        current_permissions = stat.S_IMODE(os.stat(item).st_mode)

        perm_window = tk.Toplevel(self.root)
        perm_window.title("Change Permissions")
        perm_window.geometry("300x300")

        ttk.Label(perm_window, text=f"Current permissions: {oct(current_permissions)}").pack(pady=5)

        # Owner permissions
        owner_frame = ttk.LabelFrame(perm_window, text="Owner")
        owner_frame.pack(pady=5, padx=5, fill=tk.X)

        self.owner_read = tk.BooleanVar(value=bool(current_permissions & stat.S_IRUSR))
        self.owner_write = tk.BooleanVar(value=bool(current_permissions & stat.S_IWUSR))
        self.owner_exec = tk.BooleanVar(value=bool(current_permissions & stat.S_IXUSR))

        ttk.Checkbutton(owner_frame, text="Read", variable=self.owner_read).pack(anchor=tk.W)
        ttk.Checkbutton(owner_frame, text="Write", variable=self.owner_write).pack(anchor=tk.W)
        ttk.Checkbutton(owner_frame, text="Execute", variable=self.owner_exec).pack(anchor=tk.W)

        # Group permissions
        group_frame = ttk.LabelFrame(perm_window, text="Group")
        group_frame.pack(pady=5, padx=5, fill=tk.X)

        self.group_read = tk.BooleanVar(value=bool(current_permissions & stat.S_IRGRP))
        self.group_write = tk.BooleanVar(value=bool(current_permissions & stat.S_IWGRP))
        self.group_exec = tk.BooleanVar(value=bool(current_permissions & stat.S_IXGRP))

        ttk.Checkbutton(group_frame, text="Read", variable=self.group_read).pack(anchor=tk.W)
        ttk.Checkbutton(group_frame, text="Write", variable=self.group_write).pack(anchor=tk.W)
        ttk.Checkbutton(group_frame, text="Execute", variable=self.group_exec).pack(anchor=tk.W)

        # Others permissions
        other_frame = ttk.LabelFrame(perm_window, text="Others")
        other_frame.pack(pady=5, padx=5, fill=tk.X)

        self.other_read = tk.BooleanVar(value=bool(current_permissions & stat.S_IROTH))
        self.other_write = tk.BooleanVar(value=bool(current_permissions & stat.S_IWOTH))
        self.other_exec = tk.BooleanVar(value=bool(current_permissions & stat.S_IXOTH))

        ttk.Checkbutton(other_frame, text="Read", variable=self.other_read).pack(anchor=tk.W)
        ttk.Checkbutton(other_frame, text="Write", variable=self.other_write).pack(anchor=tk.W)
        ttk.Checkbutton(other_frame, text="Execute", variable=self.other_exec).pack(anchor=tk.W)

        ttk.Button(perm_window, text="Apply Changes",
                   command=lambda: self.do_change_permissions(item)).pack(pady=10)

    def do_change_permissions(self, path):
        new_permissions = 0

        if self.owner_read.get(): new_permissions |= stat.S_IRUSR
        if self.owner_write.get(): new_permissions |= stat.S_IWUSR
        if self.owner_exec.get(): new_permissions |= stat.S_IXUSR

        if self.group_read.get(): new_permissions |= stat.S_IRGRP
        if self.group_write.get(): new_permissions |= stat.S_IWGRP
        if self.group_exec.get(): new_permissions |= stat.S_IXGRP

        if self.other_read.get(): new_permissions |= stat.S_IROTH
        if self.other_write.get(): new_permissions |= stat.S_IWOTH
        if self.other_exec.get(): new_permissions |= stat.S_IXOTH

        try:
            os.chmod(path, new_permissions)
            messagebox.showinfo("Success", "Permissions changed successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Error changing permissions: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = AdvancedFileManager(root)
    root.mainloop()