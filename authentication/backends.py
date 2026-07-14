from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from .models import User

class PhoneNumberAuthBackend(ModelBackend):
    """
    مزود مخصص للمصادقة باستخدام رقم الهاتف بدلاً من اسم المستخدم
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
        
        try:
            # استخدام USERNAME_FIELD المعرف في نموذج المستخدم (وهو phone_number)
            user = User.objects.get(phone_number=username)
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        except User.DoesNotExist:
            # عدم إرجاع أي شيء إذا لم يتم العثور على المستخدم
            return None
        except Exception:
            # في حالة وجود مشاكل أخرى، نعيد None لتجربة مزودات أخرى
            return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None