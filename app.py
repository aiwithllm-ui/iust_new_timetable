from flask import Flask, render_template, request, send_file
import random
import io
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors

app = Flask(__name__)

# -------------------------
# CONFIG
# -------------------------
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
PERIODS_PER_DAY = 4

# Store teachers temporarily in memory
teachers_subjects = []

# -------------------------
# TIMETABLE GENERATOR
# -------------------------
def generate_timetable(teachers_subjects, days, periods):
    timetable = {day: [None] * periods for day in days}
    slots = [(day, p) for day in days for p in range(periods)]
    random.shuffle(slots)

    # Repeat assignments so we can fill all slots
    assignments = teachers_subjects * (len(slots) // len(teachers_subjects) + 1)
    random.shuffle(assignments)

    used = set()  # keep track of teacher per (day, period) to avoid double-booking

    for (day, p), (teacher, subject) in zip(slots, assignments):
        # Check if teacher already teaching in this period
        if (day, p, teacher) not in used:
            timetable[day][p] = (teacher, subject)
            used.add((day, p, teacher))

    return timetable

# -------------------------
# PDF EXPORT
# -------------------------
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

# -------------------------
# ROUTES
# -------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    global teachers_subjects
    if request.method == "POST":
        teacher = request.form.get("teacher")
        subject = request.form.get("subject")
        if teacher and subject:
            teachers_subjects.append((teacher, subject))
    return render_template("index.html", teachers_subjects=teachers_subjects)

@app.route("/generate")
def generate():
    if not teachers_subjects:
        return "No teachers added!"
    timetable = generate_timetable(teachers_subjects, DAYS, PERIODS_PER_DAY)
    pdf_buffer = create_pdf(timetable)
    return send_file(pdf_buffer, as_attachment=True, download_name="timetable.pdf", mimetype="application/pdf")
# -------------------------
# RUN
# -------------------------
if __name__ == "__main__":
    app.run(debug=True)