from django.db import models
from django.conf import settings

class UserMfa(models.Model):

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='mfa_keys', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    key_id = models.BinaryField(max_length=255, null=False)
    public_key = models.BinaryField(max_length=255, null=False)
    sign_count = models.IntegerField(null=False)
    last_usage = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username + str(self.key_id)

    class Meta:
        default_permissions = ()
        unique_together = (('user', 'name', ), )
