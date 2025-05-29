from web_app import create_app
import datetime

# Flask web uygulamasını oluştur
app = create_app()

# Jinja2 şablonlarında kullanılabilecek global değişkenleri tanımla
@app.context_processor
def inject_now():
    """
    Şablonlarda kullanılmak üzere mevcut tarih/saat bilgisini sağlar.
    Bu sayede şablonlarda {{ now }} değişkeni kullanılabilir.
    """
    return {'now': datetime.datetime.now()}

if __name__ == "__main__":
    # Geliştirme sunucusunu başlat
    app.run(debug=True, port=5000) 