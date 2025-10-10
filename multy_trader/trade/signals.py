from django.db.models.signals import pre_save
from django.dispatch import receiver
from trade.models import Entry
from trade.bot import notification


@receiver(pre_save,sender=Entry)
def check_update_status(sender, instance, **kwargs):
    original_status = Entry.objects.get(id = instance.id)
    if original_status != instance.status:
        notification(instance)
