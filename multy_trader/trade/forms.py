from django.forms import (
    ModelForm,
    BooleanField,
    ModelMultipleChoiceField,
    ValidationError
)
from exchange.models import Exchange
from .models import Entry
from django.contrib.admin.widgets import FilteredSelectMultiple


class EntryForm(ModelForm):
    exchanges = ModelMultipleChoiceField(
        queryset=Exchange.objects.filter(is_active=True),
        widget=FilteredSelectMultiple("биржи", is_stacked=False),
        required=True,
        label="Выберите биржи для скальпинга",
        error_messages={'required': 'Необходимо выбрать хотя бы одну биржу'}
    )
    
    receive_notifications = BooleanField(
        initial=True,
        label="Уведомления",
        required=False
    )

    class Meta:
        model = Entry
        fields = ['profit', 'exit_course', 'shoulder', 'wallet_pair', 'is_active', 'reverse']
    