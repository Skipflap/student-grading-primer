from flask import Flask, jsonify, request
from flask_cors import CORS

import db

app = Flask(__name__)
CORS(app)

# Instructions:
# - Use the functions in backend/db.py in your implementation.
# - You are free to use additional data structures in your solution
# - You must define and tell your tutor one edge case you have devised and how you have addressed this

@app.route("/students")
def get_students():
    """
    Route to fetch all students from the database
    return: Array of student objects
    """
    try:
        students = db.get_all_students()
        return jsonify(students), 200
    except Exception:
        return jsonify({"error": "Failed to fetch students"}), 404


@app.route("/students", methods=["POST"])
def create_student():
    """
    Route to create a new student
    param name: The name of the student (from request body)
    param course: The course the student is enrolled in (from request body)
    param mark: The mark the student received (from request body)
    return: The created student if successful
    """
    try:
        data = request.get_json(silent=True)
        if not data or not data.get("name") or not data.get("course"):
            return jsonify({"error": "name and course are required"}), 404
        name = data["name"].strip() if isinstance(data["name"], str) else str(data["name"])
        course = data["course"].strip() if isinstance(data["course"], str) else str(data["course"])
        mark = data.get("mark")
        if mark is None:
            mark = 0
        else:
            try:
                mark = int(mark)
            except (TypeError, ValueError):
                return jsonify({"error": "mark must be an integer"}), 404
        student = db.insert_student(name, course, mark)
        return jsonify(student), 200
    except Exception:
        return jsonify({"error": "Failed to create student"}), 404


@app.route("/students/<int:student_id>", methods=["PUT"])
def update_student(student_id):
    """
    Route to update student details by id
    param name: The name of the student (from request body)
    param course: The course the student is enrolled in (from request body)
    param mark: The mark the student received (from request body)
    return: The updated student if successful
    """
    try:
        data = request.get_json(silent=True) or {}
        name = data.get("name")
        course = data.get("course")
        mark = data.get("mark")
        if "mark" in data and mark is not None:
            try:
                mark = int(mark)
            except (TypeError, ValueError):
                return jsonify({"error": "mark must be an integer"}), 404
        updated = db.update_student(student_id, name=name, course=course, mark=mark)
        if updated is None:
            return jsonify({"error": "Student not found"}), 404
        return jsonify(updated), 200
    except Exception:
        return jsonify({"error": "Failed to update student"}), 404


@app.route("/students/<int:student_id>", methods=["DELETE"])
def delete_student(student_id):
    """
    Route to delete student by id
    return: The deleted student
    """
    try:
        student = db.get_student_by_id(student_id)
        if student is None:
            return jsonify({"error": "Student not found"}), 404
        result = db.delete_student(student_id)
        if result is None:
            return jsonify({"error": "Student not found"}), 404
        return jsonify(student), 200
    except Exception:
        return jsonify({"error": "Failed to delete student"}), 404


@app.route("/stats")
def get_stats():
    """
    Route to show the stats of all student marks 
    return: An object with the stats (count, average, min, max)
    """
    try:
        students = db.get_all_students()
        count = len(students)
        if count == 0:
            return jsonify({
                "count": 0,
                "average": 0,
                "min": None,
                "max": None,
            }), 200
        marks = [s["mark"] for s in students]
        return jsonify({
            "count": count,
            "average": round(sum(marks) / count, 2),
            "min": min(marks),
            "max": max(marks),
        }), 200
    except Exception:
        return jsonify({"error": "Failed to fetch stats"}), 404


@app.route("/")
def health():
    """Health check."""
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
