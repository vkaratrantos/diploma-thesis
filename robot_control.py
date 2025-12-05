import time
import pigpio
from pymycobot.myarm import MyArm

# --- ΡΥΘΜΙΣΕΙΣ ΣΥΝΔΕΣΗΣ ---
# Η IP του Raspberry Pi (όπως την ορίσαμε στο καλώδιο)
PI_IP = '192.168.123.20'

# Θύρες που ανοίξαμε στο Pi
# 8888: Είναι η default θύρα του pigpio για το Gripper
# 8889: Είναι η θύρα που ορίσαμε με το socat για τον Βραχίονα
GRIPPER_PORT = 8888 
ARM_PORT = 8889

# Το Pin που σύνδεσες το Gripper στο Pi (BCM Number)
GRIPPER_PIN = 18

print(f"--- Προσπάθεια σύνδεσης στο {PI_IP} ---")

# 1. ΣΥΝΔΕΣΗ ΜΕ ΤΟ GRIPPER (μέσω δικτύου)
try:
    pi = pigpio.pi(PI_IP, GRIPPER_PORT)
    if not pi.connected:
        raise Exception("Δεν συνδέθηκε το pigpio")
    print("✅ Gripper: Συνδέθηκε!")
except Exception as e:
    print(f"❌ ΣΦΑΛΜΑ Gripper: {e}")
    print("   Στο Pi τρέξε: sudo pigpiod")
    exit()

# 2. ΣΥΝΔΕΣΗ ΜΕ ΤΟΝ ΒΡΑΧΙΟΝΑ (μέσω δικτύου)
try:
    # Η εντολή socket:// επιτρέπει στο MyArm να μιλήσει μέσω LAN
    mc = MyArm('/tmp/virtual_robot', 115200)
    time.sleep(1)
    mc.power_on()
    print("✅ Βραχίονας: Συνδέθηκε!")
except Exception as e:
    print(f"❌ ΣΦΑΛΜΑ Βραχίονα: {e}")
    print(f"   Στο Pi τρέξε την εντολή socat στην πόρτα {ARM_PORT}")
    exit()

# --- ΣΥΝΑΡΤΗΣΕΙΣ ΚΙΝΗΣΗΣ ---

def move_gripper(percentage):
    """
    percentage: 0 (Κλειστό) έως 100 (Ανοιχτό)
    """
    # Όρια παλμού για Servo (συνήθως 500-2500)
    # Αν το gripper δεν κλείνει τελείως, μείωσε το 500
    # Αν ζορίζεται ανοιχτό, μείωσε το 2500
    min_pulse = 500
    max_pulse = 2500
    
    pulse = min_pulse + (percentage / 100.0) * (max_pulse - min_pulse)
    pi.set_servo_pulsewidth(GRIPPER_PIN, pulse)
    print(f"Gripper -> {percentage}%")

def scenario():
    print("\n--- Ξεκινάει το σενάριο ---")
    
    # 1. Αρχική Θέση (Όλα μηδέν)
    print("1. Πηγαίνω Home...")
    mc.send_angles([0, 0, 0, 0, 0, 0, 0], 40)
    move_gripper(100) # Άνοιξε
    time.sleep(4)

    # 2. Κίνηση προς τα κάτω (Προσοχή μην χτυπήσει!)
    print("2. Κατεβαίνω...")
    # Γωνίες: [J1, J2, J3, J4, J5, J6, J7]
    mc.send_angles([0, -20, -30, 0, 0, 0, 0], 30)
    time.sleep(3)

    # 3. Πιάσιμο
    print("3. Κλείνω Gripper...")
    move_gripper(0) # Κλείσε
    time.sleep(1)

    # 4. Σήκωμα
    print("4. Σηκώνομαι...")
    mc.send_angles([0, 0, -20, 0, 0, 0, 0], 30)
    time.sleep(3)

    # 5. Επιστροφή
    print("5. Επιστροφή Home...")
    mc.send_angles([0, 0, 0, 0, 0, 0, 0], 40)
    move_gripper(50) # Μισάνοιχτο
    time.sleep(3)

# --- ΕΚΤΕΛΕΣΗ ---
try:
    scenario()
    print("🏁 Τέλος.")
except KeyboardInterrupt:
    print("\nΔιακοπή.")
finally:
    # Σταματάμε το σήμα στο servo για να μην ζεσταίνεται
    pi.set_servo_pulsewidth(GRIPPER_PIN, 0)
    pi.stop()
