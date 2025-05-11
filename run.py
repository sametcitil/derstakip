from web_app import create_app
import datetime

app = create_app()

# Jinja2 global değişkenleri
@app.context_processor
def inject_now():
    return {'now': datetime.datetime.now()}

if __name__ == "__main__":
    app.run(debug=True, port=5000) 