(function($) {
    function init() {
        
        function getSelectedExchanges() {
            var selected = [];
            $('.selector-chosen select option').each(function() {
                selected.push($(this).val());
            });
            return selected;
        }
        
        function fetchMinOrder() {
            var walletPair = $('#id_wallet_pair').val();
            var exchangeIds = getSelectedExchanges();
                        
            var $hint = $('#min-order-hint');
            if (!$hint.length) return;
            
            if (!walletPair || walletPair === "") {
                $hint.html('💡 Выберите валютную пару');
                return;
            }
            
            if (exchangeIds.length === 0) {
                $hint.html('💡 Выберите хотя бы одну биржу');
                return;
            }
            
            $hint.html('⏳ Загрузка...');
            
            $.ajax({
                url: '/trade/get-min-order/',
                method: 'POST',
                headers: {
                    'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val()
                },
                data: JSON.stringify({
                    'wallet_pair_id': walletPair,
                    'exchange_ids': exchangeIds
                }),
                contentType: 'application/json',
                success: function(response) {
                    if (response.success) {
                        $hint.html(
                            '✅ Минимальное количество монет: <strong>' + response.min_order  + '</strong>'
                        );
                    } else {
                        $hint.html('❌ ' + response.error);
                    }
                },
                error: function(xhr, status, error) {
                    $hint.html('❌ Ошибка: ' + error);
                }
            });
        }
        
        function addHint() {
            if ($('#min-order-hint').length) return;
            
            var $profitField = $('.field-profit').first();
            if ($profitField.length) {
                $profitField.append(
                    '<div id="min-order-hint" style="margin-top: 8px; padding: 10px; background: #f8f9fa; border-left: 4px solid #17a2b8;">' +
                    '💡 Выберите валютную пару' +
                    '</div>'
                );
            }
        }
        
        function waitForElements() {
            
            var checkExist = setInterval(function() {
                if ($('.field-profit').length && $('#id_wallet_pair').length) {
                    clearInterval(checkExist);
                    
                    addHint();
                    
                    var $select = $('#id_wallet_pair');
                    var lastValue = $select.val();
                    
                    // ПРОВЕРЯЕМ ЗНАЧЕНИЕ КАЖДУЮ СЕКУНДУ (просто и надежно)
                    setInterval(function() {
                        var currentValue = $select.val();
                        if (currentValue !== lastValue) {
                            lastValue = currentValue;
                            if (currentValue && currentValue !== "") {
                                fetchMinOrder();
                            } else {
                                $('#min-order-hint').html('💡 Выберите валютную пару');
                            }
                        }
                    }, 500);
                    
                    // Если уже выбрано при загрузке
                    if (lastValue && lastValue !== "") {
                        setTimeout(fetchMinOrder, 500);
                    }
                }
            }, 100);
        }
        
        waitForElements();
    }
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})(django.jQuery);