from app import create_app
from app.extensions import db
app = create_app()
with app.app_context():
    students = db.collection('students').get()
    best = None
    worst = None
    for s in students:
        d = s.to_dict()
        pred = d.get('predicted_attendance', 0)
        risk = d.get('risk_score', '')
        if not best or pred > best['predicted_attendance']:
            best = d
        if not worst or pred < worst['predicted_attendance']:
            worst = d
    print(f"Best Student: {best['email']} (Risk: {best['risk_score']}, Pred: {best['predicted_attendance']})")
    print(f"Worst Student: {worst['email']} (Risk: {worst['risk_score']}, Pred: {worst['predicted_attendance']})")
