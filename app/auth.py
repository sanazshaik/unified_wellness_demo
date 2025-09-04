import sqlite3
import pyotp

DB_PATH = "users.db"

# ---------------------------
# Initialize Database Function
# ---------------------------
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            email TEXT,
            age INTEGER,
            height_in INTEGER,
            weight_lb INTEGER,
            devices TEXT,
            water_goal INTEGER DEFAULT 70,
            sleep_goal INTEGER DEFAULT 8,
            calorie_goal INTEGER DEFAULT 2000,
            steps_goal INTEGER DEFAULT 10000,
            protein_goal INTEGER DEFAULT 150,
            carbs_goal INTEGER DEFAULT 250,
            fat_goal INTEGER DEFAULT 70,
            hr_goal INTEGER DEFAULT 65,
            otp_secret TEXT
        )
    ''')
    conn.commit()
    conn.close()

# ---------------------------
# Verify Password Function
# ---------------------------
def verify_password(username, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    if row and row[0] == password:
        return True
    return False

# ---------------------------
# Add User function
# ---------------------------
def add_user(username, password, email, age, height, weight, devices, otp_secret):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    # Generate secret for 2FA
    otp_secret = pyotp.random_base32()

    c.execute('''
        INSERT INTO users (username, password, email, age, height_in, weight_lb, devices, otp_secret)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (username, password, email, age, height, weight, devices, otp_secret))

    conn.commit()
    conn.close()

# ---------------------------
# Verify User function
# ---------------------------
def verify_user(username, password, otp_code):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT password, otp_secret FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()

    if row and row[0] == password:
        otp_secret = row[1]
        totp = pyotp.TOTP(otp_secret)
        return totp.verify(otp_code)  # check 6-digit OTP
    return False

# ---------------------------
# Get User Profile function
# ---------------------------
def get_user_profile(username):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""
        SELECT email, age, height_in, weight_lb, devices
        FROM users
        WHERE username=?
    """, (username,))
    row = c.fetchone()
    conn.close()

    if row:
        email, age, height_in, weight_lb, devices = row
        return {
            "email": email,
            "age": age,
            "height_in": height_in,
            "weight_lb": weight_lb,
            # Return as list to select multiple devices in a safe manner
            "devices": devices.split(",") if devices else []
        }
    else:
        return None
