import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import random
import time
import csv
import os
import sys
import atexit
from datetime import datetime
from threading import Thread, Event

class ProgressViewer(tk.Toplevel):
    def __init__(self, parent, log_file):
        super().__init__(parent)
        self.log_file = log_file
        
        self.title("Practice Session Progress")
        self.geometry("900x600")
        self.configure(bg='#1a1a2e')
        
        # Main container
        main_frame = tk.Frame(self, bg='#1a1a2e')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title with improved styling
        title_frame = tk.Frame(main_frame, bg='#1a1a2e')
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = tk.Label(
            title_frame, 
            text="Session Progress", 
            font=("Montserrat", 28, "bold"), 
            bg='#1a1a2e', 
            fg='#e94560'
        )
        title_label.pack(anchor='center')
        
        # Treeview styling
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            "Custom.Treeview", 
            background='#16213e', 
            foreground='white', 
            rowheight=35, 
            fieldbackground='#16213e'
        )
        style.configure(
            "Custom.Treeview.Heading", 
            background='#0f3460', 
            foreground='#e94560', 
            font=('Roboto', 12, 'bold')
        )
        style.map('Custom.Treeview', 
            background=[('selected', '#e94560')],
            foreground=[('selected', 'white')]
        )
        
        # Treeview container
        tree_frame = tk.Frame(main_frame, bg='#1a1a2e')
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        self.tree = ttk.Treeview(
            tree_frame, 
            columns=("Start", "End", "Duration"), 
            show="headings", 
            style="Custom.Treeview"
        )
        
        # Configure columns with improved alignment
        self.tree.heading("Start", text="Session Start ▼", command=lambda: self.sort_column("Start", False))
        self.tree.heading("End", text="Session End ▼", command=lambda: self.sort_column("End", False))
        self.tree.heading("Duration", text="Duration (sec) ▼", command=lambda: self.sort_column("Duration", False))
        
        self.tree.column("Start", width=300, anchor='center')
        self.tree.column("End", width=300, anchor='center')
        self.tree.column("Duration", width=150, anchor='center')
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(
            tree_frame, 
            orient=tk.VERTICAL, 
            command=self.tree.yview
        )
        self.tree.configure(yscroll=scrollbar.set)
        
        # Layout treeview and scrollbar
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Summary statistics frame with improved layout
        summary_frame = tk.Frame(main_frame, bg='#16213e')
        summary_frame.pack(fill=tk.X, pady=(20, 0), ipady=10)
        
        # Statistics labels with equal spacing
        self.total_sessions_label = tk.Label(
            summary_frame, 
            text="Total Sessions: 0", 
            bg='#16213e', 
            fg='#e94560', 
            font=('Roboto', 14, 'bold')
        )
        self.total_sessions_label.pack(side=tk.LEFT, expand=True, padx=20)
        
        self.total_duration_label = tk.Label(
            summary_frame, 
            text="Total Duration: 0 sec", 
            bg='#16213e', 
            fg='#e94560', 
            font=('Roboto', 14, 'bold')
        )
        self.total_duration_label.pack(side=tk.LEFT, expand=True, padx=20)
        
        self.avg_duration_label = tk.Label(
            summary_frame, 
            text="Avg Session: 0 sec", 
            bg='#16213e', 
            fg='#e94560', 
            font=('Roboto', 14, 'bold')
        )
        self.avg_duration_label.pack(side=tk.LEFT, expand=True, padx=20)
        
        # Load progress and calculate statistics
        self.load_progress()
    
    def load_progress(self):
        try:
            with open(self.log_file, 'r') as file:
                csv_reader = csv.reader(file)
                next(csv_reader)  # Skip header
                
                total_duration = 0
                session_count = 0
                sessions = []
                
                for row in csv_reader:
                    if len(row) == 3:
                        try:
                            duration = int(row[2])
                            total_duration += duration
                            session_count += 1
                            sessions.append(row)
                        except ValueError:
                            pass
                
                # Sort sessions by start time (descending)
                sessions.sort(key=lambda x: x[0], reverse=True)
                
                # Insert sorted sessions
                for row in sessions:
                    self.tree.insert("", tk.END, values=row, tags=('session',))
                
                # Update summary labels
                avg_duration = total_duration // session_count if session_count > 0 else 0
                
                self.total_sessions_label.config(text=f"Total Sessions: {session_count}")
                self.total_duration_label.config(text=f"Total Duration: {total_duration} sec")
                self.avg_duration_label.config(text=f"Avg Session: {avg_duration} sec")
                
        except FileNotFoundError:
            tk.messagebox.showinfo("No Data", "No session logs found.")
        except Exception as e:
            tk.messagebox.showerror("Error", f"Could not read log file: {e}")
    
    def sort_column(self, col, reverse):
        l = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        
        try:
            # If column is numeric (duration), sort numerically
            l.sort(key=lambda t: int(t[0]), reverse=reverse)
        except ValueError:
            # If not numeric, sort as strings
            l.sort(key=lambda t: t[0], reverse=reverse)
        
        # Rearrange items in sorted positions
        for index, (val, k) in enumerate(l):
            self.tree.move(k, '', index)
        
        # Update heading to show sort direction
        sort_symbol = "▲" if reverse else "▼"
        self.tree.heading(col, text=f"{col} {sort_symbol}", command=lambda: self.sort_column(col, not reverse))

