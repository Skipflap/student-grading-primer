"""
Extended private test suite to ensure correct implementation.
"""

import time
import sys
import psycopg2
import requests

# NOTE: If you have changed the backend port (refer to Discourse), you will need to change this
BASE_URL = "http://backend:5000"
DB_CONFIG = {
    "host": "db",
    "database": "marksdb",
    "user": "marksuser",
    "password": "markspass",
}

# Helper functions ie. Cleanup, waiting for DB to load and checking condition
def fail(msg):
    print("AUTOTEST FAILED:", msg)
    sys.exit(1)


def check(condition, msg):
    if not condition:
        raise AssertionError(msg)


def wait_for_backend(timeout_seconds=25):
    start = time.time()
    last_error = None
    while time.time() - start < timeout_seconds:
        try:
            r = requests.get(f"{BASE_URL}/")
            if r.status_code == 200:
                return
        except Exception as e:  
            last_error = e
        time.sleep(1)
    fail(f"Backend did not become ready in time (last_error={last_error})")


def db_connection():
    return psycopg2.connect(**DB_CONFIG)


def get_db_students():
    conn = db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, course, mark FROM students ORDER BY id;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        {"id": r[0], "name": r[1], "course": r[2], "mark": r[3]} for r in rows
    ]


def cleanup_test_students():
    """
    Remove autotest rows created from other tests
    """
    conn = db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM students WHERE name LIKE 'Autotest %';")
    conn.commit()
    cur.close()
    conn.close()


def get_students():
    """
    Basic check for getting students
    """
    r = requests.get(f"{BASE_URL}/students")
    check(r.status_code == 200, f"GET /students expected 200, got {r.status_code}")
    data = r.json()
    check(
        isinstance(data, list),
        f"GET /students must return a JSON list, got {type(data)}",
    )
    return data


def get_stats():
    """
    Basic check for stats having the right format
    """
    r = requests.get(f"{BASE_URL}/stats")
    check(r.status_code == 200, f"GET /stats expected 200, got {r.status_code}")
    stats = r.json()
    for key in ("count", "average", "min", "max"):
        check(key in stats, f"GET /stats response missing key '{key}'")
    return stats


def create_student(payload):
    """
    Create student with provided payload
    """
    res = requests.post(f"{BASE_URL}/students", json=payload)
    try:
        body = res.json()
    except Exception:
        body = {}
    return res, body

# ---=== Autotests ===--- #
def test_health_check():
    """
    Basic health check
    """
    res = requests.get(f"{BASE_URL}/")
    check(res.status_code == 200, f"Health endpoint expected 200, got {res.status_code}")
    data = res.json()
    check(
        isinstance(data, dict) and data.get("status") == "ok",
        "Health endpoint should return JSON with {'status': 'ok'}",
    )


def test_get_students_structure_and_db_consistency():
    """
    Check students match whatever is in the database, and stored in the correct format
    """
    students = get_students()
    check(len(students) > 0, "GET /students returned empty list")

    for s in students:
        check(
            all(k in s for k in ("id", "name", "course", "mark")),
            f"Student object missing required keys: {s}",
        )
        check(isinstance(s["id"], int), "Student id must be an int")
        check(isinstance(s["name"], str), "Student name must be a string")
        check(isinstance(s["course"], str), "Student course must be a string")
        check(
            isinstance(s["mark"], int) or s["mark"] is None,
            "Student mark must be an int or None",
        )

    db_students = get_db_students()
    check(
        len(students) == len(db_students),
        "API /students length must match DB students length "
        f"(api={len(students)}, db={len(db_students)})",
    )
    student_ids = {s["id"]: s for s in students}
    for row in db_students:
        student_id = row["id"]
        check(
            student_id in student_ids,
            f"Student id {student_id} exists in DB but not in /students response",
        )
        student_row = student_ids[student_id]
        check(
            student_row["name"] == row["name"]
            and student_row["course"] == row["course"]
            and student_row["mark"] == row["mark"],
            f"/students data for id={student_id} does not match DB row",
        )


