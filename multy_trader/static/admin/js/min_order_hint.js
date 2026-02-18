(function($) {
    function init() {
        console.log("🚀 Min order hint initialized");
        
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
            
            console.log("🔄 Fetching min order for:", {walletPair, exchangeIds});
            
            var $hint = $('#min-order-hint');
            if (!$hint.length) return;
            
            if (!walletPair) {
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
                    console.log("✅ AJAX response:", response);
                    if (response.success) {
                        $hint.html(
                            '✅ Минимальное количество монет: <strong>' + response.min_order  + '</strong>'
                        );
                    } else {
                        $hint.html('❌ ' + response.error);
                    }
                },
                error: function(xhr, status, error) {
                    console.error("❌ AJAX error:", error);
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
        
        function addManualButton() {
            if ($('#fetch-min-order-btn').length) return;
            
            var $profitField = $('.field-profit').first();
            if ($profitField.length) {
                $profitField.append(
                    '<div style="margin-top: 5px;">' +
                    '<button type="button" id="fetch-min-order-btn" style="padding: 5px 10px; background: #28a745; color: white; border: none; border-radius: 3px; cursor: pointer;">' +
                    '🔄 Получить минимальное количество монет' +
                    '</button>' +
                    '</div>'
                );
                
                $('#fetch-min-order-btn').on('click', function() {
                    console.log("🖱️ Manual button clicked");
                    fetchMinOrder();
                });
            }
        }
        
        function waitForFields() {
            console.log("⏳ Waiting for fields...");
            
            var checkExist = setInterval(function() {
                if ($('.field-profit').length && $('#id_wallet_pair').length) {
                    console.log("✅ Fields found");
                    clearInterval(checkExist);
                    
                    addHint();
                    addManualButton();
                    
                    // Пробуем и change, но теперь есть кнопка как запасной вариант
                    $('#id_wallet_pair').on('change', function() {
                        console.log("💰 Wallet pair changed");
                        fetchMinOrder();
                    });
                }
            }, 100);
        }
        
        waitForFields();
    }
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})(django.jQuery);