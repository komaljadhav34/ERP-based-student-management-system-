from flask import Flask, request, jsonify, send_from_directory, g
import os
import datetime
from pathlib import Path
from functools import wraps
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ---------- Configuration ----------
BASE_DIR = Path(__file__).resolve().parent
# Serve static files directly from the project root (parent of backend)
FRONTEND_DIR = str(BASE_DIR.parent)

SECRET = os.environ.get("ERP_SECRET", "supersecretkey")
JWT_ALGO = "HS256"
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/erp_db")

app = Flask(__name__)
CORS(app)

# ---------- Database helpers ----------
def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        client = MongoClient(MONGO_URI)
        db = g._database = client.get_database()
    return db

def init_db():
    """Initialize database indexes if needed."""
    print(f"[init_db] Connecting to MongoDB at: {MONGO_URI}")
    client = MongoClient(MONGO_URI)
    db = client.get_database()
    
    # Create unique index for username
    db.users.create_index("username", unique=True)
    
    # Seed demo users if not exist
    if db.users.count_documents({}) == 0:
        print("[init_db] Seeding demo users...")
        users = [
            {"username": "admin", "password": generate_password_hash("adminpass"), "role": "admin", "fullname": "Administrator", "email": "admin@example.com"},
            {"username": "teacher", "password": generate_password_hash("pass1234"), "role": "teacher", "fullname": "Demo Teacher", "email": "teacher@example.com"},
            {"username": "student", "password": generate_password_hash("pass1234"), "role": "student", "fullname": "Demo Student", "email": "student@example.com"}
        ]
        db.users.insert_many(users)
        
        # Sample notification
        now = datetime.datetime.utcnow().isoformat()
        db.notifications.insert_one({"title": "Welcome", "message": "System initialized", "created_at": now})
        
        print("[init_db] Database seeded.")
    else:
        print("[init_db] Database already contains data.")

@app.teardown_appcontext
def close_connection(exc):
    db = getattr(g, "_database", None)
    if db is not None:
        # PyMongo client usually doesn't need explicit close per request, but we can if we stored client
        pass

def dump_doc(doc):
    """Convert MongoDB document to dict with string ID."""
    if not doc:
        return None
    if isinstance(doc, list):
        return [dump_doc(d) for d in doc]
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    return doc

# ---------- Auth / JWT helpers ----------
def generate_token(username, role):
    payload = {
        "sub": username,
        "role": role,
        "iat": int(datetime.datetime.utcnow().timestamp())
    }
    token = jwt.encode(payload, SECRET, algorithm=JWT_ALGO)
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token

def decode_token(token):
    try:
        return jwt.decode(token, SECRET, algorithms=[JWT_ALGO])
    except jwt.ExpiredSignatureError:
        return {"error":"token_expired"}
    except Exception:
        return None

def auth_required(role=None):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            auth = request.headers.get("Authorization", "")
            if not auth.startswith("Bearer "):
                return jsonify({"error":"authorization required"}), 401
            token = auth.split(" ", 1)[1]
            data = decode_token(token)
            if data is None or (isinstance(data, dict) and data.get("error") == "token_expired"):
                return jsonify({"error":"invalid or expired token"}), 401
            if role and data.get("role") != role:
                return jsonify({"error":"forbidden"}), 403
            # attach user info to request
            request.user = data.get("sub")
            request.user_role = data.get("role")
            return f(*args, **kwargs)
        return wrapped
    return decorator

# ---------- Static frontend serving ----------
@app.route("/", defaults={"path":"index.html"})
@app.route("/<path:path>")
def frontend(path):
    if not Path(FRONTEND_DIR).exists():
        return f"FRONTEND_DIR {FRONTEND_DIR} not found on server.", 404
        
    file_path = Path(FRONTEND_DIR) / path
    if not file_path.exists():
        return f"Error: '{path}' not found in directory '{FRONTEND_DIR}' (Resolved from __file__: {__file__}). Please check your Render Start Command and Root Directory settings.", 404
        
    return send_from_directory(FRONTEND_DIR, path)

