from django.forms import ModelForm, ModelChoiceField
from exchange.models import Exchange
from .models import Entry
from django.contrib.admin.widgets import FilteredSelectMultiple


def get_exchanges():
    return Exchange.objects.all()

class EntryForm(ModelForm):
    exchange_one = ModelChoiceField(
        queryset=get_exchanges(),
        required=False,
        label="Выберите первую биржу"
    )
    exchange_two = ModelChoiceField(
        queryset=get_exchanges(),
        required=False,
        label="Выберите вторую биржу"
    )

    class Meta:
        model = Entry
        fields = ['profit', 'exit_course', 'shoulder', 'wallet_pair', 'exchange_one', 'exchange_two']
