import tkinter as tk
from tkinter import ttk, messagebox

def calculate():
    try:
        L = float(length_entry.get())

        if L <= 0:
            messagebox.showerror("Error", "Beam length must be positive.")
            return

        load_type = load_var.get()

        if load_type == "Point Load":
            P = float(load_entry.get())
            a = float(distance_entry.get())

            if a < 0 or a > L:
                messagebox.showerror("Error", "Load position must be within beam length.")
                return

            RA = P * (L - a) / L
            RB = P * a / L

        elif load_type == "UDL (Full Span)":
            w = float(load_entry.get())
            RA = RB = w * L / 2

        result_label.config(
            text=f"Reaction at A (RA): {RA:.2f}\nReaction at B (RB): {RB:.2f}"
        )

        draw_beam(L, load_type)

    except ValueError:
        messagebox.showerror("Error", "Please enter valid numbers.")


def draw_beam(L, load_type):
    canvas.delete("all")

    width = 600
    margin = 80
    beam_y = 200

    start = margin
    end = width - margin
    scale = (end - start) / L

    # Beam
    canvas.create_line(start, beam_y, end, beam_y, width=5)

    # Supports
    canvas.create_polygon(start-20, beam_y+40, start+20, beam_y+40,
                          start, beam_y, fill="gray")
    canvas.create_polygon(end-20, beam_y+40, end+20, beam_y+40,
                          end, beam_y, fill="gray")

    # Loads
    if load_type == "Point Load":
        a = float(distance_entry.get())
        x = start + a * scale

        canvas.create_line(x, beam_y-60, x, beam_y, width=2)
        canvas.create_polygon(x-7, beam_y-20, x+7, beam_y-20,
                              x, beam_y, fill="red")
        canvas.create_text(x, beam_y-75, text="P", fill="red")

    elif load_type == "UDL (Full Span)":
        for i in range(int(start), int(end), 25):
            canvas.create_line(i, beam_y-40, i, beam_y)
            canvas.create_polygon(i-5, beam_y-10,
                                  i+5, beam_y-10,
                                  i, beam_y, fill="red")

        canvas.create_text((start+end)/2, beam_y-60, text="w", fill="red")


# ================= GUI =================

root = tk.Tk()
root.title("Simply Supported Beam Reaction Calculator")
root.geometry("750x550")

title = tk.Label(root, text="Beam Support Reaction Calculator",
                 font=("Arial", 16, "bold"))
title.pack(pady=10)

# Beam length
tk.Label(root, text="Beam Length (L):").pack()
length_entry = tk.Entry(root)
length_entry.pack()

# Load type dropdown
load_var = tk.StringVar()
load_var.set("Point Load")

tk.Label(root, text="Load Type:").pack()
load_menu = ttk.Combobox(root, textvariable=load_var,
                         values=["Point Load", "UDL (Full Span)"],
                         state="readonly")
load_menu.pack()

# Load magnitude
tk.Label(root, text="Load Magnitude (P or w):").pack()
load_entry = tk.Entry(root)
load_entry.pack()

# Load distance (only for point load)
tk.Label(root, text="Distance from Left Support (a):").pack()
distance_entry = tk.Entry(root)
distance_entry.pack()

# Button
tk.Button(root, text="Calculate", command=calculate,
          bg="lightblue").pack(pady=15)

# Result
result_label = tk.Label(root, text="", font=("Arial", 12))
result_label.pack(pady=10)

# Canvas
canvas = tk.Canvas(root, width=600, height=300, bg="white")
canvas.pack(pady=20)

root.mainloop()
