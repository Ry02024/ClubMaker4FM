import tkinter as tk
import sys
import os
import time

STATUS_FILE = "overlay_status.txt"

def update_label(label, root):
    try:
        if os.path.exists(STATUS_FILE):
            try:
                with open(STATUS_FILE, "r", encoding="utf-8") as f:
                    text = f.read().strip()
                if text == "EXIT":
                    root.destroy()
                    return
                label.config(text=text)
            except:
                pass # File access conflict likely
    except Exception as e:
        print(e)
    
    root.after(200, lambda: update_label(label, root))

def main():
    root = tk.Tk()
    root.title("ClubMaker_Overlay") # Set title for potential identification
    root.overrideredirect(True) # Frameless
    root.attributes('-topmost', True) # Always on top
    root.attributes('-alpha', 0.85) # Slight transparency
    root.configure(bg='black')

    # Dimensions
    w = 600
    h = 100
    
    # Position: Bottom Right or Top Center? User said "Pop up", usually implies center.
    # Let's put it top-center so it doesn't block the field list which is usually left/center.
    # Actually, Manage Database is usually center.
    # Let's put it at the very top of the screen.
    ws = root.winfo_screenwidth()
    hs = root.winfo_screenheight()
    x = (ws // 2) - (w // 2)
    y = 50 # 50px from top

    root.geometry(f'{w}x{h}+{x}+{y}')

    label = tk.Label(root, text="Initializing...", font=("Meiryo", 16, "bold"), fg="white", bg="black", wraplength=580)
    label.pack(expand=True, fill='both', padx=20, pady=20)

    # Initial check
    update_label(label, root)
    
    root.mainloop()

if __name__ == "__main__":
    # Clean up old status
    if os.path.exists(STATUS_FILE):
        try:
            os.remove(STATUS_FILE)
        except: pass
        
    main()
