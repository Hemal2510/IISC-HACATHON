import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit.visualization import plot_histogram
import matplotlib.pyplot as plt

# --- 1. CONFIG ---
N_PEEKS = 20  # How many "Zeno" peeks to perform per scan

# This is our hidden "answer key" board
hidden_board = np.array([
    [0, 1, 0, 0],
    [0, 1, 0, 0],
    [0, 0, 0, 0],
    [1, 0, 0, 0]
])
TOTAL_SHIPS = np.sum(hidden_board)

# This is the board the player sees
player_board = np.array([
    ['?', '?', '?', '?'],
    ['?', '?', '?', '?'],
    ['?', '?', '?', '?'],
    ['?', '?', '?', '?']
])

# Initialize the simulator once
simulator = AerSimulator()

# --- 2. CORE QUANTUM LOGIC ---

def build_zeno_circuit(n_peeks, is_ship):
    """Builds the Zeno scan circuit for a 'ship' or 'dud' square."""
    
    # Use a tiny angle for our "weak" H-gates
    theta = np.pi / (2 * n_peeks)

    if is_ship:
        # "Live Bomb" circuit: 2 qubits (probe + ship)
        # This loop "freezes" the state at |00>
        qc = QuantumCircuit(2, 2)
        for _ in range(n_peeks):
            qc.ry(theta, 0)
            qc.cx(0, 1)
            qc.ry(-theta, 0)
        qc.measure([0, 1], [0, 1])
    else:
        # "Dud Bomb" circuit: 1 qubit (probe only)
        # Rotations cancel out, state stays |0>
        qc = QuantumCircuit(1, 1)
        for _ in range(n_peeks):
            qc.ry(theta, 0)
            qc.ry(-theta, 0)
        qc.measure(0, 0)
            
    return qc

# --- 3. HELPER FUNCTIONS ---

def print_board(board):
    """Simple helper to print the board nicely."""
    print("\n  A B C D")
    for i, row in enumerate(board):
        print(f"{i+1} {' '.join(row)}")
    print("")

def parse_input(user_in):
    """Converts 'B3' into array indices (2, 1)."""
    try:
        col = ord(user_in[0].upper()) - ord('A')
        row = int(user_in[1]) - 1
        if not (0 <= row < 4 and 0 <= col < 4):
            raise IndexError()
        return row, col
    except:
        print("Invalid input! Use 'A1', 'B4' format.")
        return None, None

# --- 4. "PROOF" FUNCTION (FOR PDF REPORT) ---

def show_histograms(n_peeks):
    """Generates and saves the histograms for the report."""
    print("="*30)
    print(f"RUNNING SIMULATION PROOF (N={n_peeks})...")
    print("="*30)
    
    # 1. Empty Square
    dud_circuit = build_zeno_circuit(n_peeks, is_ship=False)
    compiled_dud = transpile(dud_circuit, simulator)
    dud_counts = simulator.run(compiled_dud, shots=1024).result().get_counts()
    
    print("Result 1: Empty water. Expect: {'0': 1024}")
    plot_histogram(dud_counts, title=f"Empty Square Scan (N={n_peeks})")
    plt.savefig('histogram_empty_square.png')
    plt.show()

    # 2. Ship Square
    live_circuit = build_zeno_circuit(n_peeks, is_ship=True)
    compiled_live = transpile(live_circuit, simulator)
    live_counts = simulator.run(live_circuit, shots=1024).result().get_counts()
    
    print("Result 2: Ship square. Expect: {'00': ~1024}")
    plot_histogram(live_counts, title=f"Ship Square Scan (N={n_peeks})")
    plt.savefig('histogram_ship_square.png')
    plt.show()
    
    print("\nProof complete. Starting interactive game...")
    plt.show(block=True)

# --- 5. MAIN GAME LOOP ---

def main_game():
    ships_found = 0
    ships_hit = 0

    while ships_found < TOTAL_SHIPS:
        print_board(player_board)
        print(f"Ships Found: {ships_found}/{TOTAL_SHIPS}  |  Ships Hit: {ships_hit}")
        
        user_input = input("Enter square to scan (e.g., 'A1'): ")
        row, col = parse_input(user_in=user_input)
        
        if row is None or player_board[row, col] != '?':
            print("Invalid or already-scanned square.")
            continue

        # Check the answer key to know which circuit to build
        is_ship = (hidden_board[row, col] == 1)
        qc = build_zeno_circuit(N_PEEKS, is_ship)
        
        print(f"\n--- Scanning ({user_input.upper()})... ---")
        
        # Run a single shot of the correct circuit
        compiled_circuit = transpile(qc, simulator)
        measurement = simulator.run(compiled_circuit, shots=1).result().get_counts().popitem()[0] 
        
        # Translate the quantum result into a game move
        if is_ship:
            if measurement == '00':
                print("RESULT: '00' -> SHIP DETECTED! (Safe)")
                player_board[row, col] = 'S'
                ships_found += 1
            elif measurement == '01' or measurement == '11':
                print(f"RESULT: '{measurement}' -> KABOOM! You hit the ship!")
                player_board[row, col] = 'X'
                ships_found += 1
                ships_hit += 1
            else:
                print(f"RESULT: '{measurement}' -> Scan glitch.")
        
        else:
            if measurement == '0':
                print("RESULT: '0' -> Empty water.")
                player_board[row, col] = 'O'
            else:
                print(f"RESULT: '{measurement}' -> Scan glitch.")

    print("\n--- GAME OVER ---")
    print_board(player_board)
    print(f"You found all {ships_found} ships! You hit {ships_hit} of them.")
    print(f"Your 'Stealth' Score: {ships_found - ships_hit}")
    print("="*19)

# --- 6. SCRIPT ENTRY POINT ---
if __name__ == "__main__":
    # To generate plots for your report, uncomment the next line
    # show_histograms(N_PEEKS)
    
    # To play the game immediately
    main_game()
