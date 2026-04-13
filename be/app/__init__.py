import os

from flask import Flask
from flask_cors import CORS
from .config import Config
from flask_jwt_extended import JWTManager
from flask import send_from_directory

jwt = JWTManager()

RESULTS_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "results"))  

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(
        app,
        resources={
            r"/api/*": {"origins": "*"},
            r"/results/*": {"origins": "*"}
        },
        allow_headers=["Content-Type", "Authorization"],
        supports_credentials=True
    )

    jwt.init_app(app)

    # ensure results folder exists for image serving
    os.makedirs(RESULTS_FOLDER, exist_ok=True)

    # import routes
    from .routes.auth_routes import auth_bp
    from .routes.detection_routes import detection_bp
    from .routes.report_routes import report_bp

    # register blueprint
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(detection_bp, url_prefix="/api/detection")
    app.register_blueprint(report_bp, url_prefix="/api/report")

    @app.route("/")
    def home():
        return {
            "message": "APDetect Backend Running",
            "status": "success"
        }

    @app.route('/results/<filename>')
    def get_result_image(filename):
        return send_from_directory(RESULTS_FOLDER, filename)

    return app