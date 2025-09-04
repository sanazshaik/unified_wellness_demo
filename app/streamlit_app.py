import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import datetime
import io
from scipy.stats import spearmanr
import os
from groq import Groq
from auth import init_db, add_user, verify_password, get_user_profile
import sqlite3
import qrcode
import pyotp
from data_unify import load_and_merge
from insights import compute_correlations, generate_narrative
from anomaly import zscore_anomalies
import requests

# Page Title
st.set_page_config(page_title="Unified Wellness (Demo)", layout="wide")

# ---------------------------
# Load All Data Function
# ---------------------------
def load_all_data():
        sleep = pd.read_csv("data/sample_sleep.csv", parse_dates=['date']) # Loads in the data from imported csv's
        act = pd.read_csv("data/sample_activity.csv", parse_dates=['date'])
        nut = pd.read_csv("data/sample_nutrition.csv", parse_dates=['date'])
        bio = pd.read_csv("data/sample_biometrics.csv", parse_dates=['date'])
        return load_and_merge("data/sample_sleep.csv", 
                            "data/sample_activity.csv", 
                            "data/sample_nutrition.csv", 
                            "data/sample_biometrics.csv")

# ---------------------------
# FitBit OAuth Function
# ---------------------------

FITBIT_BASE_URL = "https://api.fitbit.com/1/user/-" # Fitbit API base URL

def get_fitbit_data(endpoint, access_token):
    """
    Fetch data from Fitbit API.
    endpoint: str, e.g. '/activities/date/today.json'
    access_token: str, user OAuth2 token
    """
    headers = {"Authorization": f"Bearer {access_token}"}
    url = FITBIT_BASE_URL + endpoint
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Fitbit API error {response.status_code}: {response.text}")
        return None


# ---------------------------
# GROQ AI Function
# ---------------------------
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
def ai_chatbot(df):
    df = load_all_data()

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    user_input = st.text_input("Ask me anything about your wellness data or general health:")

    if st.button("Send") and user_input:
        st.session_state["chat_history"].append({"role": "user", "content": user_input})

        # Grabs a summary of your recent data
        summary = {}
        if "calories" in df: summary["calories"] = df["calories"].dropna().tail(7).mean()
        if "sleep_hours" in df: summary["sleep_hours"] = df["sleep_hours"].dropna().tail(7).mean()
        if "steps" in df: summary["steps"] = df["steps"].dropna().tail(7).mean()
        if "water_oz" in df: summary["water_oz"] = df["water_oz"].dropna().tail(7).mean()

        # Creates a prompt for LLM behavior
        system_prompt = f"""
        You are a friendly AI wellness coach. The user’s 7-day averages are:
        {summary}.
        - Give practical, supportive insights.
        - Reference their numbers when helpful.
        - Reference their name
        """

        # Grabs Groq API Key
        client = Groq(api_key=os.environ["GROQ_API_KEY"])

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant", # recent version
            messages=[
                {"role": "system", "content": system_prompt},
                *st.session_state["chat_history"]
            ]
        )

        reply = response.choices[0].message.content
        st.session_state["chat_history"].append({"role": "assistant", "content": reply})

    # response state
    for msg in st.session_state["chat_history"]:
        if msg["role"] == "user":
            st.markdown(f"**You:** {msg['content']}")
        else:
            st.markdown(f"**Coach:** {msg['content']}")


