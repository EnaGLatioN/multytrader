(function($) {
    $(document).ready(function() {
        // Скрываем exchange_two и OrderInline по умолчанию
        var exchangeTwoField = $('#id_exchange_two').closest('.form-row');
        var walletPairField = $('#id_wallet_pair').closest('.form-row');
        var orderInlineSection1 = $('.inline-related:has(#order_entry-heading)');
        var orderInlineSection2 = $('.inline-related:has(#order_entry-2-heading)');
        
        var exchangeOneField = $('#id_exchange_one').closest('.form-row');
        
        if (window.location.pathname.indexOf('add') !== -1) {
            exchangeTwoField.hide();
            walletPairField.hide();
            orderInlineSection1.hide();
            orderInlineSection2.hide();

            // Обработчик изменения exchange_one
            $('#id_exchange_one').change(function() {
                var exchangeId = $(this).val();
                var exchangeText = $(this).find('option:selected').text();
                
                if (exchangeId) {
                    exchangeOneField.hide();
                    orderInlineSection1.show();
                    orderInlineSection1.find('h2').text(exchangeText);
                    exchangeTwoField.show();
                } else {
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
                    exchangeTwoField.hide();
                    orderInlineSection2.show();
                    walletPairField.show();
                    orderInlineSection2.find('h2').text(exchangeText);
                } else {
                    exchangeTwoField.hide();
                    orderInlineSection2.show();
                    walletPairField.hide();
                    $('#id_exchange_two').empty().append('<option value="" selected>---------</option>');
                }
            });

            // Проверка минимального значения profit при выборе валютной пары
            $('#id_wallet_pair').change(function() {
                var selectedPair = $(this).val();
                
                // Проверяем, что значение действительно выбрано (не пустое и не значение по умолчанию)
                if (selectedPair && selectedPair !== '' && selectedPair !== '---------') {
                    // AJAX запрос для получения минимального значения
                    $.ajax({
                        url: '/get-min-profit/', // Замените на ваш URL
                        type: 'GET',
                        data: {
                            'wallet_pair': selectedPair
                        },
                        success: function(response) {
                            if (response.min_profit) {
                                // Устанавливаем минимальное значение в поле profit
                                $('#id_profit').attr('min', response.min_profit);
                                
                                // Показываем подсказку пользователю
                                var existingHint = $('.min-profit-hint');
                                if (existingHint.length) {
                                    existingHint.text('Минимальное значение: ' + response.min_profit);
                                } else {
                                    $('<div class="help min-profit-hint" style="color: #666; margin-top: 5px;">Минимальное значение: ' + response.min_profit + '</div>').insertAfter('#id_profit');
                                }
                            }
                        },
                        error: function() {
                            console.log('Ошибка при получении минимального значения');
                        }
                    });
                } else {
                    // Если пара не выбрана, убираем ограничения и подсказки
                    $('#id_profit').removeAttr('min');
                    $('.min-profit-hint').remove();
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