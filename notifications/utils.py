from firebase_admin import messaging
import logging

logger = logging.getLogger(__name__)

def send_fcm_notification(user, title, body, data=None):
    """
    إرسال إشعار Firebase لمستخدم معين
    """
    if not user.fcm_token:
        logger.warning(f"المستخدم {user.phone_number} ليس لديه fcm_token")
        return None

    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data or {},
            token=user.fcm_token,
        )
        response = messaging.send(message)
        logger.info(f"تم إرسال الإشعار بنجاح: {response}")
        return response
    except Exception as e:
        logger.error(f"خطأ أثناء إرسال إشعار FCM: {str(e)}")
        return None

def send_bulk_fcm_notification(users, title, body, data=None):
    """
    إرسال إشعار Firebase لمجموعة من المستخدمين
    """
    tokens = [u.fcm_token for u in users if u.fcm_token]
    if not tokens:
        return None

    try:
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data or {},
            tokens=tokens,
        )
        response = messaging.send_multicast(message)
        logger.info(f"تم إرسال {response.success_count} إشعارات بنجاح")
        return response
    except Exception as e:
        logger.error(f"خطأ أثناء إرسال إشعارات Bulk FCM: {str(e)}")
        return None
