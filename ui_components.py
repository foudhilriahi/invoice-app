import tkinter as tk

def style_button(button):
    button.config(bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), padx=10, pady=5)
    return button

def style_label(label):
    label.config(font=("Arial", 12))
    return label

def style_text(text):
    text.config(font=("Arial", 10), wrap=tk.WORD)
    return text