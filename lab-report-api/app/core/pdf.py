from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet


def generate_pdf(
    file_path: str,
    hospital_profile: dict | None,
    report_number: str | None,
    template_name: str,
    patient_name: str,
    patient_age: int,
    patient_gender: str,
    patient_phone: str | None,
    referring_doctor: str | None,
    created_at: str,
    results: dict,
    parameters: list[dict],
):
    doc = SimpleDocTemplate(file_path)
    styles = getSampleStyleSheet()

    elements = []

    if hospital_profile:
        elements.append(Paragraph(hospital_profile["name"], styles["Title"]))
        if hospital_profile.get("address"):
            elements.append(Paragraph(hospital_profile["address"], styles["Normal"]))
        if hospital_profile.get("phone"):
            elements.append(Paragraph(f"Phone: {hospital_profile['phone']}", styles["Normal"]))
        if hospital_profile.get("email"):
            elements.append(Paragraph(f"Email: {hospital_profile['email']}", styles["Normal"]))
        if hospital_profile.get("registration_number"):
            elements.append(Paragraph(
                f"Registration No: {hospital_profile['registration_number']}",
                styles["Normal"],
            ))
        elements.append(Spacer(1, 12))

    elements.append(Paragraph("Pathology Lab Report", styles["Heading1"]))
    elements.append(Spacer(1, 12))

    patient_data = [
        ["Report No.", report_number or "-"],
        ["Patient Name", patient_name],
        ["Age", str(patient_age)],
        ["Gender", patient_gender],
        ["Phone", patient_phone or "-"],
        ["Referred By", referring_doctor or "-"],
        ["Test", template_name],
        ["Report Date", created_at],
    ]

    patient_table = Table(patient_data, colWidths=[120, 300])
    patient_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))

    elements.append(patient_table)
    elements.append(Spacer(1, 18))

    parameter_units = {
        parameter["name"]: parameter.get("unit", "")
        for parameter in parameters
    }

    data = [["Parameter", "Result", "Unit"]]

    for key, value in results.items():
        data.append([key, str(value), parameter_units.get(key, "")])

    table = Table(data, colWidths=[220, 100, 100])

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))

    elements.append(table)

    doc.build(elements)
