from flask import Flask, render_template, request, send_file, session, redirect, url_for
import random
import io
import os
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors

app = Flask(__name__)
app.secret_key = os.urandom(24)

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
PERIODS_PER_DAY = 4

def generate_timetable(teachers_subjects, days, periods):
    timetable = {day: [None] * periods for day in days}
    slots = [(day, p) for day in days for p in range(periods)]
    random.shuffle(slots)

    assignments = teachers_subjects * (len(slots) // len(teachers_subjects) + 1)
    random.shuffle(assignments)
    used = set()

    for (day, p), (teacher, subject) in zip(slots, assignments):
        if (day, p, teacher) not in used:
            timetable[day][p] = (teacher, subject)
            used.add((day, p, teacher))

    return timetable

def create_pdf(timetable):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    data = [["Day/Period"] + [f"P{p+1}" for p in range(PERIODS_PER_DAY)]]

    for day in DAYS:
        row = [day]
        for slot in timetable[day]:
            if slot:
                teacher, subject = slot
                row.append(f"{subject}\n({teacher})")
            else:
                row.append("Free")
        data.append(row)

    table = Table(data, repeatRows=1)
    style = TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.grey),
        ("TEXTCOLOR", (0,0), (-1,0), colors.whitesmoke),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,0), 12),
        ("GRID", (0,0), (-1,-1), 0.5, colors.black),
    ])
    table.setStyle(style)
    doc.build([table])
    buffer.seek(0)
    return buffer

@app.route("/", methods=["GET", "POST"])
def index():
    if "teachers" not in session:
        session["teachers"] = []

    if request.method == "POST":
        teacher = request.form.get("teacher")
        subject = request.form.get("subject")
        edit_index = int(request.form.get("edit_index", -1))

        if teacher and subject:
            if edit_index >= 0 and edit_index < len(session["teachers"]):
                session["teachers"][edit_index] = (teacher, subject)
            else:
                session["teachers"].append((teacher, subject))
            session.modified = True

    return render_template("index.html", teachers_subjects=session["teachers"])

@app.route("/delete/<int:index>")
def delete(index):
    if "teachers" in session and 0 <= index < len(session["teachers"]):
        session["teachers"].pop(index)
        session.modified = True
    return redirect(url_for("index"))

@app.route("/generate")
def generate():
    teachers_subjects = session.get("teachers", [])
    if not teachers_subjects:
        return "No teachers added!"

    timetable = generate_timetable(teachers_subjects, DAYS, PERIODS_PER_DAY)
    pdf_buffer = create_pdf(timetable)
    session.pop("teachers", None)

    return send_file(pdf_buffer, as_attachment=True, download_name="timetable.pdf", mimetype="application/pdf")

if __name__ == "__main__":
    app.run(debug=True)
