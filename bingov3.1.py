import tkinter as tk
from tkinter import messagebox

achtergrond = '#ffffff'

class BingoApp:
    def __init__(self, root):
        self.root = root
        root.title("Operatorscherm")
        root.geometry("400x400")

        self.bingo_numbers = [[0 for _ in range(10)] for _ in range(9)]  # Updated range to 1-90
        self.last_numbers = []
        self.displayed_numbers = []

        self.create_bingo_grid()
        self.create_reset_button()
        self.create_undo_button()  # New

    def create_bingo_grid(self):
        number = 1
        for i in range(9):  # Updated range to 1-90
            for j in range(10):
                button = tk.Button(self.root, text=str(number),font='sans 16 bold', width=5, height=2, command=lambda number=number: self.click_number(number))
                button.grid(row=i, column=j, padx=4, pady=4,)
                self.bingo_numbers[i][j] = button
                number += 1

    def create_reset_button(self):
        reset_button = tk.Button(self.root, text="Reset", width=10, height=2, command=self.reset)
        reset_button.grid(row=10, column=1, columnspan=10, pady=20)

    # New
    def create_undo_button(self):
        undo_button = tk.Button(self.root, text="Undo", width=10, height=2, command=self.undo)
        undo_button.grid(row=10, column=0, columnspan=5, pady=20)

    # New
    def undo(self):
        if not self.last_numbers:
            messagebox.showinfo("Invalid Action", "No actions to undo.")
            return

        number = self.last_numbers.pop()
        number = self.displayed_numbers.pop()
        button = self.bingo_numbers[(number - 1) // 10][(number - 1) % 10]
        button.config(state=tk.NORMAL, bg="SystemButtonFace")
        
        self.display.update_display(self.last_numbers)
        self.display.update_last_number(self.last_numbers[-1] if self.last_numbers else "")

    def reset(self):
        confirmation = messagebox.askquestion("Confirmation", "Are you sure you want to reset the game?")
        
        if confirmation == "yes":
            self.last_numbers.clear()
            self.displayed_numbers.clear()
            
            for i in range(9):
                for j in range(10):
                    button = self.bingo_numbers[i][j]
                    button.config(state=tk.NORMAL, bg="SystemButtonFace")
            
            self.display.update_display(self.last_numbers)
            self.display.update_last_number("")

    def click_number(self, number):
        if number in self.last_numbers:
            messagebox.showinfo("Invalid Selection", "You have already selected this number.")
            return

        confirmation = messagebox.askquestion("Confirmation", f"Are you sure you want to select number {number}?")
        
        if confirmation == "yes":
            self.last_numbers.append(number)
            if len(self.last_numbers) > 5:
                self.last_numbers.pop(0)
            
            self.display.update_display(self.displayed_numbers)
            self.display.update_last_number(number)
            
            self.displayed_numbers.append(self.last_numbers[-1])
            if len(self.displayed_numbers) > 5:
                self.displayed_numbers.pop(0)
            
            # Disable the button and make it red
            button = self.bingo_numbers[(number - 1) // 10][(number - 1) % 10]
            button.config(state=tk.DISABLED, bg="red")

class LastNumbersWindow:
    def __init__(self, root, app):  # Take an extra parameter for the app
        self.root = root
        self.app = app  # Save the app as an attribute
        root.title("Projectiescherm")
        root.attributes('-fullscreen', False)  # Set the window to fullscreen
        root.geometry("{0}x{1}+0+0".format(root.winfo_screenwidth(), root.winfo_screenheight()))  # Set the geometry to fill the screen
        root.configure(bg= achtergrond)

        self.last_numbers_label = tk.Label(self.root, text="Vorige nummers:", font=("Helvetica", 48), bg= achtergrond)
        self.last_numbers_label.pack(pady=20)
        
        self.last_numbers_text = tk.Label(self.root, text="", font=("Helvetica", 96), bg= achtergrond)
        self.last_numbers_text.pack(pady=20)
        
        self.last_number_label = tk.Label(self.root, text="Nieuw nummer:", font=("Helvetica", 48), bg= achtergrond)
        self.last_number_label.pack(pady=20)
        
        self.last_number_text = tk.Label(self.root, text="", font=("Helvetica", 384, "bold"), bg= achtergrond)
        self.last_number_text.pack()

    def update_display(self, displayed_numbers):
        last_numbers_text = ", ".join(str(number) for number in displayed_numbers)
        self.last_numbers_text.config(text=last_numbers_text)

    def update_last_number(self, number):
        self.last_number_text.config(text=number)

if __name__ == "__main__":
    root = tk.Tk()
    bingo_app = BingoApp(root)
    
    last_numbers_window = tk.Toplevel(root)
    bingo_app.display = LastNumbersWindow(last_numbers_window, bingo_app)  # Pass the app to the LastNumbersWindow
    
    root.mainloop()
