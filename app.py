import tkinter as tk
import random
import time
import sqlite3
import os
import sys
from PIL import Image, ImageTk
import cairosvg
import io
import pygame
import threading
import requests
import json
import tkinter.messagebox as messagebox

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
        self.rounds = self.load_texts_from_files()
        self.text = ""
        self.start_time = None
        self.time_left = 60
        self.timer_running = False
        self.timer_thread = None
        self.user_name = ""
        self.all_scores = []
        
        # Create main frame
        main_frame = tk.Frame(root, bg="#2C3E50")
        main_frame.pack(expand=True, fill="both")

        # Create canvas with scrollbar
        self.canvas = tk.Canvas(main_frame, bg="#2C3E50", highlightthickness=0)
        self.scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#2C3E50")

        # Configure grid for centering
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        
        # Create centered frame
        self.centered_frame = tk.Frame(self.scrollable_frame, bg="#2C3E50")
        self.centered_frame.grid(row=0, column=0, sticky="nsew")
        
        # Configure canvas
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        canvas_frame = self.canvas.create_window(
            (0, 0),
            window=self.scrollable_frame,
            anchor="nw",
            width=self.root.winfo_screenwidth()
        )

        def configure_canvas(event):
            self.canvas.itemconfig(canvas_frame, width=event.width)
        self.canvas.bind('<Configure>', configure_canvas)

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Pack scrollbar and canvas
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        # Add mousewheel scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # Initialize database
        self.init_database()
        
        # Now use centered_frame instead of scrollable_frame for all widgets
        self.name_frame = tk.Frame(self.centered_frame, bg="#2C3E50")
        self.name_frame.pack(expand=True, fill="both")
        
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
        self.name_entry.focus()
        
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
        
        # Create main content frame
        self.main_content = tk.Frame(self.centered_frame, bg="#2C3E50")
        
        # Create header frame for logo and title
        header_frame = tk.Frame(self.main_content, bg="#2C3E50")
        header_frame.pack(fill=tk.X, padx=20, pady=10)

        # Configure 5 columns for finer control
        # [logo][space][title][space][empty]
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
        title_label = tk.Label(
            header_frame, 
            text="Typing Test - Round 1",
            font=("Helvetica", 24, "bold"),
            bg="#2C3E50",
            fg="#ECF0F1"
        )
        title_label.grid(row=0, column=2, pady=10)

        # Empty label for balance
        empty_label = tk.Label(header_frame, bg="#2C3E50", width=16)
        empty_label.grid(row=0, column=4, padx=(0, 40))
        
        # Add round indicator
        self.round_indicator = tk.Label(
            self.main_content,
            text="Test 1 of 3",
            font=("Helvetica", 16, "bold"),
            bg="#2C3E50",
            fg="#ECF0F1"
        )
        self.round_indicator.pack(pady=10)
        
        # Add timer label
        self.timer_label = tk.Label(
            self.main_content,
            text="Time: 60s",
            font=("Helvetica", 20, "bold"),
            bg="#2C3E50",
            fg="#ECF0F1"
        )
        self.timer_label.pack(pady=(10, 5))
        
        # Create text widget for prompt
        self.prompt_label = tk.Text(
            self.main_content,
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
            self.main_content,
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
            self.main_content,
            text="",
            font=("Helvetica", 12),
            bg="#2C3E50",
            fg="#ECF0F1",
            justify=tk.LEFT
        )
        self.result_label.pack(pady=10)
        
        # Add some vertical spacing
        tk.Label(self.main_content, height=1, bg="#2C3E50").pack()
        
        # Instructions
        tk.Label(
            self.main_content,
            text="Type the text below as fast and accurately as you can.",
            font=("Helvetica", 12),
            bg="#2C3E50",
            fg="#ECF0F1"
        ).pack(pady=5)
        
        # Custom button style
        button_style = {
            "font": ("Helvetica", 12),
            "padx": 20,
            "pady": 5,
            "border": 0,
            "cursor": "hand2",
            "borderwidth": 0,
            "relief": "flat",
            "highlightthickness": 0
        }
        
        self.reset_count = 0  # Track number of resets
        self.max_resets = 3   # Maximum allowed resets
        
        # Create a frame for buttons with rounded corners
        buttons_frame = tk.Frame(self.main_content, bg="#2C3E50")
        buttons_frame.pack(pady=20)
        
        # Create canvas-based rounded buttons
        self.next_button = tk.Canvas(
            buttons_frame,
            width=150,
            height=40,
            bg="#2C3E50",
            highlightthickness=0
        )
        self.next_button.pack(side=tk.LEFT, padx=10)
        
        self.reset_button = tk.Canvas(
            buttons_frame,
            width=150,
            height=40,
            bg="#2C3E50",
            highlightthickness=0
        )
        self.reset_button.pack(side=tk.LEFT, padx=10)
        
        # Reset counter label
        self.reset_counter_label = tk.Label(
            buttons_frame,
            text="Resets remaining: 3",
            font=("Helvetica", 12),
            bg="#2C3E50",
            fg="#ECF0F1"
        )
        self.reset_counter_label.pack(side=tk.LEFT, padx=10)
        
        # Draw rounded rectangles and text for buttons
        def create_rounded_button(canvas, text, color, command):
            canvas.delete("all")
            canvas.create_rounded_rectangle = lambda x1, y1, x2, y2, radius, **kwargs: \
                canvas.create_polygon(
                    x1+radius, y1,
                    x2-radius, y1,
                    x2, y1,
                    x2, y1+radius,
                    x2, y2-radius,
                    x2, y2,
                    x2-radius, y2,
                    x1+radius, y2,
                    x1, y2,
                    x1, y2-radius,
                    x1, y1+radius,
                    x1, y1,
                    smooth=True,
                    **kwargs
                )
            
            canvas.create_rounded_rectangle(0, 0, 150, 40, 20, fill=color, outline="")
            canvas.create_text(75, 20, text=text, fill="white", font=("Helvetica", 12))
            canvas.bind("<Button-1>", lambda e: command())
            canvas.bind("<Enter>", lambda e: canvas.configure(cursor="hand2"))
        
        # Create the buttons with their respective commands
        create_rounded_button(self.next_button, "Next Test", "#3498DB", self.next_round)
        create_rounded_button(self.reset_button, "Reset", "#E74C3C", self.reset_test)
        
        # Add some spacing before footer
        tk.Label(self.main_content, height=1, bg="#2C3E50").pack()
        
        # Create footer frame
        footer_frame = tk.Frame(self.main_content, bg="#2C3E50")
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        
        # Add footer text
        footer_text = tk.Label(
            footer_frame,
            text="Developed by Team Cybrella",
            font=("Helvetica", 10, "italic"),
            fg="#3498DB",  # Light blue color
            bg="#2C3E50",
            cursor="hand2"  # Hand cursor on hover
        )
        footer_text.pack(side=tk.BOTTOM, pady=5)
        
        # Optional: Add hover effect
        def on_enter(e):
            footer_text.config(fg="#2ECC71")  # Green on hover
            
        def on_leave(e):
            footer_text.config(fg="#3498DB")  # Back to blue
            
        footer_text.bind("<Enter>", on_enter)
        footer_text.bind("<Leave>", on_leave)
        
        # Bind the text widget update to window resize
        def on_resize(event):
            # Recalculate text widget size based on content
            self.prompt_label.config(state='normal')
            content = self.prompt_label.get(1.0, tk.END)
            self.prompt_label.delete(1.0, tk.END)
            self.prompt_label.insert(tk.END, content)
            self.prompt_label.config(state='disabled')
            
        self.root.bind('<Configure>', on_resize)
        
        # Initialize pygame mixer for sound with a small buffer
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.mixer.init()
        
        # Initialize round_scores to store all metrics
        self.round_scores = {}
        
        # Initialize the first round
        self.update_round()
    
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
        if self.start_time is None:
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
        
        # Format current round's results without separator lines
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
        
        # Show only current round score
        self.result_label.config(
            text=current_round_text,
            font=("Helvetica", 12),
            fg="#ECF0F1"
        )
        
        # Disable entry and show continue message
        self.entry.config(state='disabled')
        self.timer_label.config(
            text="Press Enter for next round",
            fg="#2ECC71"
        )
        
        # Ensure the result label is visible
        self.result_label.pack(pady=10)
        
        # Bind Enter key for next round
        self.root.bind('<Return>', self.next_round)
        self.entry.unbind('<Return>')

    def reset_test(self):
        if self.reset_count >= self.max_resets:
            # If max resets reached, move to next test
            self.next_round()
            return
        
        self.reset_count += 1
        self.reset_counter_label.config(text=f"Resets remaining: {self.max_resets - self.reset_count}")
        
        self.typed_text.set("")
        self.start_time = None
        self.timer_label.config(text="Time: 60s")
        self.result_label.config(text="")  # Clear results on reset
        self.entry.config(state='normal', bg="white")
        self.consecutive_errors = 0
        self.update_prompt_highlighting("")
    
    def next_round(self, event=None):
        if self.round_index < len(self.rounds) - 1:
            self.round_index += 1
            self.update_round()
            self.result_label.config(text="")
            # Scroll to top for next round
            self.canvas.yview_moveto(0)
        else:
            # All rounds completed - show all scores without separator lines
            all_scores_text = "\n\n".join(self.all_scores)  # Just use newlines between scores
            self.result_label.config(
                text=f"Test Completed!\n\nFinal Scores:\n\n{all_scores_text}",
                font=("Helvetica", 12),
                fg="#ECF0F1"
            )
            self.entry.config(state='disabled')
            self.timer_label.config(
                text="All tests completed!",
                fg="#2ECC71"
            )
            # Scroll to see all scores
            self.canvas.yview_moveto(1)
    
    def update_round(self):
        # Reset timer
        self.time_left = 60
        self.timer_running = False
        self.timer_label.config(text="Time: 60s", fg="#ECF0F1")
        
        # Update text for current round
        self.text = self.rounds[self.round_index]
        
        # Update round indicator
        self.round_indicator.config(text=f"Test {self.round_index + 1} of {len(self.rounds)}")
        
        # Reset test state
        self.typed_text.set("")
        self.start_time = None
        self.entry.config(state='normal')
        
        # Clear result label
        self.result_label.config(text="")
        
        # Update display
        self.update_prompt_highlighting("")
        
        # Rebind the events for the new round
        self.entry.bind("<Return>", self.calculate_results)
        self.entry.bind("<KeyRelease>", self.check_typing)
        self.root.unbind('<Return>')
        
        # Focus on entry
        self.entry.focus()
    
    def cleanup(self):
        self.timer_running = False
        if self.timer_thread:
            self.timer_thread.join(0)
        if self.typing_sound:
            self.typing_sound.stop()
        pygame.mixer.quit()

    def send_scores_to_server(self):
        try:
            # Only send if we have all scores
            if all(f'round{i+1}' in self.round_scores for i in range(3)):
                user_name = self.name_entry.get() or "Anonymous"
                
                response = requests.post(
                    "http://localhost:8000/submit-scores",
                    json={
                        "user_name": user_name,
                        "round1": self.round_scores['round1'],
                        "round2": self.round_scores['round2'],
                        "round3": self.round_scores['round3'],
                        "test_duration": 60
                    }
                )
                response.raise_for_status()
                print("Scores sent to server successfully")
                
                # Show the average scores from server response
                response_data = response.json()
                if 'average_score' in response_data:
                    result_text = (
                        f"{self.result_label.cget('text')}\n\n"
                        f"Overall Results:\n"
                        f"Average Score: {response_data['average_score']:.1f}\n"
                        f"Average WPM: {response_data['average_wpm']:.1f}\n"
                        f"Average Accuracy: {response_data['average_accuracy']:.1f}%"
                    )
                    self.update_result_text(result_text)
        except Exception as e:
            print(f"Failed to send scores to server: {e}")

    def update_result_text(self, text):
        """Helper method to update the result text widget"""
        self.result_label.config(state='normal')
        self.result_label.delete(1.0, tk.END)
        self.result_label.insert(tk.END, text)
        self.result_label.config(state='disabled')
        self.result_label.see(tk.END)  # Scroll to show latest results

    def load_texts_from_files(self):
        texts = []
        # Try to load texts from round1.txt, round2.txt, round3.txt
        for i in range(1, 4):
            try:
                with open(f'round{i}.txt', 'r', encoding='utf-8') as file:
                    text = file.read().strip()
                    texts.append(text)
            except FileNotFoundError:
                print(f"Warning: round{i}.txt not found")
                # Provide default texts in case files are missing
                default_texts = [
                    "The quick brown fox jumps over the lazy dog. This pangram contains every letter of the English alphabet at least once. Pangrams are often used to display font samples and test keyboards.",
                    "She sells seashells by the seashore. The shells she sells are surely seashells. So if she sells shells on the seashore, I'm sure she sells seashore shells.",
                    "How vexingly quick daft zebras jump! The five boxing wizards jump quickly. Pack my box with five dozen liquor jugs."
                ]
                texts.append(default_texts[i-1])
        return texts

    def start_test(self):
        self.user_name = self.name_entry.get().strip()
        if not self.user_name:
            messagebox.showwarning("Name Required", "Please enter your name to start the test.")
            return
            
        # Hide name frame and show main content
        self.name_frame.pack_forget()
        self.main_content.pack(expand=True, fill="both")
        
        # Initialize the first round
        self.update_round()

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

if __name__ == "__main__":
    root = tk.Tk()
    app = TypingTest(root)
    root.mainloop()
