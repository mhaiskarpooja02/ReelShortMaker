# Main application launcher
import ttkbootstrap as tb
from ui.main_window import AppUI

def main():
    root = tb.Window(themename="darkly")
    app = AppUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
