import os
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("WHATSAPP_API_TOKEN")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
API_URL = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

def post_to_whatsapp(payload):
    try:
        res = requests.post(API_URL, headers=HEADERS, json=payload)
        if res.status_code not in [200, 201]:
            error_msg = f"WhatsApp API Error {res.status_code}: {res.text}\n"
            print(error_msg)
            with open("whatsapp_error.log", "a") as f:
                f.write(error_msg)
        return res
    except Exception as e:
        error_msg = f"WhatsApp Request Failed: {e}\n"
        print(error_msg)
        with open("whatsapp_error.log", "a") as f:
            f.write(error_msg)
        return None

def send_text_message(to, text):
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"preview_url": False, "body": text}
    }
    return post_to_whatsapp(payload)

def send_image_message(to, image_url, caption=None):
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "image",
        "image": {
            "link": image_url,
            "caption": caption if caption else ""
        }
    }
    return post_to_whatsapp(payload)

def send_button_message(to, body_text, buttons, image_url=None):
    action_buttons = []
    for btn in buttons:
        action_buttons.append({
            "type": "reply",
            "reply": {
                "id": btn["id"],
                "title": btn["title"]
            }
        })
    
    interactive = {
        "type": "button",
        "body": {
            "text": body_text
        },
        "action": {
            "buttons": action_buttons
        }
    }
    
    if image_url:
        interactive["header"] = {
            "type": "image",
            "image": {
                "link": image_url
            }
        }

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": interactive
    }
    return post_to_whatsapp(payload)

def send_list_message(to, body_text, button_text, sections, header_text=None):
    interactive = {
        "type": "list",
        "body": {
            "text": body_text
        },
        "action": {
            "button": button_text,
            "sections": sections
        }
    }
    
    if header_text:
        interactive["header"] = {
            "type": "text",
            "text": header_text
        }

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": interactive
    }
    return post_to_whatsapp(payload)
