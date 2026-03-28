# ERP Portal - Enterprise Resource Planning System

A comprehensive ERP solution for educational institutions, built with a modern web stack. This platform provides distinct interfaces and functionality for Students, Teachers, and Administrators to manage academic activities, administrative tasks, and campus life efficiently.

## 🚀 Key Features

### 🎓 Student Features
- **Dashboard**: Overview of academic progress and recent notifications.
- **Academics**: Access study materials and course information.
- **Attendance**: Real-time tracking of class attendance.
- **Marks**: View internal and external exam results.
- **Fees**: Manage fee payments and view due dates.
- **Hostel**: Room allocation details and management.
- **Leave Requests**: Submit and track leave applications.
- **Helpdesk**: Raise tickets for issues or queries.

### 👩‍🏫 Teacher Features
- **Attendance Management**: Mark and update student attendance.
- **Marks Entry**: Input and manage student results for subjects.
- **Student Details**: Access and search for student profiles.
- **Notices**: Create and share important announcements.

### 🛠️ Administrator Features
- **Inventory Management**: Track and manage campus resources.
- **System Monitoring**: Oversee overall institutional data.
- **User Management**: Handle student and staff registrations.

---

## 🛠️ Technology Stack

- **Frontend**: HTML5, CSS3, Vanilla JavaScript (Modern Responsive Design)
- **Backend**: Python with Flask
- **Database**: MongoDB (via PyMongo)
- **Authentication**: JWT (JSON Web Tokens)
- **Environment Management**: Python-dotenv

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.8+
- MongoDB installed and running locally (or a remote URI)

### 1. Clone the Repository
```bash
git clone <repository-url>
cd erp_by
```

### 2. Configure Environment Variables
Create a `.env` file in the `backend/` directory (or modify the existing one):
```env
MONGO_URI=mongodb://localhost:27017/erp_db
ERP_SECRET=your_jwt_secret_key
```

### 3. Install Dependencies
It is recommended to use a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r backend/requirements.txt
```

### 4. Seed the Database
To populate the system with demo students and initial roles:
```bash
python backend/seed_students.py
```

### 5. Run the Application
You can start the server from the root directory:
```bash
python app.py
```
The application will be available at `http://localhost:5000`.

---

## 📂 Project Structure

- `backend/`: Core logic, API endpoints, and database interactions.
- `student/`: Student-specific dashboard and pages (if applicable).
- `*.html`: Frontend templates for various modules.
- `app.py`: Main entry point for the application.
- `style.css`: Global styling for the platform.
- `script.js`: Client-side logic and API integration.

---

## 🔒 Default Credentials
After seeding, you can log in with:
- **Admin**: `admin` / `adminpass`
- **Teacher**: `teacher` / `pass1234`
- **Student**: `student` / `pass1234`
