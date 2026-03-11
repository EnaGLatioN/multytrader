from django.forms import (
    ModelForm, 
    BooleanField, 
    ModelMultipleChoiceField
)
from exchange.models import Exchange
from .models import Entry
from django.contrib.admin.widgets import FilteredSelectMultiple


class EntryForm(ModelForm):
    exchanges = ModelMultipleChoiceField(
        queryset=Exchange.objects.filter(is_active=True),
        widget=FilteredSelectMultiple("биржи", is_stacked=False),
        required=False,
        label="Выберите биржи для скальпинга"
    )
    
    receive_notifications = BooleanField(
        initial=True,
        label="Уведомления",
        required=False
    )

    class Meta:
        model = Entry
        fields = ['profit', 'exit_course', 'shoulder', 'wallet_pair', 'is_active', 'reverse']
    