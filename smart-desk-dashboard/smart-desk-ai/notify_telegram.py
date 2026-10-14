import requests

TELEGRAM_TOKEN = "8875327304:AAGt9UI-EDFwsfp3sRpv0_ifna2X0DtBahg"
TELEGRAM_CHAT_ID = "1232529581"

def send_telegram_alert(object_name, location, timestamp, photo_path=None):
    message = (
        f"SMART DESK INSPECTOR ALERT\n\n"
        f"Object: {object_name}\n"
        f"Location: {location}\n"
        f"Time: {timestamp}"
    )

    if photo_path:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        with open(photo_path, 'rb') as photo:
            requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "caption": message},
                          files={"photo": photo})
    else:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message})

    print("Telegram alert sent.")

# Test it
if __name__ == "__main__":
    send_telegram_alert("Laptop", "Classroom 101", "9:47 PM")