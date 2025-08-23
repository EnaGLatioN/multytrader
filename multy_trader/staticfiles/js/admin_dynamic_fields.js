// static/js/admin_dynamic_fields.js
(function($) {
    $(document).ready(function() {
        // Скрываем exchange_two и OrderInline по умолчанию
        var exchangeTwoField = $('#id_exchange_two').closest('.form-row');
        var orderInlineSection = $('.inline-related:has(#id_order_set-group)');
        exchangeTwoField.hide();
        orderInlineSection.hide();

        // Обработчик изменения exchange_one
        $('#id_exchange_one').change(function() {
            var exchangeId = $(this).val();
            var exchangeText = $(this).find('option:selected').text();
            
            if (exchangeId) {
                // Показываем OrderInline с заголовком
                orderInlineSection.show();
                orderInlineSection.find('h2').text(exchangeText);

                // Показываем exchange_two и подгружаем опции
                exchangeTwoField.show();
                $.ajax({
                    url: '/get_exchanges/',
                    data: { 'exclude_exchange_id': exchangeId },
                    dataType: 'json',
                    success: function(data) {
                        var exchangeTwoSelect = $('#id_exchange_two');
                        exchangeTwoSelect.empty();
                        exchangeTwoSelect.append('<option value="" selected>---------</option>');
                        $.each(data.exchanges, function(index, exchange) {
                            exchangeTwoSelect.append(
                                $('<option>').val(exchange.id).text(exchange.name)
                            );
                        });
                    }
                });
            } else {
                // Скрываем, если exchange_one не выбран
                exchangeTwoField.hide();
                orderInlineSection.hide();
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