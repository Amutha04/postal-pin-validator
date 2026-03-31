from flask import Flask
from flask_cors import CORS
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Enable CORS so React can talk to Flask
    CORS(app)
    
    # Register routes
    from app.routes.pin_routes import pin_bp
    app.register_blueprint(pin_bp, url_prefix='/api')
    
    return app