# ---------- Auth endpoints ----------
@app.route("/api/register", methods=["POST"])
def register():
    db = get_db()
    data = request.json or {}
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()
    role = (data.get("role") or "student").strip()
    
    if not username or not password:
        return jsonify({"error":"missing fields"}), 400

    if db.users.find_one({"username": username}):
        return jsonify({"error":"username exists"}), 400

    pw = generate_password_hash(password)
    user_doc = {
        "username": username,
        "password": pw,
        "role": role,
        "fullname": data.get("fullname", ""),
        "email": data.get("email", ""),
        "branch": data.get("branch", ""),
        "year": data.get("year", ""),
        "studentId": data.get("studentId", "")
    }
    if role == "student":
        user_doc["admission_status"] = "pending"
    # If details dict is passed (from my previous signup fix), flatten it or store it.
    # The previous signup fix sent: details: { studentId, branch, staffType }
    # Let's handle both top-level and nested 'details' for backward/forward compatibility
    if "details" in data:
        details = data["details"]
        if "branch" in details: user_doc["branch"] = details["branch"]
        if "studentId" in details: user_doc["studentId"] = details["studentId"]
        # Add other fields as needed
    
    db.users.insert_one(user_doc)
    
    token = generate_token(username, role)
    return jsonify({"token": token, "username": username, "role": role})

@app.route("/api/login", methods=["POST"])
def login():
    db = get_db()
    data = request.json or {}
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()
    
    if not username or not password:
        return jsonify({"error":"missing fields"}), 400
        
    user = db.users.find_one({"username": username})
    if not user:
        return jsonify({"error":"invalid credentials"}), 401
        
    if not check_password_hash(user["password"], password):
        return jsonify({"error":"invalid credentials"}), 401
        
    if user["role"] == "student" and user.get("admission_status") == "pending":
        return jsonify({"error":"Admission pending approval. Please wait for an administrator to approve your admission."}), 403
        
    token = generate_token(user["username"], user["role"])
    return jsonify({"token": token, "username": user["username"], "role": user["role"]})

@app.route("/api/profile", methods=["GET"])
@auth_required()
def profile():
    db = get_db()
    user = db.users.find_one({"username": request.user}, {"password": 0})
    if not user:
        return jsonify({"error":"user not found"}), 404
    return jsonify(dump_doc(user))

@app.route("/api/students", methods=["GET"])
@auth_required()
def list_students():
    db = get_db()
    # Allow teachers and admins to see student list
    if request.user_role not in ["teacher", "admin"]:
        return jsonify({"error":"forbidden"}), 403
        
    # Fetch all users with role 'student'
    students = list(db.users.find({"role": "student"}, {"password": 0}))
    return jsonify(dump_doc(students))

# ---------- CRUD endpoints ----------
@app.route("/api/notifications", methods=["GET","POST"])
@auth_required()
def notifications():
    db = get_db()
    if request.method == "GET":
        notifs = list(db.notifications.find().sort("created_at", -1))
        return jsonify(dump_doc(notifs))
    
    data = request.json or {}
    title = data.get("title")
    message = data.get("message")
    if not title or not message:
        return jsonify({"error":"missing fields"}), 400
        
    now = datetime.datetime.utcnow().isoformat()
    db.notifications.insert_one({"title": title, "message": message, "created_at": now})
    return jsonify({"ok":True}), 201

@app.route("/api/attendance", methods=["GET","POST"])
@auth_required()
def attendance():
    db = get_db()
    if request.method == "GET":
        # Filter by student if not admin/teacher (optional refinement)
        # For now, let's assume students only want to see their own attendance
        query = {}
        if request.user_role == "student":
            query["student"] = request.user
        recs = list(db.attendance.find(query).sort("date", -1))
        return jsonify(dump_doc(recs))
        
    data = request.json or {}
    student = data.get("student")
    date = data.get("date")
    status = data.get("status")
    if not student or not date or not status:
        return jsonify({"error":"missing fields"}), 400
        
    db.attendance.insert_one({"student": student, "date": date, "status": status})
    return jsonify({"ok":True}), 201

