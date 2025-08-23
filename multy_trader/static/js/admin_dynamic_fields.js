(function($) {
    $(document).ready(function() {
        // Скрываем exchange_two и OrderInline по умолчанию
        var exchangeTwoField = $('#id_exchange_two').closest('.form-row');
        var walletPairField = $('#id_wallet_pair').closest('.form-row');
        var orderInlineSection1 = $('.inline-related:has(#order_entry-heading)');
        var orderInlineSection2 = $('.inline-related:has(#order_entry-2-heading)');

        exchangeTwoField.hide();
        walletPairField.hide();
        orderInlineSection1.hide();
        orderInlineSection2.hide();

        // Перемещаем exchange_two после первого OrderInline
        exchangeTwoField.insertAfter(orderInlineSection1);
        walletPairField.insertAfter(orderInlineSection2);

        // Чтобы стили не похерились засовываем в класс
        exchangeTwoField.addClass('form-row');
        walletPairField.addClass('form-row');

        // Обработчик изменения exchange_one
        $('#id_exchange_one').change(function() {
            var exchangeId = $(this).val();
            var exchangeText = $(this).find('option:selected').text();
            
            if (exchangeId) {
                // Показываем OrderInline с заголовком
                orderInlineSection1.show();
                orderInlineSection1.find('h2').text(exchangeText);

                // Показываем exchange_two и подгружаем опции
                exchangeTwoField.show();

            } else {
                // Скрываем, если exchange_one не выбран
                exchangeTwoField.hide();
                orderInlineSection1.hide();
                $('#id_exchange_two').empty().append('<option value="" selected>---------</option>');
            }
        });

        $('#id_exchange_two').change(function() {
            var exchangeId = $(this).val();
            var exchangeText = $(this).find('option:selected').text();
            
            if (exchangeId) {
                // Показываем OrderInline с заголовком
                orderInlineSection2.show();
                walletPairField.show();
                orderInlineSection2.find('h2').text(exchangeText);

            } else {
                // Скрываем, если exchange_one не выбран
                exchangeTwoField.hide();
                orderInlineSection2.show();
                walletPairField.hide();
                $('#id_exchange_two').empty().append('<option value="" selected>---------</option>');
            }
        });

        // Скрываем при редактировании
        if (window.location.pathname.indexOf('change') !== -1) {
            exchangeTwoField.hide();
            orderInlineSection.hide();
        }
    });
})(django.jQuery);