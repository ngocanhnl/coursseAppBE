# utils.py
from .models import ExpoDevice
import requests

def send_push_notification(token, title, body):
    message = {
        'to': token,
        'sound': 'default',
        'title': title,
        'body': body,
        'priority': 'high'
    }
    print("Gui thông báo đến thiết bị với token:", token)
    response = requests.post('https://exp.host/--/api/v2/push/send', json=message)

    return response.json()

# def notify_user(user, title, body):
#     try:
#         device = ExpoDevice.objects.get(user=user)
#         return send_push_notification(device.token, title, body)
#     except ExpoDevice.DoesNotExist:
#         print("❗ Người dùng chưa có Expo push token")


def notify_user(users, title, body):
    devices = ExpoDevice.objects.filter(user__in=users)
    print("Đang gửi thông báo đến các thiết bị của người dùng:", users)

    if not devices.exists():
        print("❗ Không có thiết bị nào có push token cho các user này.")
        return

    for device in devices:
        send_push_notification(device.token, title, body)