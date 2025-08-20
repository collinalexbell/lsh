from pymycobot import MyCobot320
import time
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
import keyboard

# Initialize Rich Console
console = Console()

# Initialize MyCobot320
mc = MyCobot320("/dev/ttyAMA0", 115200)

# Global variable to store recorded choreography
recorded_moves = []

# MyCobot320 joint limits (degrees)
ANGLE_LIMITS = [
    (-168, 168),  # Joint 1
    (-135, 135),  # Joint 2
    (-145, 145),  # Joint 3
    (-148, 148),  # Joint 4
    (-168, 168),  # Joint 5
    (-180, 180),  # Joint 6
]

def clamp_angles(angles):
    clamped = []
    for i, angle in enumerate(angles):
        min_a, max_a = ANGLE_LIMITS[i]
        clamped.append(max(min(angle, max_a), min_a))
    return clamped



def demo():
    mc.power_on()
    console.print("[bold green]Running demo...[/bold green]")
    console.print(mc.get_angles())
    extend()
    time.sleep(2)
    #wave()
    time.sleep(2)
    home()
    time.sleep(2)
    mc.power_off()
    console.print("[bold cyan]Demo complete![/bold cyan]")

def home():
    mc.send_angles([7.11, -135, 142.91, 36.56, 83.67, -0.79], 100)

def extend():
    mc.send_angles([0, 0, 0, 0, 0, 0], 100)

def wave():
    angles = mc.get_angles()
    move_size = 30
    for i in range(3):
        if i % 2 == 0:
            angles[i] += move_size
        else:
            angles[i] -= move_size
    mc.send_angles(angles, 100)
    time.sleep(0.6)
    for i in range(3):
        if i % 2 == 0:
            angles[i] -= move_size * 2
        else:
            angles[i] += move_size * 2
    mc.send_angles(angles, 100)
    time.sleep(0.6)
    for i in range(3):
        if i % 2 == 0:
            angles[i] += move_size
        else:
            angles[i] -= move_size
    mc.send_angles(angles, 100)
    time.sleep(0.6)

def record_choreography():
    global recorded_moves
    recorded_moves = []
    console.print("[bold blue]Recording choreography... Press Enter to record a position, and type 'q' then Enter to finish.[/bold blue]")
    
    mc.power_off()
    try:
        while True:
            user_input = input("Press Enter to record position or 'q' to finish: ")
            if user_input.lower() == 'q':
                console.print("[bold cyan]Recording complete![/bold cyan]")
                break
            mc.power_on()
            time.sleep(0.1)
            angles = mc.get_angles()
            recorded_moves.append(clamp_angles(angles))
            mc.power_off()
            console.print(f"[bold green]Recorded: {angles}[/bold green]")
    finally:
        mc.power_on()
        home()
        time.sleep(1)
        mc.power_off()
    return recorded_moves

def mouse_jiggler():
    console.print("[bold blue]Place the robot on the mouse, then press Enter to start recording the jiggle pattern.[/bold blue]")
    input("Press Enter to start...")
    moves = record_choreography()
    
    console.print("[bold cyan]Jiggling started! Press any key to stop.[/bold cyan]")
    mc.power_on()
    try:
        while True:
            if keyboard.is_pressed("q"):
                console.print("[bold red]Jiggling stopped![/bold red]")
                break
            for angles in moves:
                mc.send_angles(angles, 100)
                time.sleep(1)
    finally:
        mc.power_off()

def play_choreography():
    mc.power_on()
    try:
        for _, position in enumerate(recorded_moves):
            mc.send_angles(position, 100)
            time.sleep(1)
    finally:
        home()
        time.sleep(2)
        mc.power_off()

def main_menu():
    while True:
        console.clear()
        table = Table(title="MyCobot320 Command Menu")
        table.add_column("Option", justify="center", style="cyan", no_wrap=True)
        table.add_column("Action", justify="left", style="white")
        table.add_row("1", "Run Demo")
        table.add_row("2", "Record Choreography")
        table.add_row("3", "Play Choreography")
        table.add_row("4", "Mouse Jiggler")
        table.add_row("q", "Quit")
        console.print(table)

        choice = Prompt.ask("[bold yellow]Select an option[/bold yellow]")
        if choice == "1":
            demo()
        elif choice == "2":
            global recorded_moves
            recorded_moves = record_choreography()
        elif choice == "3":
            play_choreography()
        elif choice == "4":
            mouse_jiggler()
        elif choice.lower() == "q":
            console.print("[bold red]Exiting...[/bold red]")
            break
        else:
            console.print("[bold red]Invalid option, try again.[/bold red]")

        time.sleep(2)  # Pause before refreshing menu


if __name__ == "__main__":
    main_menu()

