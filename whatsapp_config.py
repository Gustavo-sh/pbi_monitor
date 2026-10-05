import requests

def notify_whatsapp(msg):
    requests.post(
        "http://localhost:3000/send",
        json={
            "group": "120363426925350661@g.us",
            "message": msg
        }
    )