(function($) {
    function init() {
        console.log("Dynamic exchange inlines initialized");
        
        function getEntryId() {
            var path = window.location.pathname;
            if (path.includes('/add/')) {
                return null;
            }
            var match = path.match(/\/entry\/([a-f0-9-]+)\//);
            return match ? match[1] : null;
        }
        
        function saveExchangesToSession(exchangeIds) {
            var entryId = getEntryId();
            
            $.ajax({
                url: '/trade/save-exchanges-to-session/',
                method: 'POST',
                headers: {
                    'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val()
                },
                data: JSON.stringify({
                    'exchange_ids': exchangeIds,
                    'entry_id': entryId
                }),
                contentType: 'application/json',
                success: function() {
                    location.reload();
                },
                error: function(xhr, status, error) {
                    console.error('Error saving exchanges:', error);
                }
            });
        }
        
        function getSelectedFromChosen() {
            var selected = [];
            $('.selector-chosen select option').each(function() {
                selected.push($(this).val());
            });
            console.log('Selected from chosen:', selected);
            return selected;
        }
        
        function watchChosenColumn() {
            var $chosenSelect = $('.selector-chosen select');
            
            if (!$chosenSelect.length) {
                console.log('Chosen select not found yet');
                return false;
            }
            
            console.log('Chosen select found, attaching events');
            
            $chosenSelect.on('change', function() {
                console.log('Chosen select changed');
                var selected = getSelectedFromChosen();
                saveExchangesToSession(selected);
            });
            
            $('.selector-chooseall, .selector-add, .selector-remove, .selector-clearall').on('click', function() {
                console.log('Selector button clicked');
                setTimeout(function() {
                    var selected = getSelectedFromChosen();
                    saveExchangesToSession(selected);
                }, 100);
            });
            
            $chosenSelect.on('dblclick', 'option', function() {
                console.log('Option double clicked');
                setTimeout(function() {
                    var selected = getSelectedFromChosen();
                    saveExchangesToSession(selected);
                }, 50);
            });
            
            return true;
        }
        
        // Пробуем инициализировать сразу
        if (!watchChosenColumn()) {
            // Если не нашли - пробуем через 500мс
            setTimeout(function() {
                console.log('Retrying init...');
                watchChosenColumn();
            }, 500);
            
            // И через 1 секунду для надежности
            setTimeout(function() {
                console.log('Final retry...');
                watchChosenColumn();
            }, 1000);
        }
    }
    
    // Ждем полной загрузки DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})(django.jQuery);