class CSVManager:
    def __init__(self, root, csv_dir="practice_files"):
        self.root = root
        self.csv_dir = csv_dir
        self.current_file = None
        
        # Create directory if it doesn't exist
        if not os.path.exists(csv_dir):
            os.makedirs(csv_dir)
            self.create_default_csv()
    
    def create_default_csv(self):
        """Creates a default CSV file with some common guitar chords"""
        default_chords = [
            {"Type": "A", "Duration": "15"},
            {"Type": "D", "Duration": "15"},
            {"Type": "G", "Duration": "15"},
            {"Type": "E", "Duration": "15"},
            {"Type": "C", "Duration": "15"},
            {"Type": "Am", "Duration": "15"},
            {"Type": "Em", "Duration": "15"},
            {"Type": "Dm", "Duration": "15"}
        ]
        
        filepath = os.path.join(self.csv_dir, "default_chords.csv")
        with open(filepath, 'w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=["Type", "Duration"])
            writer.writeheader()
            writer.writerows(default_chords)
        
        return filepath
    
    def create_new_csv(self):
        """Creates a new CSV file with a user-specified name"""
        filename = simpledialog.askstring("New Practice File", "Enter file name (without .csv):")
        if filename:
            if not filename.endswith('.csv'):
                filename += '.csv'
            
            filepath = os.path.join(self.csv_dir, filename)
            
            # Check if file already exists
            if os.path.exists(filepath):
                if not messagebox.askyesno("File Exists", "File already exists. Overwrite?"):
                    return None
            
            try:
                with open(filepath, 'w', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(["Type", "Duration"])  # Write header
                return filepath
            except Exception as e:
                messagebox.showerror("Error", f"Could not create file: {e}")
                return None
        return None
    
    def delete_csv(self, filename):
        if filename:
            try:
                os.remove(filename)
                return True
            except Exception as e:
                messagebox.showerror("Error", f"Could not delete file: {e}")
                return False
        return False
    
    def select_csv(self):
        # Create selection dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Practice File")
        dialog.geometry("400x300")
        dialog.configure(bg='#1a1a2e')
        
        # List available CSV files
        listbox = tk.Listbox(
            dialog,
            bg='#16213e',
            fg='white',
            selectmode=tk.SINGLE,
            font=('Roboto', 12)
        )
        listbox.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)
        
        for file in os.listdir(self.csv_dir):
            if file.endswith('.csv'):
                listbox.insert(tk.END, file)
        
        button_frame = tk.Frame(dialog, bg='#1a1a2e')
        button_frame.pack(pady=10, fill=tk.X)
        
        def select():
            selection = listbox.curselection()
            if selection:
                filename = listbox.get(selection[0])
                self.current_file = os.path.join(self.csv_dir, filename)
                dialog.destroy()
        
        def create_new():
            new_file = self.create_new_csv()
            if new_file:
                self.current_file = new_file
                dialog.destroy()
        
        def delete_selected():
            selection = listbox.curselection()
            if selection:
                filename = listbox.get(selection[0])
                filepath = os.path.join(self.csv_dir, filename)
                
                if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {filename}?"):
                    if self.delete_csv(filepath):
                        listbox.delete(selection)
                        if filepath == self.current_file:
                            self.current_file = None
        
        tk.Button(
            button_frame,
            text="Select",
            command=select,
            bg='#0f3460',
            fg='#e94560',
            font=('Roboto', 10, 'bold')
        ).pack(side=tk.LEFT, padx=10, expand=True)
        
        tk.Button(
            button_frame,
            text="Create New",
            command=create_new,
            bg='#0f3460',
            fg='#e94560',
            font=('Roboto', 10, 'bold')
        ).pack(side=tk.LEFT, padx=10, expand=True)
        
        tk.Button(
            button_frame,
            text="Delete",
            command=delete_selected,
            bg='#e94560',
            fg='white',
            font=('Roboto', 10, 'bold')
        ).pack(side=tk.LEFT, padx=10, expand=True)
        
        dialog.transient(self.root)
        dialog.grab_set()
        self.root.wait_window(dialog)
        
        return self.current_file

class GuitarChordPracticeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Guitar Practice")
        self.root.geometry("500x700")
        self.root.resizable(False, False)
        self.root.configure(bg='#1a1a2e')
        
        # Initialize all attributes
        self.start_time = None
        self.end_time = None
        self.current_note = None
        self.running = False
        self.stop_event = Event()
        self.note_data = {}
        self.notes = []
        self.global_interval = 15
        
        # Initialize CSV manager
        self.csv_manager = CSVManager(root)
        self.current_notes_file = None
        
        # Create log file path
        self.log_dir = "practice_logs"
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        self.log_file = os.path.join(self.log_dir, "session_log.csv")
        
        # Register exit handlers
        atexit.register(self.on_exit)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Create initial UI with file selection button
        self.create_initial_ui()
    
    def create_initial_ui(self):
        main_frame = tk.Frame(self.root, bg='#1a1a2e', width=460, height=660)
        main_frame.pack_propagate(0)
        main_frame.pack(expand=False, padx=20, pady=20)
        
        message_label = tk.Label(
            main_frame,
            text="No practice file selected",
            font=("Montserrat", 24, "bold"),
            bg='#1a1a2e',
            fg='#e94560'
        )
        message_label.pack(pady=(100, 20))
        
        select_file_button = tk.Button(
            main_frame,
            text="Select or Create Practice File",
            command=self.initialize_practice,
            bg='#0f3460',
            fg='#e94560',
            font=("Roboto", 14, "bold"),
            borderwidth=2,
            relief=tk.RAISED
        )
        select_file_button.pack(pady=20)
    
    def initialize_practice(self):
        self.select_practice_file()
        if self.current_notes_file:
            self.load_notes()
            # Destroy initial UI
            for widget in self.root.winfo_children():
                widget.destroy()
            # Create main practice UI
            self.create_ui()

    def select_practice_file(self):
        self.current_notes_file = self.csv_manager.select_csv()
    
    def select_practice_file(self):
        self.current_notes_file = self.csv_manager.select_csv()
        if not self.current_notes_file:
            if messagebox.askretrycancel("No File Selected", "Would you like to select a practice file?"):
                self.select_practice_file()
            else:
                self.root.destroy()
    
    def load_notes(self):
        self.note_data = {}
        try:
            with open(self.current_notes_file, 'r') as file:
                csv_reader = csv.DictReader(file)
                for row in csv_reader:
                    self.note_data[row['Type']] = row['Duration']
            self.notes = list(self.note_data.keys())
        except Exception as e:
            messagebox.showerror("Error", f"Could not load notes: {e}")
    
    def get_note_interval(self, note):
        duration = self.note_data.get(note, 'default')
        return int(duration) if duration != 'default' else self.global_interval
    
    def create_ui(self):
        main_frame = tk.Frame(self.root, bg='#1a1a2e', width=460, height=660)
        main_frame.pack_propagate(0)
        main_frame.pack(expand=False, padx=20, pady=20)
        
        self.create_notes_editor_button(main_frame)
        
        self.chord_label = tk.Label(
            main_frame, 
            text="Press Start", 
            font=("Montserrat", 48, "bold"), 
            bg='#16213e', 
            fg='#e94560',
            borderwidth=5,
            relief=tk.RAISED,
            width=10,
            height=2
        )
        self.chord_label.pack(pady=(10, 20))
        
        self.timer_label = tk.Label(
            main_frame, 
            text=f"Next in: {self.global_interval} sec", 
            font=("Roboto", 20), 
            bg='#16213e', 
            fg='#0f3460',
            width=20,
            height=2
        )
        self.timer_label.pack(pady=(0, 10))
        
        interval_frame = tk.Frame(main_frame, bg='#1a1a2e')
        interval_frame.pack(pady=(0, 10))
        
        self.interval_entry = tk.Entry(
            interval_frame, 
            width=5, 
            font=("Arial", 12),
            bg='#e94560',
            fg='white',
            justify='center'
        )
        self.interval_entry.pack(side=tk.LEFT, padx=5)
        self.interval_entry.insert(0, str(self.global_interval))
        
        tk.Label(
            interval_frame, 
            text="Global Interval (sec)", 
            bg='#1a1a2e', 
            fg='#e94560'
        ).pack(side=tk.LEFT)
        
        button_frame = tk.Frame(main_frame, bg='#1a1a2e')
        button_frame.pack(pady=(10, 20), fill=tk.X)
        
        button_style = {
            'font': ("Roboto", 12, "bold"),
            'borderwidth': 2,
            'relief': tk.RAISED,
            'width': 10
        }
        
        self.start_button = tk.Button(
            button_frame, 
            text="Start", 
            command=self.start,
            bg='#0f3460', 
            fg='#e94560',
            **button_style
        )
        self.start_button.pack(side=tk.LEFT, expand=True, padx=5)
        
        self.next_button = tk.Button(
            button_frame, 
            text="Next", 
            command=self.force_next,
            bg='#16213e', 
            fg='#0f3460',
            state=tk.DISABLED,
            **button_style
        )
        self.next_button.pack(side=tk.LEFT, expand=True, padx=5)
        
        self.stop_button = tk.Button(
            button_frame, 
            text="Stop", 
            command=self.stop,
            bg='#e94560', 
            fg='#16213e',
            **button_style
        )
        self.stop_button.pack(side=tk.LEFT, expand=True, padx=5)
        
        progress_button = tk.Button(
            main_frame, 
            text="View Progress", 
            command=self.view_progress,
            bg='#0f3460', 
            fg='#e94560',
            font=("Roboto", 12, "bold"),
            borderwidth=2,
            relief=tk.RAISED
        )
        progress_button.pack(pady=(10, 0))
        
        self.session_label = tk.Label(
            main_frame, 
            text="Session: Not Started", 
            bg='#1a1a2e', 
            fg='#0f3460',
            font=("Arial", 10)
        )
        self.session_label.pack(pady=(10, 0))
    
    def create_notes_editor_button(self, main_frame):
        button_frame = tk.Frame(main_frame, bg='#1a1a2e')
        button_frame.pack(pady=(10, 0))
        
        notes_editor_button = tk.Button(
            button_frame,
            text="Edit Current Notes",
            command=lambda: self.open_csv(self.current_notes_file),
            bg='#0f3460',
            fg='#e94560',
            font=("Roboto", 12, "bold"),
            borderwidth=2,
            relief=tk.RAISED
        )
        notes_editor_button.pack(side=tk.LEFT, padx=5)
        
        select_file_button = tk.Button(
            button_frame,
            text="Select Different File",
            command=self.change_practice_file,
            bg='#0f3460',
            fg='#e94560',
            font=("Roboto", 12, "bold"),
            borderwidth=2,
            relief=tk.RAISED
        )
        select_file_button.pack(side=tk.LEFT, padx=5)
    
    def open_csv(self, filename):
        import subprocess
        import os
        
        if not os.path.exists(filename):
            messagebox.showwarning("File Not Found", f"{filename} does not exist.")
            return
        
        subprocess.Popen(['notepad.exe', filename])
        
        # Reload notes after Notepad is closed
        self.load_notes()
    
    def change_practice_file(self):
        if self.running:
            self.stop()
        self.select_practice_file()
        if self.current_notes_file:
            self.load_notes()
            self.chord_label.config(text="Press Start")
    
    def display_random_chord(self):
        while self.running and not self.stop_event.is_set():
            self.current_note = random.choice(self.notes)
            note_interval = self.get_note_interval(self.current_note)
            
            self.chord_label.config(text=self.current_note)
            self.next_button.config(state=tk.NORMAL)
            
            for remaining in range(note_interval, 0, -1):
                if not self.running or self.stop_event.is_set():
                    break
                self.timer_label.config(text=f"Next in: {remaining} sec")
                time.sleep(1)
            
            self.stop_event.clear()
            
            if not self.running:
                break
    
    def force_next(self):
        self.stop_event.set()
    
    def view_progress(self):
        ProgressViewer(self.root, self.log_file)
    
    def on_close(self):
        if self.running:
            self.stop()
        self.root.destroy()
    
    def on_exit(self):
        if self.start_time and not self.end_time:
            self.end_time = datetime.now()
            self.save_progress(None, None)
    
    def save_progress(self, chord, interval):
        try:
            file_exists = os.path.exists(self.log_file)
            with open(self.log_file, 'a', newline='') as file:
                writer = csv.writer(file)
                if not file_exists:
                    writer.writerow(["Session Start", "Session End", "Duration (seconds)"])
                
                if self.start_time and self.end_time:
                    duration = int((self.end_time - self.start_time).total_seconds())
                    writer.writerow([
                        self.start_time.strftime('%Y-%m-%d %H:%M:%S'), 
                        self.end_time.strftime('%Y-%m-%d %H:%M:%S'),
                        duration
                    ])
        except Exception as e:
            print(f"Error saving progress: {e}")
    
    def start(self):
        if not self.running:
            try:
                new_interval = int(self.interval_entry.get())
                if new_interval > 0:
                    self.global_interval = new_interval
            except ValueError:
                pass
            
            self.start_time = datetime.now()
            self.running = True
            self.session_label.config(text=f"Session Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            
            self.thread = Thread(target=self.display_random_chord, daemon=True)
            self.thread.start()
    
    def stop(self):
        if self.running:
            self.running = False
            self.stop_event.set()
            self.end_time = datetime.now()
            
            self.save_progress(None, None)
            
            self.session_label.config(text=f"Session Ended. Total Time: {int((self.end_time - self.start_time).total_seconds())} seconds")
            
            self.chord_label.config(text="Press Start")
            self.timer_label.config(text=f"Next in: {self.global_interval} sec")
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.next_button.config(state=tk.DISABLED)

def main():
    root = tk.Tk()
    app = GuitarChordPracticeApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()