def test_create_student_persists_and_updates_stats():
    """
    Creating a student:
    - returns 200 and a well-formed student object
    - row appears in the DB
    - /students and /stats reflect the new student.
    """
    students_before = get_students()
    stats_before = get_stats()

    payload = {
        "name": "Autotest student 1",
        "course": "COMP3900",
        "mark": 75,
    }
    res, body = create_student(payload)
    check(res.status_code == 200, f"POST /students expected 200, got {res.status_code}")
    for key in ("id", "name", "course", "mark"):
        check(key in body, f"Created student missing key '{key}'")
    student_id = body["id"]
    check(isinstance(student_id, int), "Created student id must be an int")
    check(body["name"] == payload["name"], "Created student name mismatch")
    check(body["course"] == payload["course"], "Created student course mismatch")
    check(body["mark"] == payload["mark"], "Created student mark mismatch")

    # Confirm it is in DB
    conn = db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT name, course, mark FROM students WHERE id = %s;", (student_id,)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    check(row is not None, "Created student not found in DB by id")
    check(
        row[0] == payload["name"]
        and row[1] == payload["course"]
        and row[2] == payload["mark"],
        "DB row for created student does not match payload",
    )

    students_after = get_students()
    check(
        len(students_after) == len(students_before) + 1,
        "After POST /students, /students length did not increase by 1",
    )

    stats_after = get_stats()
    marks = [s["mark"] for s in students_after if isinstance(s.get("mark"), int)]
    if marks:
        expected_count = len(marks)
        expected_min = min(marks)
        expected_max = max(marks)
        expected_avg = round(sum(marks) / expected_count, 2)

        check(
            stats_after["count"] == expected_count,
            f"/stats count {stats_after['count']} does not match "
            f"number of marks {expected_count}",
        )
        check(
            stats_after["min"] == expected_min,
            f"/stats min {stats_after['min']} does not match expected {expected_min}",
        )
        check(
            stats_after["max"] == expected_max,
            f"/stats max {stats_after['max']} does not match expected {expected_max}",
        )
        check(
            abs(stats_after["average"] - expected_avg) <= 0.1,
            f"/stats average {stats_after['average']} does not match "
            f"expected {expected_avg}",
        )

    # Count shouldn't decrease
    check(
        stats_after["count"] >= stats_before["count"],
        "/stats count decreased after creating a student",
    )


def test_create_student_without_mark_has_mark_field():
    """
    Add student with empty mark field (remove assumptions that FE has correct input)
    """
    payload = {
        "name": "Autotest NoMark",
        "course": "COMP3900",
    }
    r, body = create_student(payload)
    check(r.status_code == 200, f"POST /students (no mark) expected 200, got {r.status_code}")
    check(
        "mark" in body,
        "Created student without explicit mark must still include 'mark' in response",
    )
    check(
        isinstance(body["mark"], int) or body["mark"] is None,
        "Implicit mark must be int or None",
    )

def test_update_existing_student_changes_db_and_response():
    """
    Updating an existing student should update the DB
    """
    # Create a fresh student to update
    res_create, created = create_student(
        {"name": "Autotest Update", "course": "COMP3900", "mark": 40}
    )
    check(res_create.status_code == 200, "Failed to create student for update test")
    student_id = created["id"]

    update_payload = {
        "name": "Autotest Updated",
        "course": "COMP3900",
        "mark": 90,
    }
    res = requests.put(f"{BASE_URL}/students/{student_id}", json=update_payload)
    check(
        res.status_code == 200,
        f"PUT /students/{student_id} expected 200, got {res.status_code}",
    )
    body = res.json()
    for key in ("id", "name", "course", "mark"):
        check(key in body, f"Updated student missing key '{key}'")
    check(body["id"] == student_id, "Updated student id must not change")
    check(body["name"] == update_payload["name"], "Updated student name mismatch")
    check(body["mark"] == update_payload["mark"], "Updated student mark mismatch")

    conn = db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT name, course, mark FROM students WHERE id = %s;", (student_id,)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    check(row is not None, "Updated student not found in DB by id")
    check(
        row[0] == update_payload["name"]
        and row[1] == update_payload["course"]
        and row[2] == update_payload["mark"],
        "DB row for updated student does not match payload",
    )


def test_update_nonexistent_student():
    """
    Updating a student with a non-existent id should return 404.
    """
    db_students = get_db_students()
    max_id = max((s["id"] for s in db_students), default=0)
    missing_id = max_id + 10_000
    payload = {"name": "RandomStudent", "course": "COMP3900", "mark": 10}
    res = requests.put(f"{BASE_URL}/students/{missing_id}", json=payload)
    check(res.status_code == 404, f"PUT /students/{missing_id} should return 404, got {res.status_code}")


def test_delete_existing_student_removes_from_db():
    """
    Deleting an existing student should remove the student row from the DB and the student should disappear from /students.
    """
    r_create, created = create_student(
        {"name": "Autotest Delete", "course": "COMP3900", "mark": 55}
    )
    check(r_create.status_code == 200, "Failed to create student for delete test")
    student_id = created["id"]

    r = requests.delete(f"{BASE_URL}/students/{student_id}")
    check(
        r.status_code == 200,
        f"DELETE /students/{student_id} expected 200, got {r.status_code}",
    )

    students = get_students()
    ids = [s["id"] for s in students]
    check(
        student_id not in ids,
        f"Student id {student_id} still present in /students after DELETE",
    )

    conn = db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM students WHERE id = %s;", (student_id,))
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    check(count == 0, "Student row still exists in DB after DELETE")


def test_delete_nonexistent_student():
    """
    Deleting a non-existent student id should return 404.
    """
    db_students = get_db_students()
    max_id = max((s["id"] for s in db_students), default=0)
    missing_id = max_id + 20_000
    r = requests.delete(f"{BASE_URL}/students/{missing_id}")
    check(
        r.status_code == 404,
        f"DELETE /students/{missing_id} should return 404, got {r.status_code}",
    )