@app.route("/api/marks", methods=["GET","POST"])
@auth_required()
def marks():
    db = get_db()
    if request.method == "GET":
        query = {}
        if request.user_role == "student":
            query["student"] = request.user
        recs = list(db.marks.find(query))
        return jsonify(dump_doc(recs))
        
    data = request.json or {}
    student = data.get("student")
    subject = data.get("subject")
    marks = data.get("marks")
    if not student or not subject or marks is None:
        return jsonify({"error":"missing fields"}), 400
        
    db.marks.insert_one({"student": student, "subject": subject, "marks": int(marks)})
    return jsonify({"ok":True}), 201

@app.route("/api/timetable", methods=["GET","POST"])
@auth_required()
def timetable():
    db = get_db()
    if request.method == "GET":
        recs = list(db.timetable.find())
        return jsonify(dump_doc(recs))
        
    data = request.json or {}
    day = data.get("day")
    slot = data.get("slot")
    subject = data.get("subject")
    teacher = data.get("teacher")
    if not day or not slot or not subject:
        return jsonify({"error":"missing fields"}), 400
        
    db.timetable.insert_one({"day": day, "slot": slot, "subject": subject, "teacher": teacher})
    return jsonify({"ok":True}), 201

@app.route("/api/tickets", methods=["GET","POST"])
@auth_required()
def tickets():
    db = get_db()
    if request.method == "GET":
        query = {}
        if request.user_role == "student":
            query["user"] = request.user
        recs = list(db.tickets.find(query).sort("created_at", -1))
        return jsonify(dump_doc(recs))
        
    data = request.json or {}
    subj = data.get("subject")
    msg = data.get("message")
    if not subj or not msg:
        return jsonify({"error":"missing fields"}), 400
        
    now = datetime.datetime.utcnow().isoformat()
    db.tickets.insert_one({
        "user": request.user,
        "subject": subj,
        "message": msg,
        "status": "open",
        "created_at": now
    })
    return jsonify({"ok":True}), 201

@app.route("/api/fees", methods=["GET","POST"])
@auth_required()
def fees():
    db = get_db()
    if request.method == "GET":
        query = {}
        if request.user_role == "student":
            query["student"] = request.user
        recs = list(db.fees.find(query))
        return jsonify(dump_doc(recs))
        
    data = request.json or {}
    student = data.get("student")
    amount = data.get("amount")
    due = data.get("due_date")
    if not student or amount is None or not due:
        return jsonify({"error":"missing fields"}), 400
        
    db.fees.insert_one({
        "student": student,
        "amount": float(amount),
        "due_date": due,
        "paid": 0
    })
    return jsonify({"ok":True}), 201

@app.route("/api/leaves", methods=["GET","POST"])
@auth_required()
def leaves():
    db = get_db()
    if request.method == "GET":
        query = {}
        if request.user_role == "student":
            query["user"] = request.user
        recs = list(db.leaves.find(query))
        return jsonify(dump_doc(recs))
        
    data = request.json or {}
    start = data.get("start_date")
    end = data.get("end_date")
    reason = data.get("reason")
    if not start or not end or not reason:
        return jsonify({"error":"missing fields"}), 400
        
    db.leaves.insert_one({
        "user": request.user,
        "start_date": start,
        "end_date": end,
        "reason": reason,
        "status": "pending"
    })
    return jsonify({"ok":True}), 201

@app.route("/api/inventory", methods=["GET","POST"])
@auth_required(role="admin")
def inventory():
    db = get_db()
    if request.method == "GET":
        recs = list(db.inventory.find())
        return jsonify(dump_doc(recs))
        
    data = request.json or {}
    item = data.get("item")
    qty = data.get("qty")
    loc = data.get("location", "")
    if not item or qty is None:
        return jsonify({"error":"missing fields"}), 400
        
    db.inventory.insert_one({"item": item, "qty": int(qty), "location": loc})
    return jsonify({"ok":True}), 201

@app.route("/api/exams", methods=["GET","POST"])
@auth_required()
def exams():
    db = get_db()
    if request.method == "GET":
        recs = list(db.exams.find())
        return jsonify(dump_doc(recs))
        
    data = request.json or {}
    title = data.get("title")
    date = data.get("date")
    details = data.get("details", "")
    if not title or not date:
        return jsonify({"error":"missing fields"}), 400
        
    db.exams.insert_one({"title": title, "date": date, "details": details})
    return jsonify({"ok":True}), 201