# ---------------------------
# Login function
# ---------------------------
def login():
    st.title("Unified Wellness Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if "step" not in st.session_state:
        st.session_state["step"] = "password"

    # Takes in username and password
    if st.session_state["step"] == "password":
        if st.button("Login"):
            if verify_password(username, password):  # checks password from DB
                st.success("Password verified. Scan the QR code below with Google Authenticator.")

                # Create user's OTP secret
                conn = sqlite3.connect("users.db")
                c = conn.cursor()
                c.execute("SELECT otp_secret FROM users WHERE username=?", (username,))
                row = c.fetchone()

                if row and row[0]:
                    otp_secret = row[0]
                else:
                    otp_secret = pyotp.random_base32()
                    c.execute("UPDATE users SET otp_secret=? WHERE username=?", (otp_secret, username))
                    conn.commit()

                conn.close()

                # Generates a QR code for user to scan
                totp = pyotp.TOTP(otp_secret)
                otp_uri = totp.provisioning_uri(name=username, issuer_name="Unified Wellness")
                qr = qrcode.make(otp_uri)
                buf = io.BytesIO()
                qr.save(buf, format="PNG")
                st.image(buf.getvalue(), caption="Scan this QR code with Google Authenticator")

                # Save secret key in session for OTP
                st.session_state["otp_secret"] = otp_secret
                st.session_state["user"] = username
                st.session_state["step"] = "otp"
            else:
                st.error("Invalid username or password.") 

    # Checks correct OTP
    if st.session_state["step"] == "otp":
        otp_code = st.text_input("Enter 6-digit code from Google Authenticator")

        if st.button("Verify Code"):
            totp = pyotp.TOTP(st.session_state["otp_secret"])
            if totp.verify(otp_code):
                st.success("Login successful!")
                st.session_state["logged_in"] = True
                st.session_state["page"] = "Dashboard" # Redirect to dashboard
                st.rerun()
            else:
                st.error("Invalid code. Please try again.") # # If OTP fails or new one generates


    # Redirect to create an account
    st.markdown("---")
    if st.button("Don't have an account? Create one"):
        st.session_state["page"] = "Register"
        st.rerun()

# ---------------------------
# Register function
# ---------------------------
def register():
    st.title("Create Your Account")

    # Input user details
    new_user = st.text_input("Choose a username")
    new_pass = st.text_input("Choose a password", type="password")
    new_email = st.text_input("Your email (optional)")

    new_age = st.number_input("Age", min_value=10, max_value=120, step=1)
    new_height = st.number_input("Height (inches)", min_value=36, max_value=96, step=1)
    new_weight = st.number_input("Weight (lbs)", min_value=50, max_value=600, step=1)
    new_devices = st.multiselect(
        "Preferred Devices",
        ["Fitbit", "Apple Health", "Google Fit", "Oura", "MyFitnessPal"]
    )

    if st.button("Register"):
        if new_user and new_pass:
            otp_secret = pyotp.random_base32()  # generate secret but don't show QR yet, could be removed
            add_user(
                new_user,
                new_pass,
                new_email,
                new_age,
                new_height,
                new_weight,
                ",".join(new_devices),
                otp_secret
            )
            st.success("Account created successfully! Please log in.")
            st.session_state["page"] = "Login"
            st.rerun() # Redirect to login page
        else:
            st.error("Please enter both a username and password.")

    # Redirect to login page if account is already created
    st.markdown("---")
    if st.button("Already have an account? Log in"):
        st.session_state["page"] = "Login"
        st.rerun()


# ---------------------------
# Profile function
# ---------------------------
def profile():
    user = st.session_state.get("user", "User")
    st.title(f"{user.capitalize()}'s Profile")

    # Loads from the database
    profile_data = get_user_profile(user)

    # Default values
    if not profile_data:
        profile_data = {
            "email": f"{user}@wellnessapp.com",
            "age": "N/A",
            "height_in": "N/A",
            "weight_lb": "N/A",
            "devices": []
        }
    
    # Displays profile information and devices 
    st.subheader("Profile Information")
    st.write(f"**Email:** {profile_data.get('email', 'N/A')}")
    st.write(f"**Age:** {profile_data.get('age', 'N/A')}")
    st.write(f"**Height:** {profile_data.get('height_in', 'N/A')} in")
    st.write(f"**Weight:** {profile_data.get('weight_lb', 'N/A')} lbs")

    devices = profile_data.get("devices", [])
    if isinstance(devices, str):
        devices = devices.split(",") if devices else []
    st.write("**Preferred Devices:** " + (", ".join(devices) if devices else "N/A"))

    

   

    # Edits Profile
    st.markdown("### Update Profile")

    new_email = st.text_input("Update Email", profile_data.get("email", ""))
    new_age = st.number_input("Age", 10, 100, value=int(profile_data.get("age", 21)))
    new_height = st.number_input("Height (inches)", 48, 84, value=int(profile_data.get("height_in", 65)))
    new_weight = st.number_input("Weight (lbs)", 80, 300, value=int(profile_data.get("weight_lb", 140)))

    devices = profile_data.get("devices", "")
    if isinstance(devices, str):
        devices = devices.split(",") if devices else []

    # Display devices
    st.write("**Preferred Devices:**")
    st.write(", ".join(devices) if devices else "N/A")

    # Edit devices form (add/remove)
    preferred_devices = st.multiselect(
        "Connected Devices",
        ["Fitbit", "Apple Health", "Google Fit", "Oura", "MyFitnessPal"],
        default=devices
    )
    st.write(", ".join(preferred_devices) if preferred_devices else "None")

    # Make sures changes are saved even when page is reloaded
    if st.button("Save Changes"):
        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute('''
            UPDATE users
            SET email=?, age=?, height_in=?, weight_lb=?, devices=?
            WHERE username=?
        ''', (new_email, new_age, new_height, new_weight, ",".join(preferred_devices), user))
        conn.commit()
        conn.close()
        st.success("Profile updated!")
        st.rerun()

    st.markdown("### Your Data")

    # Load unified data 
    df = load_and_merge(
        "data/sample_sleep.csv",
        "data/sample_activity.csv",
        "data/sample_nutrition.csv",
        "data/sample_biometrics.csv"
    )
    

    # Show preview table of unified data
    st.dataframe(df.tail(14), use_container_width=True)

    # Create download button for full CSV
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    st.download_button(
        label="Download Your Unified Data (CSV)",
        data=csv_buffer.getvalue(),
        file_name="unified_wellness_data.csv",
        mime="text/csv"
    )


# Displays insights in card form (flags in color)
def display_insights(insights):
    df = load_all_data()
    st.markdown("### Your Generated Insights & Recommendations")

    # If there is not enough data
    if not insights:
        st.info("Not enough data yet for insights. Keep logging.")
        return

    # Insight category
    for line in insights:
        if "higher" in line or "elevated" in line or "X" in line:
            st.error(f"{line}")       # red card for risks
        elif "trended up" in line or "trended down" in line or "consecutive" in line:
            st.warning(f"{line}")     # yellow card for trends
        else:
            st.success(f"{line}")     # green card for helpful tips and support



# Anomaly chart
def plot_anomalies(df, column, z, flags):
    df = load_all_data()
    a = df[['date', column]].dropna()
    a['z'] = z
    a['anomaly'] = flags

    c = alt.Chart(a).mark_line().encode(
        x='date:T', y=f'{column}:Q'
    )
    points = alt.Chart(a[a['anomaly']]).mark_circle(color='red', size=80).encode(
        x='date:T', y=f'{column}:Q'
    )
    st.altair_chart(c + points, use_container_width=True)


# ---------------------------
# Dashboard function
# ---------------------------
def dashboard():
    df = load_all_data()
    user = st.session_state.get("user", "User")
    profile_data = get_user_profile(user) or {}

    # User info
    name = user.capitalize()
    weight = profile_data.get("weight_lb", None)
    height = profile_data.get("height_in", None)
    age = profile_data.get("age", "N/A")

    # Default goals
    water_goal = profile_data.get("water_goal", 70)
    sleep_goal = 8
    calorie_goal = 2000
    steps_goal = 10000

    # Casting just in case numbers don't convert from DB
    try:
        weight = float(weight) if weight not in (None, "N/A") else None
        height = float(height) if height not in (None, "N/A") else None
        age = int(age) if age not in (None, "N/A") else "N/A"
    except ValueError:
        pass

    # Load biometrics CSV
    bio = pd.read_csv("data/sample_biometrics.csv", parse_dates=["date"])
    latest_bio = bio.tail(1).iloc[0] if not bio.empty else {}
    body_fat = latest_bio.get("body_fat_pct", None)

    # BMI calculation category and color flag
    bmi = None
    bmi_status = "N/A"
    bmi_color = "white" # otherwise is the default

    if isinstance(weight, (int, float)) and isinstance(height, (int, float)) and height > 0:
        bmi = round((weight / (height * height)) * 703, 1)

        # for testing
        # bmi = 28 

        # Assigns a category and color for insight
        if bmi < 18.5:
            bmi_status = "Underweight"
            bmi_color = "orange"
        elif 18.5 <= bmi < 25:
            bmi_status = "Healthy"
            bmi_color = "lightgreen"
        elif 25 <= bmi < 30:
            bmi_status = "Overweight"
            bmi_color = "yellow"
        else:
            bmi_status = "Obese"
            bmi_color = "red"

    

    # Load activity CSV
    activity = pd.read_csv("data/sample_activity.csv", parse_dates=["date"])

    if not activity.empty:
        # Re-calculates distance (miles) and speed (mph)
        activity["distance_mi"] = activity["steps"] * 0.0004734848
        activity["speed_mph"] = activity.apply(
            lambda row: (row["distance_mi"] / (row["workout_min"] / 60))
            if row["workout_min"] > 0 else 0, axis=1
        )

        # Last 7 days averages of distance (miles) and speed (mph)
        recent = activity.tail(7)
        avg_distance = round(recent["distance_mi"].mean(), 2)
        avg_speed = round(recent["speed_mph"].mean(), 2)

        # Latest entry for activity metrics and rounds
        latest_act = activity.tail(1).iloc[0]
        activity_steps = int(latest_act["steps"])
        activity_distance = round(latest_act["distance_mi"], 2)
        activity_time = round(latest_act["workout_min"], 1)
        activity_speed = round(latest_act["speed_mph"], 2)
    else:
        avg_distance = avg_speed = activity_steps = activity_distance = activity_time = activity_speed = 0



    # Top row: Overview and Reminders
    col1, col2 = st.columns([2, 2])

    with col1:
        st.markdown("### Overview")
        today = datetime.date.today().strftime("%B %d, %Y") # displays todays date
        st.caption(f"{today}")
        st.markdown(
            f"""
            <div style="background-color:#1E1E1E; padding:20px; border-radius:12px; margin-bottom:20px; width:100%;">
                <h4 style="margin:0; color:white;">{name}</h4>
                <hr style="border: 0.5px solid #444; margin:10px 0;">
                <div style="display:flex; justify-content:space-between; font-size:20px; color:gray; text-align:center;">
                    <div style="margin-right:20px;">Weight: <b style="color:white;">{weight if weight else "N/A"} lbs</b></div>
                    <div style="margin-right:20px;">Height: <b style="color:white;">{height if height else "N/A"} in</b></div>
                    <div style="margin-right:20px;">Age: <b style="color:white;">{age}</b></div>
                    <div style="margin-right:20px;">BMI: <b style="color:white;">{bmi if bmi else "N/A"}</b>
                        <br><span style="font-size:14px; color:{bmi_color};">{bmi_status}</span></div>
                    <div>Body Fat: <b style="color:white;">{round(body_fat,1) if body_fat else "N/A"}%</b></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Reminders: create a reminder, check it off, and delete
    with col2:
        st.markdown("### Reminders")
        if "reminders" not in st.session_state:
            st.session_state["reminders"] = []
        new_reminder = st.text_input("Add a reminder")
        if st.button("Add Reminder"):
            if new_reminder.strip():
                st.session_state["reminders"].append({"text": new_reminder, "done": False})

        delete_index = None
        for i, r in enumerate(st.session_state["reminders"]):
            col_rem1, col_rem2 = st.columns([8, 1])
            with col_rem1:
                checked = st.checkbox(r["text"], value=r["done"], key=f"rem_{i}")
                st.session_state["reminders"][i]["done"] = checked
            with col_rem2:
                if st.button("X", key=f"del_{i}"):
                    delete_index = i
        if delete_index is not None:
            st.session_state["reminders"].pop(delete_index)
            st.rerun()

  # Second row: Wellness summary insight and activity metrics
    col3, col4 = st.columns([2, 2])
    with col3:
        st.markdown("### Wellness Summary")

        if not df.empty:
            recent = df.tail(7)

            # Calculate averages
            avg_sleep = recent["sleep_hours"].dropna().mean() if "sleep_hours" in recent else None
            avg_steps = recent["steps"].dropna().mean() if "steps" in recent else None
            avg_calories = recent["calories"].dropna().mean() if "calories" in recent else None
            avg_water = recent["water_oz"].dropna().mean() if "water_oz" in recent else None

            # Insight narrative
            summary_text = "Here’s your past week at a glance: "
            if avg_sleep:
                summary_text += f"you averaged {avg_sleep:.1f} hrs of sleep, "
            if avg_steps:
                summary_text += f"took around {avg_steps:.0f} steps a day, "
            if avg_calories:
                summary_text += f"burned roughly {avg_calories:.0f} calories per day, "
            if avg_water:
                summary_text += f"and drank about {avg_water:.0f} oz of water per day. "

            # Supportive statements
            if avg_sleep and avg_sleep < 7:
                summary_text += "Your sleep is a bit low — consider adjusting your bedtime. "
            if avg_steps and avg_steps > 10000:
                summary_text += "Great job staying active, you hit more than 10K steps! "
            if avg_water and avg_water < 70:
                summary_text += "Hydration is slightly below your goal, keep a water bottle nearby. "

            st.markdown(
                f"""
                <div style="background-color:#2b2b2b; padding:20px; border-radius:12px; margin-bottom:20px;">
                    <p style="color:white; font-size:16px; margin:0;">{summary_text}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.info("Not enough data yet to generate a summary. Keep logging!")

    # Grabs latest activity metrics
    with col4:
        st.markdown("### Your Recent Activity")
        st.markdown(
            f"""
            <div style="background-color:#1E1E1E; padding:20px; border-radius:12px; margin-bottom:20px; width:100%;">
                <div style="display:flex; justify-content:space-between; font-size:20px; color:gray; text-align:center;">
                    <div style="margin-right:20px;">Steps: <b style="color:white;">{activity_steps}</b></div>
                    <div style="margin-right:20px;">Distance: <b style="color:white;">{activity_distance} mi</b></div>
                    <div style="margin-right:20px;">Time: <b style="color:white;">{activity_time} min</b></div>
                    <div style="margin-right:20px;">Speed: <b style="color:white;">{activity_speed} mph</b></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
            
        )    
        # Insight
        st.caption(
            f"Over the past 7 days, you averaged around **{avg_distance} miles/day** "
            f"at an average pace of **{avg_speed} mph**."
        )
        

    
    # Sidebar file inputs (default to sample data) - potentially if you want to add your own data/csv files
    #st.sidebar.header("Data Sources")
    #sleep_file = st.sidebar.file_uploader("Sleep CSV", type=["csv"], key="sleep")
    #act_file = st.sidebar.file_uploader("Activity CSV", type=["csv"], key="act")
    #nut_file = st.sidebar.file_uploader("Nutrition CSV", type=["csv"], key="nut")
    #bio_file = st.sidebar.file_uploader("Biometrics CSV", type=["csv"], key="bio")

    #st.sidebar.markdown("### Data Sources")

    use_fitbit = st.sidebar.checkbox("Connect Fitbit (mock OAuth)") # a mock to demonstrate how Fitbit API works
    if use_fitbit:
        access_token = st.sidebar.text_input("Enter Fitbit Access Token", type="password")
        if access_token:
            today = datetime.date.today().strftime("%Y-%m-%d")
            fitbit_data = get_fitbit_data(f"/activities/date/{today}.json", access_token)
            if fitbit_data:
                steps = fitbit_data["summary"]["steps"]
                st.metric("Today's Steps (Fitbit)", steps)

    def _read_or_default(upload, default_path):
        if upload is not None:
            return pd.read_csv(upload, parse_dates=['date'])
        return pd.read_csv(default_path, parse_dates=['date'])

    df = load_all_data()

    # Load user goals from DB
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT water_goal, sleep_goal, calorie_goal, steps_goal, protein_goal, carbs_goal, fat_goal, hr_goal FROM users WHERE username=?", (st.session_state["user"],))
    row = c.fetchone()
    conn.close()

    if row:
        goals = {
            "water_oz": row[0],
            "sleep_hours": row[1],
            "calories": row[2],
            "steps": row[3],
            "protein_g": row[4],
            "carbs_g": row[5],
            "fat_g": row[6],
            "resting_hr": row[7]
        }
    else:
        goals = {"water_oz": 70, "sleep_hours": 8, "calories": 2000, "steps": 10000, "protein_g": 150, "carbs_g": 250, "fat_g": 70, "resting_hr": 65}


    st.subheader("Your Daily Average - Last 7 Days")

    col1, col2, col3, col4 = st.columns(4)
    recent = df.tail(7)   # Last 7 days

    # Water
    if "water_oz" in recent:
        avg_water = recent["water_oz"].dropna().mean()
        col1.metric("Water", f"{avg_water:.0f} oz", f"Goal: {goals['water_oz']} oz")

    # Sleep
    if "sleep_hours" in recent:
        avg_sleep = recent["sleep_hours"].dropna().mean()
        col2.metric("Sleep", f"{avg_sleep:.1f} hrs", f"Goal: {goals['sleep_hours']} hrs")

    # Calories
    if "calories" in recent:
        avg_calories = recent["calories"].dropna().mean()
        col3.metric("Calories", f"{avg_calories:.0f} kcal", f"Goal: {goals['calories']} kcal")

    # Steps
    if "steps" in recent:
        avg_steps = recent["steps"].dropna().mean()
        col4.metric("Steps", f"{avg_steps:.0f}", f"Goal: {goals['steps']}")

    # Data Visualization: chart shows the past 7 days with your nutrition/activity metrics and a red goal line
    def plot_goal_chart(df, col, goal, title, y_label, color):
        if col in df:
            recent = df[['date', col]].dropna().tail(7)

            bars = alt.Chart(recent).mark_bar(color=color).encode(
                x=alt.X("date:T", title="Date"),
                y=alt.Y(f"{col}:Q", title=y_label),
                tooltip=["date", col]
            )

            goal_line = alt.Chart(pd.DataFrame({"y": [goal]})).mark_rule(
                color="red", strokeDash=[5,3]
            ).encode(y="y:Q")

            return (bars + goal_line).properties(title=title, height=250)
        return None

    
    st.subheader(f"Past Week Snapshot")

    # Define goals
    water_goal = profile_data.get("water_goal", 70) if profile_data else 70 
    sleep_goal = 8
    calorie_goal = 2000
    steps_goal = 10000

    # Layout in 2x2 grid
    col1, col2 = st.columns(2)
    with col1:
        chart = plot_goal_chart(df, "water_oz", water_goal, "Water Intake", "Water (oz)", "#1f77b4")
        if chart: st.altair_chart(chart, use_container_width=True)

    with col2:
        chart = plot_goal_chart(df, "sleep_hours", sleep_goal, "Sleep Hours", "Sleep (hrs)", "#9467bd")
        if chart: st.altair_chart(chart, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        chart = plot_goal_chart(df, "calories", calorie_goal, "Calories", "Calories", "#ff7f0e")
        if chart: st.altair_chart(chart, use_container_width=True)

    with col4:
        chart = plot_goal_chart(df, "steps", steps_goal, "Steps", "Steps", "#2ca02c")
        if chart: st.altair_chart(chart, use_container_width=True)
    
    # Example: take the last day's nutrition/fitness data
    latest = df.tail(1).iloc[0]

    goals = st.session_state.get("goals", {
        "protein_g": 150,
        "carbs_g": 250,
        "fat_g": 70,
        "resting_hr": 65,
        "calories": 2000,
        "steps": 10000,
        "water_oz": 70,
        "sleep_hours": 8
    })

    col1, col2, col3, col4, col5 = st.columns(5)

    # Protein
    with col1:
        if "protein_g" in df:
            avg_protein = df["protein_g"].dropna().tail(7).mean()
            goal = goals.get("protein_g", 150)
            

    # Carbs
    with col2:
        if "carbs_g" in df:
            avg_carbs = df["carbs_g"].dropna().tail(7).mean()
            goal = goals.get("carbs_g", 250)
          

    # Fats
    with col3:
        if "fat_g" in df:
            avg_fats = df["fat_g"].dropna().tail(7).mean()
            goal = goals.get("fat_g", 70)
            

    # Heart Rate
    with col4:
        if "resting_hr" in df:
            avg_hr = df["resting_hr"].dropna().tail(7).mean()
            goal = goals.get("resting_hr", 65)
            

    # Energy Burn / Calories
    with col5:
        if "calories_burned" in df:
            avg_calories = df["calories_burned"].dropna().tail(7).mean()
            goal = goals.get("calories", 2000)
    


    # Define labels, units, colors, and icons
    overview_items = [
        ("protein_g", "Protein", "g", "green", ""),
        ("carbs_g", "Carbs", "g", "blue", ""),
        ("fat_g", "Fats", "g", "orange",""),
        ("resting_hr", "Heart Rate", "bpm", "red",""),
        ("calories", "Energy Burn", "kcal", "purple",""),
    ]

    st.subheader("Nutrition & Fitness Overview")

    # Display in a row
    cols = st.columns(len(overview_items))

    for col, (field, label, unit, color, icon) in zip(cols, overview_items):
        if field in latest:
            value = latest[field]
            goal = goals.get(field, value)
            pct = min(100, (value / goal) * 100)

            col.markdown(
                f"""
                <div style="background-color:#1E1E1E; border-radius:12px; padding:15px; text-align:center">
                    <div style="font-size:30px">{icon}</div>
                    <p style="margin:0; font-size:16px; color:gray">{label}</p>
                    <h3 style="margin:5px 0; color:{color}">{value:.0f} {unit}</h3>
                    <div style="background:#333; border-radius:10px; height:8px;">
                        <div style="width:{pct}%; background:{color}; height:8px; border-radius:10px"></div>
                    </div>
                    <p style="font-size:12px; color:gray">Goal: {goal} {unit}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

# ---------------------------
# Goals function
# ---------------------------
def goals():
    st.title("My Goals")

    st.subheader("Set Your Daily Goals")

    if "goals" not in st.session_state:
        st.session_state["goals"] = {
            "water_oz": 70,
            "sleep_hours": 8,
            "calories": 2000,
            "steps": 10000,
            "protein_g": 150,
            "carbs_g": 250,
            "fat_g": 70,
            "resting_hr": 65
        }

    goals = st.session_state["goals"]

    # Edit goals
    water_goal = st.number_input("Water Goal (oz)", 20, 200, goals.get("water_oz", 70))
    sleep_goal = st.number_input("Sleep Goal (hrs)", 4, 12, goals.get("sleep_hours", 8))
    cal_goal = st.number_input("Total Caloric Goal", 1000, 5000, goals.get("calories", 2000))
    step_goal = st.number_input("Steps Goal", 1000, 50000, goals.get("steps", 10000))
    protein_goal = st.number_input("Protein Goal (g)", 50, 300, goals.get("protein_g", 150))
    carbs_goal = st.number_input("Carbs Goal (g)", 50, 400, goals.get("carbs_g", 250))
    fat_goal = st.number_input("Fat Goal (g)", 20, 150, goals.get("fat_g", 70))
    hr_goal = st.number_input("Resting HR Goal (bpm)", 40, 120, goals.get("resting_hr", 65))

    if st.button("Save Goals"):
        goals_dict = {
            "water_oz": water_goal,
            "sleep_hours": sleep_goal,
            "calories": cal_goal,
            "steps": step_goal,
            "protein_g": protein_goal,
            "carbs_g": carbs_goal,
            "fat_g": fat_goal,
            "resting_hr": hr_goal
        }
        st.session_state["goals"] = goals_dict

        # Saves and connects to DB
        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("""
            UPDATE users
            SET water_goal=?, sleep_goal=?, calorie_goal=?, steps_goal=?,
                protein_goal=?, carbs_goal=?, fat_goal=?, hr_goal=?
            WHERE username=?
        """, (
            goals_dict["water_oz"], goals_dict["sleep_hours"], goals_dict["calories"], goals_dict["steps"],
            goals_dict["protein_g"], goals_dict["carbs_g"], goals_dict["fat_g"], goals_dict["resting_hr"],
            st.session_state["user"]
        ))
        conn.commit()
        conn.close()

        st.success("Goals updated and saved permanently!")

# ---------------------------
# Insights_page function
# ---------------------------
def insights_page(df):
    df = load_all_data()
    st.title("Insights")

    # ========================
    # INSIGHTS SECTION
    # ========================
    corr_df = compute_correlations(df)
    insights = generate_narrative(df, corr_df)
    display_insights(insights)

    # ========================
    # ANOMALY SECTION
    # ========================
    if 'resting_hr' in df:
        st.markdown("### Heart Rate Trend")
        z, flags = zscore_anomalies(df['resting_hr'])
        plot_anomalies(df, 'resting_hr', z, flags)
    
    # Anomaly summary
    total_anomalies = int(flags.sum())
    recent_anomalies = int(flags.tail(30).sum())  # Last 30 days
    avg_hr = df['resting_hr'].mean()

    if total_anomalies == 0:
        st.success(f"Your resting HR has been stable with an average of **{avg_hr:.1f} bpm** and **no anomalies detected**.")
    else:
        st.warning(
            f"Your average resting HR is **{avg_hr:.1f} bpm**. "
            f"We detected **{total_anomalies} anomalies overall**, "
            f"with **{recent_anomalies} occurring in the last 30 days**. "
            "Most readings are stable, but the flagged points suggest occasional unusual highs or lows."
        )
    
    if not df.empty:
    # Example chart: sleep vs next-day sugar
        s = df[['date','sleep_hours','sugar_next_day']].dropna().tail(60)
        if len(s) > 10:
            base = alt.Chart(s).mark_circle(size=60).encode(
                x=alt.X('sleep_hours', title='Sleep (hours)'),
                y=alt.Y('sugar_next_day', title='Sugar Next Day (g)'),
                tooltip=['date','sleep_hours','sugar_next_day']
            )

            # Defines a healthy zone (7–9 hrs sleep, sugar 30–60g) and displays green zone
            green_zone = alt.Chart(pd.DataFrame({
                'x': [7], 'x2': [9],
                'y': [30], 'y2': [60]
            })).mark_rect(opacity=0.2, color='green').encode(
                x='x:Q', x2='x2:Q',
                y='y:Q', y2='y2:Q'
            )

            chart = base + green_zone

            st.markdown("### Sleep Impact on Your Recent Sugar Intake")
            st.altair_chart(chart.properties(height=350), use_container_width=True)

            # Calculate avg sugar inside the healthy zone
            mask = (s['sleep_hours'].between(7, 9)) & (s['sugar_next_day'].between(30, 60))
            avg_sugar = s.loc[mask, 'sugar_next_day'].mean()

            # Displays insight below chart
            if not pd.isna(avg_sugar):
                st.success(f"Your average sugar intake during well-rested days (7–9h sleep) is **{avg_sugar:.1f} g**, which is within a healthy balance.")
            else:
                st.warning("Not enough data in the healthy sleep range (7–9h) to calculate your balanced sugar intake. Keep logging!")

# ---------------------------
# Google Authenticator QR Code function
# ---------------------------
def show_qr(username, otp_secret):
    totp = pyotp.TOTP(otp_secret)
    uri = totp.provisioning_uri(name=username, issuer_name="Unified Wellness App")
    img = qrcode.make(uri)
    st.image(img, caption="Scan this QR with Google Authenticator", use_column_width=True)

# ---------------------------
# GROQ AI Chatbot function
# ---------------------------
def ai_healthbot_page(df):
    st.title("AI HealthBot")
    st.caption("Your personal AI wellness coach - Powered by Groq")

    ai_chatbot(df)  # reuse your existing chatbot function

# initializes database
init_db() 

# ---------------------------
# Main
# ---------------------------
def main():
    # Session for Login and Register pages
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if "page" not in st.session_state:
        st.session_state["page"] = "Login"

    if not st.session_state["logged_in"]:
        if st.session_state["page"] == "Login":
            login()
        elif st.session_state["page"] == "Register":
            register()
    else:
        # Shows sidebar navigation many only after login
        # Sidebar
        st.sidebar.markdown(
            """
            <style>
                .nav-button {
                    display: block;
                    padding: 10px 15px;
                    margin: 5px 0;
                    border-radius: 8px;
                    text-decoration: none;
                    font-weight: 500;
                    color: white;
                    background-color: #1E1E1E;
                    border: 1px solid #333;
                }
                .nav-button:hover {
                    background-color: #333;
                }
                .active {
                    background-color: #4CAF50 !important; /* green highlight for active tab */
                    border: 1px solid #4CAF50;
                }
            </style>
            """,
            unsafe_allow_html=True
        )

        # Table of contents
        nav_options = {
            "Dashboard": "Dashboard",
            "Profile": "Profile",
            "Goals": "My Goals",
            "Insights": "Insights",
            "AI HealthBot": "AI HealthBot"
        }

        # Stores current page in session
        if "page" not in st.session_state:
            st.session_state["page"] = "Dashboard"

        # Buttons for navigation menu
        for key, label in nav_options.items():
            if st.sidebar.button(label, key=f"nav_{key}"):
                st.session_state["page"] = key

        page = st.session_state["page"]

        if page == "Dashboard":
            dashboard()
        elif page == "Profile":
            profile()
        elif page == "Goals":
            goals()
        elif page == "Insights":
            # Use unified data
            df = load_and_merge(
                "data/sample_sleep.csv",
                "data/sample_activity.csv",
                "data/sample_nutrition.csv",
                "data/sample_biometrics.csv"
            )
            insights_page(df)
        elif page == "AI HealthBot":
            df = load_and_merge(
                "data/sample_sleep.csv",
                "data/sample_activity.csv",
                "data/sample_nutrition.csv",
                "data/sample_biometrics.csv"
            )
            ai_healthbot_page(df)

        # Log out session
        if st.session_state.get("logged_in", False):
            st.sidebar.markdown("---")
            if st.sidebar.button("Logout"):
                st.session_state.clear()
                st.session_state["logged_in"] = False
                st.session_state["page"] = "Login"
                st.rerun()


if __name__ == "__main__":
    main()