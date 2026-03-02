from django.db.models.signals import pre_save
from django.dispatch import receiver
from trade.models import Entry
from trade.bot_new import first_notification


@receiver(pre_save, sender=Entry)
def check_update_status(sender, instance, **kwargs):
    if instance.status == 'WAIT':
        result = first_notification(instance)
        if result:
            instance.message_id = result.get('message_id')
