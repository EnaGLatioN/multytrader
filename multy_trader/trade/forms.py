from django.forms import ModelForm, ModelChoiceField
from exchange.models import Exchange
from .models import Entry
from django.contrib.admin.widgets import FilteredSelectMultiple


class EntryForm(ModelForm):
    exchange_one = ModelChoiceField(
        queryset=Exchange.objects.all(),
        required=False,
        label="Биржа"
    )
    exchange_two = ModelChoiceField(
        queryset=Exchange.objects.all(),
        required=False,
        label="Биржа"
    )

    class Meta:
        model = Entry
        fields = ['profit', 'exit_course', 'shoulder', 'wallet_pair', 'exchange_one', 'exchange_two']