def test_delete_student_updates_stats():
    """
    Deleting a student should update /stats to reflect the remaining marks.
    """
    students_before = get_students()
    marks_before = [s["mark"] for s in students_before if isinstance(s.get("mark"), int)]
    stats_before = get_stats()

    # Create a student with a known mark
    res_create, created = create_student(
        {"name": "Autotest Delete Stats", "course": "COMP3900", "mark": 60}
    )
    check(res_create.status_code == 200, "Failed to create student for delete-stats test")
    student_id = created["id"]

    students_with = get_students()
    marks_with = [s["mark"] for s in students_with if isinstance(s.get("mark"), int)]
    stats_with = get_stats()

    # Stats after creation should reflect the extra mark
    expected_count_with = len(marks_with)
    expected_min_with = min(marks_with)
    expected_max_with = max(marks_with)
    expected_avg_with = round(sum(marks_with) / expected_count_with, 2)

    check(
        stats_with["count"] == expected_count_with,
        f"/stats count after create {stats_with['count']} does not match expected {expected_count_with}",
    )
    check(
        stats_with["min"] == expected_min_with,
        f"/stats min after create {stats_with['min']} does not match expected {expected_min_with}",
    )
    check(
        stats_with["max"] == expected_max_with,
        f"/stats max after create {stats_with['max']} does not match expected {expected_max_with}",
    )
    check(
        abs(stats_with["average"] - expected_avg_with) < 0.1,
        f"/stats average after create {stats_with['average']} does not match expected {expected_avg_with}",
    )

    # Delete student id
    res = requests.delete(f"{BASE_URL}/students/{student_id}")
    check(
        res.status_code == 200,
        f"DELETE /students/{student_id} expected 200, got {res.status_code}",
    )

    students_after = get_students()
    marks_after = [s["mark"] for s in students_after if isinstance(s.get("mark"), int)]
    stats_after = get_stats()

    # Check deleted id is gone
    ids_after = [s["id"] for s in students_after]
    check(student_id not in ids_after, "Deleted student still appears in /students after DELETE")

    if marks_after:
        expected_count_after = len(marks_after)
        expected_min_after = min(marks_after)
        expected_max_after = max(marks_after)
        expected_avg_after = round(sum(marks_after) / expected_count_after, 2)

        check(
            stats_after["count"] == expected_count_after,
            f"/stats count after delete {stats_after['count']} does not match expected {expected_count_after}",
        )
        check(
            stats_after["min"] == expected_min_after,
            f"/stats min after delete {stats_after['min']} does not match expected {expected_min_after}",
        )
        check(
            stats_after["max"] == expected_max_after,
            f"/stats max after delete {stats_after['max']} does not match expected {expected_max_after}",
        )
        check(
            abs(stats_after["average"] - expected_avg_after) < 0.1,
            f"/stats average after delete {stats_after['average']} does not match expected {expected_avg_after}",
        )

    if marks_before:
        check(
            stats_after["count"] == stats_before["count"],
            "After deleting the test student, /stats count did not return to its original value",
        )

def test_stats_matches_students_marks():
    """
    /stats should match the marks from /students.
    """
    students = get_students()
    marks = [s["mark"] for s in students if isinstance(s.get("mark"), int)]
    check(marks, "No integer marks found in /students for /stats consistency test")

    stats = get_stats()
    expected_count = len(marks)
    expected_min = min(marks)
    expected_max = max(marks)
    expected_avg = round(sum(marks) / expected_count, 2)

    check(stats["count"] == expected_count, f"/stats count {stats['count']} does not match expected {expected_count}")
    check(stats["min"] == expected_min, f"/stats min {stats['min']} does not match expected {expected_min}")
    check(stats["max"] == expected_max, f"/stats max {stats['max']} does not match expected {expected_max}")
    check(abs(stats["average"] - expected_avg) < 0.1, f"/stats average {stats['average']} does not match expected {expected_avg}")

def main():
    print("Waiting for backend to become ready...")
    wait_for_backend()
    cleanup_test_students()

    tests = [
        ("health_check", test_health_check),
        ("get_students_structure_and_db_consistency", test_get_students_structure_and_db_consistency),
        ("create_student_persists_and_updates_stats", test_create_student_persists_and_updates_stats),
        ("create_student_without_mark_has_mark_field", test_create_student_without_mark_has_mark_field),
        ("update_existing_student_changes_db_and_response", test_update_existing_student_changes_db_and_response),
        ("update_nonexistent_student_returns_404", test_update_nonexistent_student),
        ("delete_existing_student_removes_from_db", test_delete_existing_student_removes_from_db),
        ("delete_nonexistent_student_returns_404", test_delete_nonexistent_student),
        ("delete_student_updates_stats", test_delete_student_updates_stats),
        ("stats_matches_students_marks", test_stats_matches_students_marks),
    ]

    try:
        for name, fn in tests:
            print(f"Running {name}...")
            fn()
            print(f"[OK] {name}")
    except AssertionError as e:
        fail(str(e))
    except Exception as e: 
        fail(f"Unexpected error: {e}")

    print("ALL AUTOTESTS PASSED (show output to your tutor)")


if __name__ == "__main__":
    main()

