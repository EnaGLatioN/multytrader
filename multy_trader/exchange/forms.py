from django import forms
from django.contrib import admin
from .models import WalletPair, PairExchangeMapping


class WalletPairAdminForm(forms.ModelForm):
    """Поле для множественного выбора существующих пар"""

    selected_pairs = forms.ModelMultipleChoiceField(
        queryset=PairExchangeMapping.objects.all(),
        widget=admin.widgets.FilteredSelectMultiple("биржевые пары", is_stacked=False),
        required=False,
        label="Выберите биржевые пары"
    )
    
    class Meta:
        model = WalletPair
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['selected_pairs'].initial = self.instance.exchange_mappings.all()
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        return instance