(function($) {
    $(document).ready(function() {
        // Скрываем exchange_two и OrderInline по умолчанию
        var exchangeTwoField = $('#id_exchange_two').closest('.form-row');
        var walletPairField = $('#id_wallet_pair').closest('.form-row');
        var orderInlineSection1 = $('.inline-related:has(#order_entry-heading)');
        var orderInlineSection2 = $('.inline-related:has(#order_entry-2-heading)');
        
        var exchangeOneField = $('#id_exchange_one').closest('.form-row');
        var orderEntryGroup1 = $('#order_entry-group');
        var orderEntryGroup2 = $('#order_entry-2-group');
        
        if (window.location.pathname.indexOf('add') !== -1) {
        exchangeTwoField.hide();
        walletPairField.hide();
        orderInlineSection1.hide();
        orderInlineSection2.hide();
        
        // Перемещаем exchange_two после первой группы ордеров а валютную пару после второй
        //exchangeTwoField.insertAfter(orderEntryGroup1);
        //walletPairField.insertAfter(orderEntryGroup2);


        // Обработчик изменения exchange_one
        $('#id_exchange_one').change(function() {
            
            var exchangeId = $(this).val();
            var exchangeText = $(this).find('option:selected').text();
            
            if (exchangeId) {
                // Показываем OrderInline с заголовком
                exchangeOneField.hide();  // Убираем выбор биржи после выбора можно убрать если так не надо
                orderInlineSection1.show();
                orderInlineSection1.find('h2').text(exchangeText);

                // Показываем exchange_two и подгружаем опции
                exchangeTwoField.show();

            } else {
                // Скрываем, если exchange_one не выбран
                exchangeOneField.show();
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
                exchangeTwoField.hide(); // Убираем выбор биржи после выбора можно убрать если так не надо
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
    }
        // Скрываем при редактировании
        if (window.location.pathname.indexOf('change') !== -1) {
            exchangeTwoField.hide();
            exchangeOneField.hide();
            orderInlineSection2.hide();
        }
    });
})(django.jQuery);