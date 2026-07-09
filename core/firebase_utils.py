import firebase_admin
from firebase_admin import messaging
import logging

logger = logging.getLogger(__name__)

def send_push_notification(token, title, body, data=None):
    """إرسال إشعار لمستخدم واحد عبر التوكن"""
    if not token:
        return

    try:
        # تحويل جميع قيم data إلى strings لأن Firebase يتطلب ذلك
        string_data = {k: str(v) for k, v in (data or {}).items()}

        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=string_data,
            token=token,
        )
        response = messaging.send(message)
        logger.info(f"Successfully sent Firebase message: {response}")
        return response
    except Exception as e:
        logger.error(f"Error sending Firebase message: {e}")
        return None

def send_bulk_push_notification(tokens, title, body, data=None):
    """إرسال إشعارات لمجموعة من التوكنات (Multicast)"""
    if not tokens:
        return

    try:
        # إزالة التوكنات الفارغة والقيم غير الصالحة
        valid_tokens = [str(t) for t in tokens if t and len(str(t)) > 10]
        if not valid_tokens:
            return None

        # تحويل البيانات لنصوص فقط
        string_data = {str(k): str(v) for k, v in (data or {}).items()}

        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=str(title),
                body=str(body),
            ),
            data=string_data,
            tokens=valid_tokens,
        )
        response = messaging.send_multicast(message)
        logger.info(f"Successfully sent {response.success_count} messages.")
        return response
    except Exception as e:
        logger.error(f"Firebase multicast error: {e}")
        return None
