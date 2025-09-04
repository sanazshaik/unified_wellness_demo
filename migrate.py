## --------------------------------------------
## Useful file for Data Migration
## --------------------------------------------
# import sqlite3

# def migrate():
#     conn = sqlite3.connect("users.db")
#     c = conn.cursor()

#     # List of new goal columns with defaults
#     goal_columns = {
#         "water_goal": 70,
#         "sleep_goal": 8,
#         "calorie_goal": 2000,
#         "steps_goal": 10000,
#         "protein_goal": 150,
#         "carbs_goal": 250,
#         "fat_goal": 70,
#         "hr_goal": 65
#     }

#     # Try to add each column if missing
#     for col, default in goal_columns.items():
#         try:
#             c.execute(f"ALTER TABLE users ADD COLUMN {col} INTEGER DEFAULT {default}")
#             print(f"Added column: {col}")
#         except sqlite3.OperationalError:
#             print(f"Column already exists: {col}")

#     conn.commit()
#     conn.close()
#     print("Migration complete!")

# if __name__ == "__main__":
#     migrate()
