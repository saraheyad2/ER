import pygame
import random
import csv
import matplotlib.pyplot as plt
import numpy as np

print("Starting script execution...")

# Test imports
try:
    pygame.init()
    print("Pygame initialized successfully")
except Exception as e:
    print(f"Error initializing Pygame: {e}")

try:
    import matplotlib.pyplot as plt
    import numpy as np
    print("Matplotlib and NumPy imported successfully")
except Exception as e:
    print(f"Error importing Matplotlib/NumPy: {e}")

# Screen setup
try:
    WIDTH, HEIGHT = 800, 600
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Emergency Room Simulation with More Staff")
    pygame.display.flip()
    print("Pygame display set up successfully")
except Exception as e:
    print(f"Error setting up Pygame display: {e}")
    screen = None

BG_COLOR = (240, 240, 240)
BLACK = (0, 0, 0)

COLORS = {
    "Critical": (255, 0, 0),
    "Serious": (255, 165, 0),
    "Minor": (0, 200, 0)
}

font = pygame.font.SysFont(None, 24)
big_font = pygame.font.SysFont(None, 36)

waiting_area = [(100 + i * 60, 400) for i in range(10)]
doctor_positions = [(300, 150), (400, 150), (500, 150), (600, 150)]  # Added positions for 4 doctors
nurse_positions = [(100, 150), (150, 150)]  # Added position for second nurse
NUM_DOCTORS = 4  # Increased to 4 doctors
NUM_NURSES = 2  # Increased to 2 nurses

FPS = 60
SIMULATION_SPEED = 1 / 10
clock = pygame.time.Clock()

patients = []
doctors = [None for _ in range(NUM_DOCTORS)]
waiting_times = []
patient_data = []
queue_sizes = []
next_arrival = 0

class Patient:
    def __init__(self, pid, severity, arrival_time):
        self.id = pid
        self.severity = severity
        self.color = COLORS[severity]
        self.state = "arrived"
        # Registration time halved with 2 nurses: 4–6 minutes
        self.registration_time = random.uniform(4, 6)
        base_times = {"Critical": 60, "Serious": 30, "Minor": 15}
        self.treatment_time = min(max(random.uniform(base_times[severity] * 0.8, base_times[severity] * 1.2), 1), 100)
        self.timer = self.registration_time
        self.position = (nurse_positions[pid % NUM_NURSES][0] + random.randint(-10, 10), nurse_positions[pid % NUM_NURSES][1] + random.randint(-10, 10))
        self.arrival_time = arrival_time
        self.start_treatment_time = None
        self.reg_start = arrival_time
        self.reg_end = None
        self.treat_start = None
        self.treat_end = None
        self.waiting_time = None
        #print(f"Patient P{self.id} created: Reg Time={self.registration_time:.2f}, Treat Time={self.treatment_time:.2f}")

def add_patient(pid, current_minute):
    severity = random.choices(["Critical", "Serious", "Minor"], weights=[0.2, 0.3, 0.5])[0]
    patient = Patient(pid, severity, current_minute)
    patients.append(patient)
    patient_data.append(patient)

def process_registration(current_time):
    for p in patients:
        if p.state == "arrived":
            p.timer -= SIMULATION_SPEED
            if p.timer <= 0:
                p.state = "waiting"
                p.reg_end = current_time
                p.timer = p.treatment_time
                p.position = waiting_area[len([x for x in patients if x.state == "waiting"]) % len(waiting_area)]
                #print(f"P{p.id} registration done at {current_time:.2f}, starting treatment timer: {p.timer:.2f}")

def assign_doctors(current_time):
    for i in range(NUM_DOCTORS):
        if doctors[i] is None:
            for p in sorted(patients, key=lambda x: {"Critical": 1, "Serious": 2, "Minor": 3}[x.severity]):
                if p.state == "waiting":
                    p.state = "being treated"
                    p.treat_start = current_time
                    p.start_treatment_time = current_time
                    p.waiting_time = current_time - p.arrival_time
                    waiting_times.append(p.waiting_time)
                    p.position = doctor_positions[i]
                    doctors[i] = p
                    #print(f"P{p.id} assigned to Doctor {i+1} at {current_time:.2f}, waiting time: {p.waiting_time:.2f}, treat time: {p.treatment_time:.2f}")
                    break

