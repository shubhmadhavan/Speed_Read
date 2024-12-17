import pyperclip
import time
import tkinter as tk
from tkinter import ttk
from tkinter import colorchooser  # Import the colorchooser module
import threading
import keyboard

# Global variables
stop_event = None
current_index = 0  # To track the word index being displayed
stop_button_press_count = 0  # To track consecutive Stop button presses
highlight_color = "#AD0321"  # Default highlight color

# Function to replace new lines with a forward slash
def process_text(text):
    text = '\n'.join([' '.join(line.strip().split()) for line in text.split('\n') if line.strip()])
    text = text.replace("\n", "\n")
    return text

# Function to reveal text word by word
def reveal_text(words, speed, label, text_widget):
    global current_index
    num_words = len(words)

    while current_index < num_words:
        if stop_event.is_set():  # Check if the thread should stop
            return
        
        # Get the current word and display it in the label
        word = words[current_index]
        label.config(text=word)
        
        # Highlight the corresponding word in the text widget based on index
        highlight_word_by_index(current_index, words, text_widget)
        
        current_index += 1
        time.sleep(speed)
    
    # Reset the index when done revealing text
    current_index = 0

# Function to highlight the word in the text widget by index
def highlight_word_by_index(index, words, text_widget):
    pos = 0  # Position tracker
    
    for i in range(index):  # Traverse through words to reach the desired word
        pos += len(words[i])
        if words[i] != "\n":  # Account for spaces except for newlines
            pos += 1

    # Calculate the start and end indices
    start_idx = f"1.0 + {pos}c"
    end_idx = f"{start_idx} + {len(words[index])}c"

    # Clear previous highlights and apply the highlight to the current word
    text_widget.tag_remove("highlight", "1.0", "end")
    text_widget.tag_add("highlight", start_idx, end_idx)
    text_widget.tag_configure("highlight", foreground=highlight_color)  # Use the global highlight color

    # Scroll the text widget to ensure the current word is visible
    text_widget.see(start_idx)

# Function to update the current speed label
def update_speed_label(speed_var, speed_label):
    speed = speed_var.get()
    words_per_second = 1 / speed
    speed_label.config(text=f"{speed:.1f} seconds per word / {words_per_second:.2f} words per second")

# Function to start the reveal process
def start_reveal_process(label, speed_var, root, text_widget, speed_label):
    global stop_event, stop_button_press_count
    stop_button_press_count = 0  # Reset stop button press count when starting
    text = pyperclip.paste().strip()  # Fetch clipboard content
    if not text:
        label.config(text="No text found in clipboard!")
        return

    text = process_text(text)  # Replace newlines with forward slashes

    # Update the text widget with the clipboard content
    text_widget.delete(1.0, "end")  # Clear previous content
    text_widget.insert("1.0", text)  # Insert the clipboard text

    # Start revealing text
    label.config(text="")  # Clear previous message
    speed = speed_var.get()  # Fetch the speed from the slider

    # If there's an existing running task, stop it
    if stop_event is not None and stop_event.is_set():
        stop_event.clear()

    # Create a new stop event to manage this thread
    stop_event = threading.Event()

    # Run the reveal in a separate thread to keep the UI responsive
    words = text.split()  # Split the text into words
    threading.Thread(target=reveal_text, args=(words, speed, label, text_widget), daemon=True).start()

    # Bring the application window to the front
    bring_window_to_front(root)
    update_speed_label(speed_var, speed_label)

# Function to stop the reveal process
def stop_reveal(label, text_widget, speed_var, speed_label):
    global stop_event, stop_button_press_count, current_index
    if stop_event is not None:
        stop_event.set()

    stop_button_press_count += 1  # Increment the stop button press count

    if stop_button_press_count == 2:  # Reset the application state
        stop_button_press_count = 0
        current_index = 0  # Reset the word index
        label.config(text="")  # Clear the label
        text_widget.delete(1.0, "end")  # Clear the text widget
        speed_var.set(0.3)  # Reset the speed slider to default
        update_speed_label(speed_var, speed_label)  # Update the speed label

# Function to bring the window to the front and set it always on top
def bring_window_to_front(root):
    root.lift()  # Bring the window to the front
    root.attributes('-topmost', True)  # Keep the window on top
    root.after(100, lambda: root.attributes('-topmost', False))  # Remove from topmost after 100ms (optional, for temporary on-top)

# Function to open the color chooser dialog
def open_color_chooser():
    global highlight_color
    color = colorchooser.askcolor(initialcolor=highlight_color)[1]  # Get the selected color (returns a hex string)
    if color:  # If a color was chosen
        highlight_color = color  # Update the global highlight color

# Main function to create the GUI
def main():
    global current_index
    root = tk.Tk()
    
    root.title("Speed Reader")
    root.geometry("600x450")
    root.iconbitmap('icon.ico')  # Replace with the path to your .ico file

    # Create a label to display the text
    label = tk.Label(root, text="", font=("Helvetica", 22), wraplength=580, justify="center")
    label.pack(pady=28)

    # Create a frame to hold the buttons (start and stop)
    button_frame = tk.Frame(root)
    button_frame.pack(pady=1)

    # Create a speed control slider
    speed_var = tk.DoubleVar(value=0.3)
    speed_label = tk.Label(root, text="")
    speed_label.pack()

    speed_slider = ttk.Scale(root, from_=0.1, to=1.5, variable=speed_var, orient="horizontal", length=500)
    speed_slider.pack(fill="x", padx=20)

    # Create a speed label to display the current speed below the slider
    speed_value_label = tk.Label(root, text="0.3 seconds per word / 3.33 words per second", font=("Helvetica", 8), fg="gray")
    speed_value_label.pack()

    # Update speed value label when slider value changes
    speed_slider.config(command=lambda val: update_speed_label(speed_var, speed_value_label))

    # Create Start and Stop buttons
    start_button = ttk.Button(
        button_frame,
        text="Start",
        command=lambda: start_reveal_process(label, speed_var, root, text_widget, speed_value_label)
    )
    start_button.pack(side="left", padx=2, ipadx=2, ipady=2)

    stop_button = ttk.Button(
        button_frame,
        text="Stop",
        command=lambda: stop_reveal(label, text_widget, speed_var, speed_value_label)
    )
    stop_button.pack(side="left", padx=2, ipadx=2, ipady=2)

    # Create a Text widget to display clipboard content and highlight words
    text_widget = tk.Text(root, wrap="word", height=10, width=70, font=("Helvetica", 12))  # Change font size as needed
    text_widget.pack(pady=20, fill="both", expand=True)


    # Add settings cogwheel icon to top right
    settings_button = ttk.Button(
        root,
        text="",
        command=open_color_chooser,
        style="TButton",  
        width=4
        
    )
    settings_button.pack(side="right", padx=10, pady=2)

    # Set up a global hotkey
    keyboard.add_hotkey(
        "ctrl+alt+shift+q",
        lambda: start_reveal_process(label, speed_var, root, text_widget, speed_value_label),
        suppress=True
    )

    # Display instructions
    instructions = tk.Label(
        root,
        text="Ctrl+Alt+Shift+Q",
        font=("Helvetica", 8),
        fg="#808080",
        anchor="e",
        justify="right"
    )
    instructions.pack(pady=2, fill="x", padx=10)

    root.mainloop()

if __name__ == "__main__":
    main()
