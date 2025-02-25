import tkinter as tk
import time
import sqlite3
import os
import sys
from PIL import Image, ImageTk
import cairosvg
import io
import threading
import pygame
import tkinter.messagebox as messagebox
from tkinter import ttk

def load_texts_from_files():
    def resource_path(relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)
    
    texts = []
    # Try to load texts from round1.txt, round2.txt, round3.txt
    for i in range(1, 4):
        try:
            file_path = resource_path(f'round{i}.txt')
            with open(file_path, 'r', encoding='utf-8') as file:
                # Read the file and join lines with whitespace
                text = ' '.join(file.read().split())
                texts.append(text)
        except FileNotFoundError:
            print(f"Warning: round{i}.txt not found")
            # Provide a default text in case the file is missing
            texts.append("The quick brown fox jumps over the lazy dog.")
    return texts

class ResultsPage(tk.Frame):
    def __init__(self, parent, all_scores, user_name):
        super().__init__(parent, bg="#2C3E50")
        self.parent = parent
        self.all_scores = all_scores
        self.user_name = user_name
        
        # Calculate average score
        self.calculate_average_scores()
        
        # Create the results UI
        self.create_widgets()
    
    def calculate_average_scores(self):
        # Extract numeric values from score strings
        self.avg_wpm = 0
        self.avg_accuracy = 0
        self.avg_error_rate = 0
        count = 0
        
        for score_text in self.all_scores:
            try:
                lines = score_text.split('\n')
                for line in lines:
                    if "Net WPM:" in line:
                        self.avg_wpm += int(line.split(":")[1].strip())
                    elif "Word Accuracy:" in line:
                        self.avg_accuracy += float(line.split(":")[1].strip().replace('%', ''))
                    elif "Error Rate:" in line:
                        self.avg_error_rate += float(line.split(":")[1].strip().replace('%', ''))
                count += 1
            except (ValueError, IndexError) as e:
                print(f"Error parsing scores: {e}")
        
        if count > 0:
            self.avg_wpm /= count
            self.avg_accuracy /= count
            self.avg_error_rate /= count
    
    def create_widgets(self):
        # Configure the frame to expand
        self.pack(expand=True, fill="both")
        
        # Create a container frame to hold the canvas and scrollbar
        container = tk.Frame(self, bg="#2C3E50")
        container.pack(expand=True, fill="both")
        
        # Create a scrollable canvas
        self.canvas = tk.Canvas(container, bg="#2C3E50", highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        
        # Configure the canvas scrolling
        self.scrollable_frame = tk.Frame(self.canvas, bg="#2C3E50")
        
        # Create window inside canvas with fixed width
        window_id = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # Configure the canvas to use the scrollbar
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack scrollbar and canvas
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # Update the scrollregion when the size of the scrollable frame changes
        def configure_scroll_region(event):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
        self.scrollable_frame.bind("<Configure>", configure_scroll_region)
        
        # Update the canvas window when the canvas size changes
        def configure_window_size(event):
            # Set the width of the window to the width of the canvas
            self.canvas.itemconfig(window_id, width=event.width)
        
        self.canvas.bind("<Configure>", configure_window_size)
        
        # Add mousewheel scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        # Header with congratulations
        header_frame = tk.Frame(self.scrollable_frame, bg="#2C3E50")
        header_frame.pack(fill="x", padx=20, pady=30)
        
        # Congratulations label with emoji
        congrats_label = tk.Label(
            header_frame,
            text=f"🎉 Congratulations, {self.user_name}! 🎉",
            font=("Helvetica", 28, "bold"),
            bg="#2C3E50",
            fg="#ECF0F1"
        )
        congrats_label.pack(pady=10)
        
        # Subtitle
        subtitle_label = tk.Label(
            header_frame,
            text="You've completed all typing tests!",
            font=("Helvetica", 18),
            bg="#2C3E50",
            fg="#3498DB"
        )
        subtitle_label.pack(pady=5)
        
        # Add a decorative separator
        separator = ttk.Separator(self.scrollable_frame, orient='horizontal')
        separator.pack(fill='x', padx=50, pady=10)
        
        # Display average scores in a card
        avg_score_frame = tk.Frame(
            self.scrollable_frame, 
            bg="#34495E",
            bd=0,
            highlightthickness=0
        )
        avg_score_frame.pack(padx=50, pady=20, fill="x")
        
        # Add some padding inside the card
        avg_content = tk.Frame(avg_score_frame, bg="#34495E", padx=30, pady=20)
        avg_content.pack(fill="x")
        
        # Average scores header
        tk.Label(
            avg_content,
            text="📊 Your Average Performance 📊",
            font=("Helvetica", 20, "bold"),
            bg="#34495E",
            fg="#ECF0F1"
        ).pack(pady=(0, 20))
        
        # Display average scores in a grid layout
        scores_grid = tk.Frame(avg_content, bg="#34495E")
        scores_grid.pack(fill="x")
        
        # Configure grid columns
        scores_grid.columnconfigure(0, weight=1)
        scores_grid.columnconfigure(1, weight=1)
        scores_grid.columnconfigure(2, weight=1)
        
        # Score metrics with emoji indicators
        metrics = [
            ("⚡ Average WPM", f"{self.avg_wpm:.1f}"),
            ("✓ Average Accuracy", f"{self.avg_accuracy:.1f}%"),
            ("❌ Average Error Rate", f"{self.avg_error_rate:.1f}%")
        ]
        
        # Create a row for each metric with nice styling
        for i, (label_text, value_text) in enumerate(metrics):
            frame = tk.Frame(scores_grid, bg="#34495E", padx=15, pady=15)
            frame.grid(row=0, column=i, sticky="nsew")
            
            tk.Label(
                frame,
                text=label_text,
                font=("Helvetica", 16),
                bg="#34495E",
                fg="#3498DB"
            ).pack()
            
            tk.Label(
                frame,
                text=value_text,
                font=("Helvetica", 24, "bold"),
                bg="#34495E",
                fg="#2ECC71"
            ).pack(pady=10)
        
        # Add a separator
        separator2 = ttk.Separator(self.scrollable_frame, orient='horizontal')
        separator2.pack(fill='x', padx=50, pady=20)
        
        # Detailed round results
        round_results_frame = tk.Frame(self.scrollable_frame, bg="#2C3E50")
        round_results_frame.pack(fill="x", padx=50, pady=10)
        
        tk.Label(
            round_results_frame,
            text="📝 Detailed Round Results 📝",
            font=("Helvetica", 20, "bold"),
            bg="#2C3E50",
            fg="#ECF0F1"
        ).pack(pady=10)
        
        # Create a card for each round's results
        for i, score in enumerate(self.all_scores):
            round_card = tk.Frame(
                round_results_frame,
                bg="#34495E",
                bd=0,
                padx=30,
                pady=20,
                highlightthickness=0
            )
            round_card.pack(fill="x", pady=10)
            
            # Extract round number
            round_num = i + 1
            
            # Round header
            tk.Label(
                round_card,
                text=f"Round {round_num}",
                font=("Helvetica", 18, "bold"),
                bg="#34495E",
                fg="#ECF0F1"
            ).pack(anchor="w")
            
            # Format the score text
            formatted_score = self.format_score_text(score)
            
            # Score details
            tk.Label(
                round_card,
                text=formatted_score,
                font=("Helvetica", 14),
                bg="#34495E",
                fg="#ECF0F1",
                justify=tk.LEFT
            ).pack(anchor="w", pady=5)
        
        # Bottom buttons frame
        button_frame = tk.Frame(self.scrollable_frame, bg="#2C3E50")
        button_frame.pack(pady=30)
        
        # Restart button
        restart_button = tk.Button(
            button_frame,
            text="Take the Test Again",
            font=("Helvetica", 14, "bold"),
            bg="#3498DB",
            fg="#ECF0F1",
            relief=tk.FLAT,
            padx=20,
            pady=10,
            command=self.restart_test
        )
        restart_button.pack(side=tk.LEFT, padx=10)
        
        # Exit button
        exit_button = tk.Button(
            button_frame,
            text="Exit",
            font=("Helvetica", 14, "bold"),
            bg="#E74C3C",
            fg="#ECF0F1",
            relief=tk.FLAT,
            padx=20,
            pady=10,
            command=self.exit_app
        )
        exit_button.pack(side=tk.LEFT, padx=10)
        
        # Footer
        footer_frame = tk.Frame(self.scrollable_frame, bg="#2C3E50")
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=20)
        
        footer_text = tk.Label(
            footer_frame,
            text="Developed by Team Cybrella",
            font=("Helvetica", 10, "italic"),
            fg="#3498DB",
            bg="#2C3E50"
        )
        footer_text.pack()
    
    def format_score_text(self, score_text):
        # Remove the "Round X Score:" part if it exists
        lines = score_text.split('\n')
        if lines and "Round" in lines[0] and "Score" in lines[0]:
            lines = lines[1:]
        
        # Format the remaining lines
        return '\n'.join(lines)
    
    def restart_test(self):
        # Hide the results page
        self.pack_forget()
        
        # Recreate the main test UI
        self.parent.destroy_frames()
        self.parent.create_name_frame()
        self.parent.show_name_frame()
    
    def exit_app(self):
        self.master.destroy()
    
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(-1 * (event.delta // 120), "units")
class TypingTest:
    def __init__(self, root):
        self.root = root
        self.root.title("Typing Test - Cybrella Edition")
        
        # Cross-platform window maximization
        width = self.root.winfo_screenwidth()
        height = self.root.winfo_screenheight()
        self.root.geometry(f"{width}x{height}+0+0")
        
        # For Linux specifically
        try:
            self.root.attributes('-zoomed', True)
        except:
            pass  # If the attribute is not supported, use the geometry method above
        
        # Initialize variables
        self.round_index = 0
        self.rounds = load_texts_from_files()
        self.text = ""
        self.start_time = None
        self.time_left = 60
        self.timer_running = False
        self.timer_thread = None
        self.user_name = ""
        self.all_scores = []
        self.typing_sound = None
        self.consecutive_errors = 0
        
        # Create main frame
        self.main_frame = tk.Frame(root, bg="#2C3E50")
        self.main_frame.pack(expand=True, fill="both")
        
        # Initialize database
        self.init_database()
        
        # Create UI frames
        self.create_name_frame()
        
        # Create main content frame (initially hidden)
        self.create_main_content()
        
        # Show the name frame on startup
        self.show_name_frame()  # <-- Add this line
        
        # Initialize pygame mixer for sound
        pygame.mixer.init()
        
        # Initialize round_scores to store all metrics
        self.round_scores = {}
        
        # Initialize the reset count
        self.reset_count = 0
        self.max_resets = 3
    
    def init_database(self):
        try:
            # Try both database names
            for db_name in ['typing_scores.db', 'typing_test.db']:
                try:
                    conn = sqlite3.connect(db_name)
                    cursor = conn.cursor()
                    
                    # Create table if it doesn't exist
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS typing_results (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_name TEXT,
                            round_number INTEGER,
                            gross_wpm INTEGER,
                            net_wpm INTEGER,
                            accuracy REAL,
                            error_rate REAL,
                            timestamp REAL
                        )
                    ''')
                    
                    conn.commit()
                    conn.close()
                    self.db_name = db_name  # Store the successful database name
                    print(f"Successfully connected to {db_name}")
                    break
                except Exception as e:
                    print(f"Failed to connect to {db_name}: {e}")
                    continue
        except Exception as e:
            print(f"Database initialization error: {e}")
            self.db_name = 'typing_scores.db'  # Default to this if all fails
    
    def create_name_frame(self):
        # Create the name entry frame (DON'T PACK HERE)
        self.name_frame = tk.Frame(self.main_frame, bg="#2C3E50")
        
        name_label = tk.Label(
            self.name_frame,
            text="Enter your name:",
            font=("Helvetica", 20, "bold"),
            bg="#2C3E50",
            fg="#ECF0F1"
        )
        name_label.pack(pady=(100, 20))
        
        self.name_entry = tk.Entry(
            self.name_frame,
            font=("Helvetica", 16),
            width=30,
            bg="#ECF0F1",
            fg="#2C3E50",
            relief=tk.FLAT,
            bd=10,
            justify='center'
        )
        self.name_entry.pack(pady=20)
        
        self.name_entry.bind("<Return>", lambda event: self.start_test())
        
        start_button = tk.Button(
            self.name_frame,
            text="Start Test",
            font=("Helvetica", 14, "bold"),
            bg="#27AE60",
            fg="#ECF0F1",
            relief=tk.FLAT,
            bd=0,
            padx=30,
            pady=10,
            command=self.start_test
        )
        start_button.pack(pady=20)

    def show_name_frame(self):
    # Hide main content and show name frame
        if self.main_content.winfo_ismapped():
            self.main_content.pack_forget()
        self.name_frame.pack(expand=True, fill="both")
    
    def create_main_content(self):
        # Create the main content frame
        self.main_content = tk.Frame(self.main_frame, bg="#2C3E50")
        
        # Create canvas with scrollbar for better scrolling
        self.canvas = tk.Canvas(self.main_content, bg="#2C3E50", highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.main_content, orient="vertical", command=self.canvas.yview)
        
        # Create a frame inside the canvas
        self.content_frame = tk.Frame(self.canvas, bg="#2C3E50")
        
        # Configure scrolling
        self.content_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        # Create window in canvas
        content_window = self.canvas.create_window((0, 0), window=self.content_frame, anchor="nw")
        
        # Configure canvas to expand with window
        def on_canvas_configure(event):
            self.canvas.itemconfig(content_window, width=event.width)
        
        self.canvas.bind("<Configure>", on_canvas_configure)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Pack scrollbar and canvas
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # Add mousewheel scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        # Create header frame for logo and title
        header_frame = tk.Frame(self.content_frame, bg="#2C3E50")
        header_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Configure columns for header
        header_frame.grid_columnconfigure(0, weight=0)  # Logo column - fixed width
        header_frame.grid_columnconfigure(1, weight=1)  # Spacing
        header_frame.grid_columnconfigure(2, weight=0)  # Title column - fixed width
        header_frame.grid_columnconfigure(3, weight=1)  # Spacing
        header_frame.grid_columnconfigure(4, weight=0)  # Empty column - fixed width
        
        # Load and display logo
        try:
            png_data = cairosvg.svg2png(url="logo.svg", output_width=120, output_height=120)
            logo_image = Image.open(io.BytesIO(png_data))
            logo_photo = ImageTk.PhotoImage(logo_image)
            
            logo_label = tk.Label(
                header_frame,
                image=logo_photo,
                bg="#2C3E50"
            )
            logo_label.image = logo_photo
            logo_label.grid(row=0, column=0, padx=(40, 0), pady=15)
            
        except Exception as e:
            print(f"Error loading logo: {e}")
        
        # Title label centered
        self.title_label = tk.Label(
            header_frame, 
            text="Typing Test - Round 1",
            font=("Helvetica", 24, "bold"),
            bg="#2C3E50",
            fg="#ECF0F1"
        )
        self.title_label.grid(row=0, column=2, pady=10)
        
        # Empty label for balance
        empty_label = tk.Label(header_frame, bg="#2C3E50", width=16)
        empty_label.grid(row=0, column=4, padx=(0, 40))
        
        # Add round indicator
        self.round_indicator = tk.Label(
            self.content_frame,
            text="Test 1 of 3",
            font=("Helvetica", 16, "bold"),
            bg="#2C3E50",
            fg="#ECF0F1"
        )
        self.round_indicator.pack(pady=10)
        
        # Add timer label
        self.timer_label = tk.Label(
            self.content_frame,
            text="Time: 60s",
            font=("Helvetica", 20, "bold"),
            bg="#2C3E50",
            fg="#ECF0F1"
        )
        self.timer_label.pack(pady=(10, 5))
        
        # Create text widget for prompt
        self.prompt_label = tk.Text(
            self.content_frame,
            wrap=tk.WORD,
            font=("Helvetica", 18),
            bg="#34495E",
            fg="#ECF0F1",
            relief=tk.FLAT,
            state='disabled',
            height=10,
            width=100,
            padx=30,
            pady=25,
            borderwidth=0,
        )
        self.prompt_label.pack(fill=tk.BOTH, expand=True, padx=20)
        
        # Configure text tags for coloring
        self.prompt_label.tag_configure("correct", foreground="#2ECC71")
        self.prompt_label.tag_configure("incorrect", foreground="#E74C3C")
        self.prompt_label.tag_configure("default", foreground="#ECF0F1")
        
        # Create and bind the entry widget
        self.typed_text = tk.StringVar()
        self.entry = tk.Entry(
            self.content_frame,
            textvariable=self.typed_text,
            font=("Helvetica", 16),
            width=100,
            bg="#ECF0F1",
            fg="#2C3E50",
            relief=tk.FLAT,
            bd=15,
            highlightthickness=1,
            highlightbackground="#3498DB",
            highlightcolor="#3498DB",
            insertwidth=2,
            insertbackground="#2C3E50"
        )
        self.entry.pack(fill=tk.X, padx=60, pady=20)
        
        # Bind both events to the entry
        self.entry.bind("<KeyRelease>", self.check_typing)
        self.entry.bind("<Return>", self.calculate_results)
        
        # Add result label
        self.result_label = tk.Label(
            self.content_frame,
            text="",
            font=("Helvetica", 12),
            bg="#2C3E50",
            fg="#ECF0F1",
            justify=tk.LEFT
        )
        self.result_label.pack(pady=10)
        
        # Add some vertical spacing
        tk.Label(self.content_frame, height=1, bg="#2C3E50").pack()
        
        # Instructions
        tk.Label(
            self.content_frame,
            text="Type the text below as fast and accurately as you can.",
            font=("Helvetica", 12),
            bg="#2C3E50",
            fg="#ECF0F1"
        ).pack(pady=5)
        
        # Create a frame for buttons
        buttons_frame = tk.Frame(self.content_frame, bg="#2C3E50")
        buttons_frame.pack(pady=20)
        
        # Function to create styled buttons
        def create_button(parent, text, bg_color, command):
            button = tk.Button(
                parent,
                text=text,
                font=("Helvetica", 12, "bold"),
                bg=bg_color,
                fg="#FFFFFF",
                relief=tk.FLAT,
                padx=20,
                pady=8,
                bd=0,
                command=command
            )
            return button
        
        # Create buttons
        self.next_button = create_button(buttons_frame, "Next Test", "#3498DB", self.next_round)
        self.next_button.pack(side=tk.LEFT, padx=10)
        
        self.reset_button = create_button(buttons_frame, "Reset", "#E74C3C", self.reset_test)
        self.reset_button.pack(side=tk.LEFT, padx=10)
        
        # Show results button (initially hidden)
        self.results_button = create_button(buttons_frame, "Show Results 🏆", "#27AE60", self.show_results)
        
        # Reset counter label
        self.reset_counter_label = tk.Label(
            buttons_frame,
            text="Resets remaining: 3",
            font=("Helvetica", 12),
            bg="#2C3E50",
            fg="#ECF0F1"
        )
        self.reset_counter_label.pack(side=tk.LEFT, padx=10)
        
        # Add some spacing before footer
        tk.Label(self.content_frame, height=1, bg="#2C3E50").pack()
        
        # Create footer frame
        footer_frame = tk.Frame(self.content_frame, bg="#2C3E50")
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        
        # Add footer text
        footer_text = tk.Label(
            footer_frame,
            text="Developed by Team Cybrella",
            font=("Helvetica", 10, "italic"),
            fg="#3498DB",
            bg="#2C3E50",
            cursor="hand2"
        )
        footer_text.pack(side=tk.BOTTOM, pady=5)
        
        # Optional: Add hover effect
        def on_enter(e):
            footer_text.config(fg="#2ECC71")
            
        def on_leave(e):
            footer_text.config(fg="#3498DB")
            
        footer_text.bind("<Enter>", on_enter)
        footer_text.bind("<Leave>", on_leave)
    
    def init_database(self):
        try:
            # Try both database names
            for db_name in ['typing_scores.db', 'typing_test.db']:
                try:
                    conn = sqlite3.connect(db_name)
                    cursor = conn.cursor()
                    
                    # Create table if it doesn't exist
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS typing_results (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_name TEXT,
                            round_number INTEGER,
                            gross_wpm INTEGER,
                            net_wpm INTEGER,
                            accuracy REAL,
                            error_rate REAL,
                            timestamp REAL
                        )
                    ''')
                    
                    conn.commit()
                    conn.close()
                    self.db_name = db_name  # Store the successful database name
                    print(f"Successfully connected to {db_name}")
                    break
                except Exception as e:
                    print(f"Failed to connect to {db_name}: {e}")
                    continue
        except Exception as e:
            print(f"Database initialization error: {e}")
            self.db_name = 'typing_scores.db'  # Default to this if all fails
    
    def start_timer(self):
        self.timer_running = True
        self.timer_thread = threading.Thread(target=self.update_timer)
        self.timer_thread.daemon = True  # Thread will close with main program
        self.timer_thread.start()
    
    def update_timer(self):
        while self.timer_running and self.time_left > 0:
            mins, secs = divmod(self.time_left, 60)
            self.timer_label.config(text=f"Time: {mins:02d}:{secs:02d}")
            time.sleep(1)
            self.time_left -= 1
            
        if self.time_left <= 0:
            self.root.after(0, self.time_up)
    
    def time_up(self):
        if self.entry['state'] != 'disabled':  # Only if test hasn't been submitted
            self.calculate_results()
            self.timer_label.config(text="Time's up!", fg="#E74C3C")
            
            # Auto-advance to next round after a short delay
            self.root.after(2000, self.next_round)
    
    def check_typing(self, event):
        if self.start_time is None and self.typed_text.get():
            self.start_time = time.time()
            self.start_timer()
        
        typed = self.typed_text.get()
        self.update_prompt_highlighting(typed)
        
        # Auto-submit if typed length matches text length
        if len(typed) >= len(self.text):
            self.calculate_results(None)  # Pass None as event
    
    def update_prompt_highlighting(self, typed):
        self.prompt_label.config(state='normal')
        self.prompt_label.delete(1.0, tk.END)
        
        # Insert the full text first
        self.prompt_label.insert(tk.END, self.text)
        
        # Apply highlighting for each character
        for i, (typed_char, text_char) in enumerate(zip(typed, self.text)):
            start_pos = f"1.{i}"
            end_pos = f"1.{i + 1}"
            
            if typed_char == text_char:
                self.prompt_label.tag_add("correct", start_pos, end_pos)
            else:
                self.prompt_label.tag_add("incorrect", start_pos, end_pos)
        
        # Ensure text is visible
        self.prompt_label.see("1.0")
        self.prompt_label.config(state='disabled')
    
    def calculate_results(self, event=None):
        if self.start_time is None or self.entry['state'] == 'disabled':
            return
        
        # Stop the timer
        self.timer_running = False
        if self.timer_thread:
            self.timer_thread.join(0)
        
        # Calculate metrics...
        end_time = time.time()
        elapsed_time = min(end_time - self.start_time, 60)
        minutes = elapsed_time / 60
        typed = self.typed_text.get()
        
        # Calculate scores...
        typed_words = typed.split()
        correct_words = self.text.split()
        min_len = min(len(typed_words), len(correct_words))
        correct_word_count = sum(1 for i in range(min_len) if typed_words[i] == correct_words[i])
        total_words = max(len(typed_words), len(correct_words))
        word_accuracy = (correct_word_count / total_words) * 100 if total_words > 0 else 0
        
        total_keystrokes = len(typed)
        errors = sum(1 for i, char in enumerate(typed) if i < len(self.text) and char != self.text[i])
        error_percentage = (errors / total_keystrokes * 100) if total_keystrokes > 0 else 0
        
        gross_wpm = int((total_keystrokes / 5) / minutes)
        net_wpm = int(((total_keystrokes - errors) / 5) / minutes)
        
        # Update database with name and results
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            # Insert results
            cursor.execute('''
                INSERT INTO typing_results 
                (user_name, round_number, gross_wpm, net_wpm, accuracy, error_rate, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.user_name,
                self.round_index + 1,
                gross_wpm,
                net_wpm,
                word_accuracy,
                error_percentage,
                time.time()
            ))
            
            conn.commit()
            conn.close()
            print(f"Successfully saved results for {self.user_name} - Round {self.round_index + 1}")
        except Exception as e:
            print(f"Database error: {e}")
        
        # Format current round's results
        current_round_text = (
            f"Round {self.round_index + 1} Score:\n"
            f"Time: {int(elapsed_time)}s\n"
            f"Gross WPM: {gross_wpm}\n"
            f"Net WPM: {net_wpm}\n"
            f"Word Accuracy: {word_accuracy:.1f}%\n"
            f"Error Rate: {error_percentage:.1f}%"
        )
        
        # Store the score
        self.all_scores.append(current_round_text)
        
                # Update UI with results
        self.entry.config(state='disabled')
        result_text = (
            f"Gross WPM: {gross_wpm}\n"
            f"Net WPM: {net_wpm}\n"
            f"Word Accuracy: {word_accuracy:.1f}%\n"
            f"Error Rate: {error_percentage:.1f}%"
        )
        self.result_label.config(text=result_text)

        # Show appropriate buttons
        if self.round_index < len(self.rounds) - 1:
            self.next_button.pack(side=tk.LEFT, padx=10)
        else:
            self.results_button.pack(side=tk.LEFT, padx=10)
            self.next_button.pack_forget()

    def next_round(self):
        if self.round_index < len(self.rounds) - 1:
            self.round_index += 1
            self.reset_test(full_reset=False)
            self.title_label.config(text=f"Typing Test - Round {self.round_index + 1}")
            self.round_indicator.config(text=f"Test {self.round_index + 1} of 3")
        else:
            self.show_results()

    def reset_test(self, full_reset=True):
        if self.reset_count >= self.max_resets:
            messagebox.showwarning("Reset Limit", "You've used all your resets!")
            return

        if full_reset:
            self.reset_count += 1
            self.reset_counter_label.config(text=f"Resets remaining: {self.max_resets - self.reset_count}")

        # Reset test parameters
        self.start_time = None
        self.time_left = 60
        self.timer_running = False
        self.typed_text.set("")
        self.entry.config(state='normal')
        self.result_label.config(text="")
        self.prompt_label.config(state='normal')
        self.prompt_label.delete(1.0, tk.END)
        self.prompt_label.insert(tk.END, self.text)
        self.prompt_label.config(state='disabled')
        self.timer_label.config(text="Time: 60s", fg="#ECF0F1")
        
        # Reload the current round's text
        self.text = self.rounds[self.round_index]
        self.prompt_label.config(state='normal')
        self.prompt_label.delete(1.0, tk.END)
        self.prompt_label.insert(tk.END, self.text)
        self.prompt_label.config(state='disabled')
        self.entry.focus_set()

    def show_results(self):
        # Hide main content and show results page
        self.main_content.pack_forget()
        ResultsPage(self.main_frame, self.all_scores, self.user_name)

    def start_test(self):
        self.user_name = self.name_entry.get().strip()
        if not self.user_name:
            messagebox.showerror("Name Required", "Please enter your name to continue!")
            return

        self.name_frame.pack_forget()
        self.main_content.pack(expand=True, fill="both")
        self.text = self.rounds[self.round_index]
        self.prompt_label.config(state='normal')
        self.prompt_label.insert(tk.END, self.text)
        self.prompt_label.config(state='disabled')
        self.entry.focus_set()

    def destroy_frames(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(-1 * (event.delta // 120), "units")

if __name__ == "__main__":
    root = tk.Tk()
    app = TypingTest(root)
    root.mainloop()