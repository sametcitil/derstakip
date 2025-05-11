import requests
from flask import current_app

def api_get(path, **kwargs):
    """
    FastAPI'ye GET isteği gönderir.
    
    Args:
        path: API endpoint yolu (örn. "/students/1")
        **kwargs: requests.get'e iletilecek diğer parametreler
        
    Returns:
        JSON yanıtı
    """
    url = f"{current_app.config['API_URL']}{path}"
    r = requests.get(url, **kwargs)
    r.raise_for_status()
    return r.json()

def api_post(path, json=None, **kwargs):
    """
    FastAPI'ye POST isteği gönderir.
    
    Args:
        path: API endpoint yolu (örn. "/students/")
        json: Gönderilecek JSON verisi
        **kwargs: requests.post'a iletilecek diğer parametreler
        
    Returns:
        JSON yanıtı
    """
    url = f"{current_app.config['API_URL']}{path}"
    r = requests.post(url, json=json, **kwargs)
    r.raise_for_status()
    return r.json()

def api_delete(path, **kwargs):
    """
    FastAPI'ye DELETE isteği gönderir.
    
    Args:
        path: API endpoint yolu (örn. "/students/1/courses/CS101")
        **kwargs: requests.delete'e iletilecek diğer parametreler
        
    Returns:
        JSON yanıtı
    """
    url = f"{current_app.config['API_URL']}{path}"
    r = requests.delete(url, **kwargs)
    r.raise_for_status()
    return r.json() 