def update_treatment(current_time):
    for i in range(NUM_DOCTORS):
        p = doctors[i]
        if p:
            p.timer -= SIMULATION_SPEED
            #print(f"P{p.id} treatment timer at {current_time:.2f}: {p.timer:.2f}")
            if p.timer <= 0:
                p.state = "done"
                p.treat_end = current_time
                doctors[i] = None
                #print(f"P{p.id} finished treatment at {current_time:.2f}, total treat time: {p.treatment_time:.2f}")

def draw_scene(minute, final=False):
    if screen is None:
        #print("Skipping draw_scene: Pygame display not initialized")
        return

    try:
        screen.fill(BG_COLOR)

        title = big_font.render("Emergency Room Simulation", True, BLACK)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 20))

        for i, pos in enumerate(nurse_positions):
            pygame.draw.rect(screen, BLACK, (pos[0]-30, pos[1]-30, 60, 60), 2)
            nurse_label = font.render(f"Nurse {i+1}", True, BLACK)
            screen.blit(nurse_label, (pos[0] - 20, pos[1] + 35))

        for i, pos in enumerate(doctor_positions):
            pygame.draw.rect(screen, BLACK, (pos[0]-30, pos[1]-30, 60, 60), 2)
            d_label = font.render(f"Doctor {i+1}", True, BLACK)
            screen.blit(d_label, (pos[0] - 35, pos[1] + 35))

        for p in patients:
            if p.state != "done":
                pygame.draw.circle(screen, p.color, p.position, 20)
            label = font.render(f"P{p.id}", True, BLACK)
            screen.blit(label, (p.position[0] - 10, p.position[1] - 10))

        avg_wait = sum(waiting_times) / len(waiting_times) if waiting_times else 0
        treated_count = len([p for p in patients if p.state == "done"])
        status = font.render(f"Time: {minute:.2f} min | Patients: {len(patients)} | Treated: {treated_count} | Avg Wait: {avg_wait:.2f} min", True, BLACK)
        screen.blit(status, (20, HEIGHT - 30))

        if final:
            done_msg = big_font.render("Simulation Complete - Press any key to exit", True, BLACK)
            screen.blit(done_msg, (WIDTH // 2 - done_msg.get_width() // 2, HEIGHT // 2 + 30))

        pygame.display.flip()
        #print(f"Drew scene at minute {minute:.2f}")
    except Exception as e:
        print(f"Error in draw_scene: {e}")

def save_results():
    #print("Saving simulation results...")
    try:
        with open("simulation_results_with_more_staff.csv", mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Patient ID", "Arrival Time", "Registration Start", "Registration End", "Treatment Start", "Treatment End", "Waiting Time"])
            for patient in patient_data:
                writer.writerow([
                    patient.id,
                    patient.arrival_time,
                    patient.reg_start,
                    patient.reg_end if patient.reg_end else "",
                    patient.treat_start if patient.treat_start else "",
                    patient.treat_end if patient.treat_end else "",
                    patient.waiting_time if patient.waiting_time else ""
                ])
        print("Saved simulation_results_with_more_staff.csv")
    except Exception as e:
        print(f"Error saving simulation_results_with_more_staff.csv: {e}")

    try:
        with open("treatment_times_with_more_staff.csv", mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Patient ID", "Severity", "Registration Time", "Treatment Time"])
            for patient in patient_data:
                writer.writerow([
                    patient.id,
                    patient.severity,
                    f"{patient.registration_time:.2f}",
                    f"{patient.treatment_time:.2f}"
                ])
        print("Saved treatment_times_with_more_staff.csv")
    except Exception as e:
        print(f"Error saving treatment_times_with_more_staff.csv: {e}")

def plot_results():
    #print("Generating plots...")
    try:
        patient_ids = [p.id for p in patient_data if p.waiting_time is not None]
        waiting_times_plot = [p.waiting_time for p in patient_data if p.waiting_time is not None]
        plt.figure(figsize=(10, 6))
        plt.bar(patient_ids, waiting_times_plot, color='blue')
        plt.title('Waiting Time per Patient')
        plt.xlabel('Patient ID')
        plt.ylabel('Waiting Time (minutes)')
        plt.grid(True, axis='y')
        plt.savefig('waiting_times_bar_with_more_staff.png')
        plt.close()
        print("Saved waiting_times_bar_with_more_staff.png")
    except Exception as e:
        print(f"Error generating waiting_times_bar_with_more_staff.png: {e}")

    try:
        plt.figure(figsize=(10, 6))
        plt.hist(waiting_times_plot, bins=10, color='green', edgecolor='black')
        plt.title('Distribution of Waiting Times')
        plt.xlabel('Waiting Time (minutes)')
        plt.ylabel('Frequency')
        plt.grid(True)
        plt.savefig('waiting_times_histogram_with_more_staff.png')
        plt.close()
        print("Saved waiting_times_histogram_with_more_staff.png")
    except Exception as e:
        print(f"Error generating waiting_times_histogram_with_more_staff.png: {e}")

    try:
        if queue_sizes:
            times, sizes = zip(*queue_sizes)
            plt.figure(figsize=(10, 6))
            plt.plot(times, sizes, color='purple', label='Queue Size')
            plt.title('Queue Size Over Time')
            plt.xlabel('Time (minutes)')
            plt.ylabel('Number of Patients in Queue')
            plt.grid(True)
            plt.legend()
            plt.savefig('queue_size_over_time_with_more_staff.png')
            plt.close()
            print("Saved queue_size_over_time_with_more_staff.png")
        else:
            print("No queue size data to plot")
    except Exception as e:
        print(f"Error generating queue_size_over_time_with_more_staff.png: {e}")

    try:
        patient_ids = [p.id for p in patient_data]
        treatment_times_plot = [p.treatment_time for p in patient_data]
        plt.figure(figsize=(10, 6))
        plt.bar(patient_ids, treatment_times_plot, color='orange')
        plt.title('Treatment Time per Patient')
        plt.xlabel('Patient ID')
        plt.ylabel('Treatment Time (minutes)')
        plt.grid(True, axis='y')
        plt.savefig('treatment_times_bar_with_more_staff.png')
        plt.close()
        print("Saved treatment_times_bar_with_more_staff.png")
    except Exception as e:
        print(f"Error generating treatment_times_bar_with_more_staff.png: {e}")

def main():
    global next_arrival
    print("Starting simulation...")
    running = True
    minute = 0
    next_pid = 1
    while running and minute < 720:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if minute >= next_arrival:
            add_patient(next_pid, minute)
            next_pid += 1
            next_arrival = minute + random.uniform(5, 10)

        process_registration(minute)
        assign_doctors(minute)
        update_treatment(minute)

        queue_size = len([p for p in patients if p.state == "waiting"])
        queue_sizes.append((minute, queue_size))

        draw_scene(minute)
        #print(f"Simulation at minute {minute:.2f}, patients: {len(patients)}, queue size: {queue_size}")

        clock.tick(FPS)
        minute += SIMULATION_SPEED

    print("Simulation complete, rendering final scene...")
    draw_scene(minute, final=True)
    
    print("\nTreatment Times for Each Patient:")
    print("Patient ID | Severity | Registration Time | Treatment Time")
    print("-" * 50)
    for patient in patient_data:
        print(f"P{patient.id:<9} | {patient.severity:<8} | {patient.registration_time:>16.2f} min | {patient.treatment_time:>14.2f} min")

    save_results()
    plot_results()

    print("Simulation finished. Waiting for key press to exit...")
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or event.type == pygame.KEYDOWN:
                waiting = False

    pygame.quit()
    print("Pygame quit. Exiting.")

if __name__ == "__main__":
    print("Entering main block...")
    main()
    print("Script execution completed.")