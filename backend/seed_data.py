import os
import random
import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/erp_db")
client = MongoClient(MONGO_URI)
db = client.get_database()

def seed_data():
    print("Seeding additional data (Attendance, Marks, Timetable, Notifications, etc.)...")
    
    # 1. Notifications
    db.notifications.delete_many({"title": {"$regex": "^Demo"}})
    demo_notifs = [
        {"title": "Demo: Semester Exam Schedule", "message": "The final semester exams will begin on the 15th of next month. Please check the timetable.", "created_at": datetime.datetime.utcnow().isoformat()},
        {"title": "Demo: Holiday Notice", "message": "The college will remain closed on Friday due to the state holiday.", "created_at": datetime.datetime.utcnow().isoformat()},
        {"title": "Demo: Library Fine Update", "message": "Please clear all pending library fines before the end of the semester.", "created_at": datetime.datetime.utcnow().isoformat()}
    ]
    db.notifications.insert_many(demo_notifs)
    print("Added Demo Notifications.")

    # Get a list of students to attach data to
    students = list(db.users.find({"role": "student"}))
    if not students:
        print("No students found. Please run seed_students.py first.")
        return
        
    # We will pick a few random students, including the default "student"
    demo_student = db.users.find_one({"username": "student"})
    sample_students = random.sample(students, min(10, len(students)))
    if demo_student and demo_student not in sample_students:
        sample_students.append(demo_student)

    # 2. Timetable
    db.timetable.delete_many({"subject": {"$regex": "^Demo"}})
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    slots = ["09:00 AM - 10:00 AM", "10:00 AM - 11:00 AM", "11:15 AM - 12:15 PM", "01:00 PM - 02:00 PM"]
    subjects = ["Demo: Data Structures", "Demo: Algorithms", "Demo: Database Systems", "Demo: Computer Networks", "Demo: Operating Systems"]
    
    timetable_entries = []
    for day in days:
        for slot in slots:
            timetable_entries.append({
                "day": day,
                "slot": slot,
                "subject": random.choice(subjects),
                "teacher": "Demo Teacher"
            })
    db.timetable.insert_many(timetable_entries)
    print("Added Demo Timetable.")

    # 3. Attendance & Marks
    db.attendance.delete_many({"date": {"$regex": "^202"}})
    db.marks.delete_many({"subject": {"$regex": "^Demo"}})
    
    attendance_records = []
    marks_records = []
    
    today = datetime.date.today()
    
    for student in sample_students:
        uname = student["username"]
        # Add marks
        for subj in subjects:
            marks_records.append({
                "student": uname,
                "subject": subj,
                "marks": random.randint(40, 100)
            })
            
        # Add attendance for the last 5 days
        for i in range(5):
            date_str = (today - datetime.timedelta(days=i)).isoformat()
            status = random.choice(["Present", "Present", "Present", "Absent"]) # higher chance of present
            attendance_records.append({
                "student": uname,
                "date": date_str,
                "status": status
            })

    if marks_records:
        db.marks.insert_many(marks_records)
        print("Added Demo Marks.")
    if attendance_records:
        db.attendance.insert_many(attendance_records)
        print("Added Demo Attendance.")
        
    print("Data seeding complete!")

if __name__ == "__main__":
    seed_data()
