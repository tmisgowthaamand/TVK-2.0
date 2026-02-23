import os
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("WHATSAPP_API_TOKEN")
PHONE = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
URL = f"https://graph.facebook.com/v17.0/{PHONE}/messages"

print("Sending to Meta...")
r = requests.post(URL, headers={
    "Authorization": f"Bearer {TOKEN}", 
    "Content-Type": "application/json"
}, json={
    "messaging_product": "whatsapp",
    "to": "91949977628193093",
    "type": "text",
    "text": {"body": "test"}
})
print(r.status_code)
print(r.text)
