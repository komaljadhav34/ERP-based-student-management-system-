import os
import random
from pymongo import MongoClient
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/erp_db")
client = MongoClient(MONGO_URI)
db = client.get_database()

departments = ["CSE", "IT", "ENTC", "Mech", "Civil"]
years = ["FE", "SE", "TE", "BE"]

def seed_students():
    print("Seeding students...")
    
    # Remove old dummy students - let's be more aggressive to clear previous failed runs
    result = db.users.delete_many({
        "$or": [
            {"username": {"$regex": "^student_"}},
            {"username": {"$regex": "_[a-z]+_[a-z]+$"}} 
        ]
    })
    print(f"Removed {result.deleted_count} old dummy students.")
    
    # Expanded List of realistic names
    first_names = [
        "Aanchal", "Rohan", "Priya", "Amit", "Sneha", "Rahul", "Kavita", "Vikram", "Neha", "Suresh",
        "Anjali", "Raj", "Pooja", "Deepak", "Simran", "Arjun", "Nisha", "Karan", "Meera", "Varun",
        "Siddharth", "Aditi", "Manish", "Riya", "Akash", "Tanvi", "Rohit", "Ishita", "Nikhil", "Kritika",
        "Aarav", "Vivaan", "Aditya", "Vihaan", "Arun", "Dhruv", "Kabir", "Kian", "Reyansh", "Sai",
        "Aaradhya", "Diya", "Saanvi", "Ananya", "Kiara", "Pari", "Ridhima", "Saira", "Myra", "Amaya",
        "Aryan", "Ishaan", "Rishabh", "Viraj", "Yash", "Gaurav", "Alok", "Pranav", "Chetan", "Manoj"
    ]
    last_names = [
        "Sharma", "Verma", "Gupta", "Singh", "Patel", "Mehta", "Kumar", "Reddy", "Nair", "Joshi",
        "Malhotra", "Bhatia", "Saxena", "Iyer", "Kulkarni", "Deshmukh", "Chopra", "Jain", "Agarwal", "Rao"
    ]
    
    students = []
    
    for dept in departments:
        for year in years:
            # Ensure unique first names within a class for better variety
            # If we have enough names, sample 10 unique ones. Else allow repeats.
            if len(first_names) >= 10:
                class_fnames = random.sample(first_names, 10)
            else:
                class_fnames = [random.choice(first_names) for _ in range(10)]
                
            for i in range(1, 11): # 10 students per class
                fname = class_fnames[i-1]
                lname = random.choice(last_names)
                fullname = f"{fname} {lname}"
                
                # Username: firstname_dept_year_i (to ensure uniqueness)
                username = f"{fname.lower()}{i}_{dept.lower()}_{year.lower()}"
                
                if db.users.find_one({"username": username}):
                    continue
                    
                student = {
                    "username": username,
                    "password": generate_password_hash("pass1234"),
                    "role": "student",
                    "fullname": fullname,
                    "email": f"{username}@example.com",
                    "branch": dept,
                    "year": year,
                    "studentId": f"{dept}{year}{i:03d}"
                }
                students.append(student)
    
    if students:
        db.users.insert_many(students)
        print(f"Added {len(students)} new students with realistic names.")
    else:
        print("No new students to add.")

if __name__ == "__main__":
    seed_students()
