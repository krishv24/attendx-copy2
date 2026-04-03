import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate('firebase-credentials.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

for coll in ['attendances', 'alerts', 'users']:
    docs = db.collection(coll).get()
    for doc in docs:
        data = doc.to_dict()
        if data.get('student_id') is not None and not isinstance(data.get('student_id'), str):
            print(f"Updating {coll} {doc.id}")
            doc.reference.update({'student_id': str(data.get('student_id'))})
            
print("Normalization complete.")