@app.route("/api/hostel", methods=["GET","POST"])
@auth_required()
def hostel():
    db = get_db()
    if request.method == "GET":
        query = {}
        if request.user_role == "student":
            query["student"] = request.user
        recs = list(db.hostel.find(query))
        return jsonify(dump_doc(recs))
        
    data = request.json or {}
    student = data.get("student")
    room = data.get("room")
    block = data.get("block", "")
    if not student or not room:
        return jsonify({"error":"missing fields"}), 400
        
    db.hostel.insert_one({"student": student, "room": room, "block": block})
    return jsonify({"ok":True}), 201

# ---------- Workflow Endpoints ----------
@app.route("/api/admissions/pending", methods=["GET"])
@auth_required(role="admin")
def pending_admissions():
    db = get_db()
    recs = list(db.users.find({"role": "student", "admission_status": "pending"}, {"password": 0}))
    return jsonify(dump_doc(recs))

@app.route("/api/admissions/approve/<user_id>", methods=["POST"])
@auth_required(role="admin")
def approve_admission(user_id):
    db = get_db()
    res = db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"admission_status": "approved"}})
    if res.modified_count == 0:
        return jsonify({"error": "User not found or already approved"}), 400
    return jsonify({"ok": True}), 200

@app.route("/api/fees/pay", methods=["POST"])
@auth_required()
def pay_fee():
    db = get_db()
    data = request.json or {}
    fee_id = data.get("fee_id")
    amount = data.get("amount")
    if not fee_id or amount is None:
        return jsonify({"error":"missing fields"}), 400
        
    # Find fee
    fee = db.fees.find_one({"_id": ObjectId(fee_id)})
    if not fee:
        return jsonify({"error":"Fee record not found"}), 404
        
    # Update paid amount
    new_paid = fee.get("paid", 0) + float(amount)
    db.fees.update_one({"_id": ObjectId(fee_id)}, {"$set": {"paid": new_paid}})
    
    # Generate receipt
    receipt = {
        "student": request.user,
        "fee_id": fee_id,
        "amount_paid": float(amount),
        "date": datetime.datetime.utcnow().isoformat(),
        "transaction_id": f"TXN-{int(datetime.datetime.utcnow().timestamp())}"
    }
    db.receipts.insert_one(receipt)
    return jsonify({"ok":True, "transaction_id": receipt["transaction_id"]}), 201

@app.route("/api/receipts", methods=["GET"])
@auth_required()
def receipts():
    db = get_db()
    query = {}
    if request.user_role == "student":
        query["student"] = request.user
    recs = list(db.receipts.find(query).sort("date", -1))
    return jsonify(dump_doc(recs))

@app.route("/api/library", methods=["GET","POST"])
@auth_required()
def library():
    db = get_db()
    if request.method == "GET":
        query = {}
        if request.user_role == "student":
            query["student"] = request.user
        recs = list(db.library.find(query))
        return jsonify(dump_doc(recs))
        
    data = request.json or {}
    book_title = data.get("book_title")
    if not book_title:
        return jsonify({"error":"missing fields"}), 400
        
    db.library.insert_one({
        "student": request.user,
        "book_title": book_title,
        "borrow_date": datetime.datetime.utcnow().isoformat(),
        "status": "borrowed"
    })
    return jsonify({"ok":True}), 201

@app.route("/api/dashboard/stats", methods=["GET"])
@auth_required(role="admin")
def dashboard_stats():
    db = get_db()
    stats = {
        "total_students": db.users.count_documents({"role": "student", "admission_status": {"$ne": "pending"}}),
        "pending_admissions": db.users.count_documents({"role": "student", "admission_status": "pending"}),
        "total_fees_collected": sum([f.get("amount_paid", 0) for f in db.receipts.find()]),
        "total_hostel_occupancy": db.hostel.count_documents({}),
        "total_books_borrowed": db.library.count_documents({"status": "borrowed"})
    }
    return jsonify(stats)

# ---------- App start ----------
if __name__ == "__main__":
    init_db()
    print("[startup] Serving frontend from:", FRONTEND_DIR)
    port = int(os.environ.get("PORT", 5000))
    print(f"[startup] Starting app on http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
