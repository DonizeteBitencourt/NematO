import os
import logging
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
import random
import json

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Configure SQLAlchemy with PostgreSQL
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///plantcare.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)
db.init_app(app)

# Enable CORS
CORS(app)

# Create tables within app context
with app.app_context():
    from models import Property
    db.create_all()
    logging.info("Database tables created")

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/diagnose', methods=['POST'])
def diagnose():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if file and file.filename:
        filename = secure_filename(file.filename)
        # In a real app, we would save the file and process it with an AI model
        # For this demo, we'll just return mock results like in the original FastAPI app
        
        # Simulate AI with fictional results
        classes = ["Ferrugem Asiática - Phakopsora pachyrhizi", "Antracnose", "Míldio", "Sadio", 
                   "Mancha Alvo", "Mancha Parda", "Oídio", "Mofo Branco"]
        
        results = [
            {"label": cls, "score": round(random.uniform(70, 99), 2)}
            for cls in random.sample(classes, k=2)
        ]
        
        # Sort results by score in descending order
        results = sorted(results, key=lambda x: x["score"], reverse=True)
        
        return jsonify({"diagnosis": results})

@app.route('/property', methods=['POST'])
def save_property():
    from models import Property
    
    try:
        data = request.json
        if not data:
            return jsonify({
                "success": False,
                "message": "Dados da propriedade não fornecidos."
            }), 400
        
        # Create new property object
        new_property = Property(
            name=data.get('name', ''),
            owner=data.get('owner', ''),
            area=float(data.get('area', 0)),
            state=data.get('state', ''),
            city=data.get('city', ''),
            address=data.get('address', ''),
            main_crop=data.get('main_crop', ''),
            planted_area=float(data.get('planted_area', 0)),
            notes=data.get('notes', '')
        )
        
        # Save to database
        db.session.add(new_property)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Propriedade cadastrada com sucesso!",
            "property_id": new_property.id
        })
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error saving property: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Erro ao salvar os dados da propriedade."
        }), 500

@app.route('/property', methods=['GET'])
def get_property():
    from models import Property
    
    # Get the latest property
    latest_property = Property.query.order_by(Property.id.desc()).first()
    
    if latest_property:
        return jsonify({
            "success": True,
            "property": {
                "id": latest_property.id,
                "name": latest_property.name,
                "owner": latest_property.owner,
                "area": latest_property.area,
                "state": latest_property.state,
                "city": latest_property.city,
                "address": latest_property.address,
                "main_crop": latest_property.main_crop,
                "planted_area": latest_property.planted_area,
                "notes": latest_property.notes
            }
        })
    else:
        return jsonify({
            "success": False,
            "message": "Nenhuma propriedade encontrada."
        }), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
