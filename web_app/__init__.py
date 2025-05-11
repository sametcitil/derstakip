from flask import Flask
from flask_debugtoolbar import DebugToolbarExtension

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "change-me"
    app.config["API_URL"] = "http://localhost:8000/api"  # FastAPI
    
    # Debug toolbar
    app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = False
    toolbar = DebugToolbarExtension(app)

    # Blueprint'leri bağla
    from .routes.students import bp as students_bp
    app.register_blueprint(students_bp)

    # Ana sayfa yönlendirmesi
    @app.route("/")
    def index():
        from flask import redirect, url_for
        return redirect(url_for("students.list_students"))

    return app 