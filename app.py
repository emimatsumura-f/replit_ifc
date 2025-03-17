import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.utils import secure_filename
import csv
import tempfile
from ifc_processor import process_ifc_file

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")

# Configure SQLite database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///ifc_converter.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size
app.config["UPLOAD_FOLDER"] = tempfile.gettempdir()

ALLOWED_EXTENSIONS = {"ifc"}

db.init_app(app)

# Import models after db initialization
from models import UploadHistory

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        flash("No file selected", "error")
        return redirect(url_for("index"))
    
    file = request.files["file"]
    if file.filename == "":
        flash("No file selected", "error")
        return redirect(url_for("index"))

    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)

            # Process IFC file
            elements = process_ifc_file(filepath)
            
            # Create CSV file
            csv_filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            csv_path = os.path.join(app.config["UPLOAD_FOLDER"], csv_filename)
            
            with open(csv_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Type", "Size", "Weight", "Length", "Quantity"])
                for element in elements:
                    writer.writerow([
                        element["type"],
                        element["size"],
                        element["weight"],
                        element["length"],
                        element["quantity"]
                    ])

            # Save to history
            history = UploadHistory(
                filename=filename,
                processed_date=datetime.now(),
                element_count=len(elements)
            )
            db.session.add(history)
            db.session.commit()

            # Clean up IFC file
            os.remove(filepath)
            
            return send_file(
                csv_path,
                as_attachment=True,
                download_name=csv_filename,
                mimetype='text/csv'
            )

        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            flash(f"Error processing file: {str(e)}", "error")
            return redirect(url_for("index"))
    else:
        flash("Invalid file type. Please upload an IFC file.", "error")
        return redirect(url_for("index"))

@app.route("/history")
def history():
    uploads = UploadHistory.query.order_by(UploadHistory.processed_date.desc()).all()
    return render_template("history.html", uploads=uploads)

with app.app_context():
    db.create_all()
