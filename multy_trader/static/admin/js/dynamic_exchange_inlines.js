(function($) {
    var initialized = false;
    var saving = false;

    function getEntryId() {
        var path = window.location.pathname;
        if (path.includes('/add/')) {
            return null;
        }
        var match = path.match(/\/entry\/([a-f0-9-]+)\//);
        return match ? match[1] : null;
    }

    function saveExchangesToSession(exchangeIds) {
        if (saving) return;
        saving = true;

        $.ajax({
            url: '/trade/save-exchanges-to-session/',
            method: 'POST',
            headers: {
                'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val()
            },
            data: JSON.stringify({
                'exchange_ids': exchangeIds,
                'entry_id': getEntryId()
            }),
            contentType: 'application/json',
            success: function() {
                location.reload();
            },
            error: function(xhr, status, error) {
                console.error('Error saving exchanges:', error);
                saving = false;
            }
        });
    }

    function getSelectedFromChosen() {
        var selected = [];
        $('.selector-chosen select option').each(function() {
            selected.push($(this).val());
        });
        return selected;
    }

    function attachEvents() {
        if (initialized) return;

        var $chosenSelect = $('.selector-chosen select');
        var $availableSelect = $('.selector-available select');

        if (!$chosenSelect.length) return false;

        initialized = true;

        // Кнопки-стрелки
        $('.selector-chooseall, .selector-add, .selector-remove, .selector-clearall').on('click', function() {
            setTimeout(function() {
                saveExchangesToSession(getSelectedFromChosen());
            }, 100);
        });

        // Двойной клик в левом списке (добавить)
        $availableSelect.on('dblclick', 'option', function() {
            var addedVal = $(this).val();
            setTimeout(function() {
                var selected = getSelectedFromChosen();
                if (selected.indexOf(addedVal) === -1) {
                    selected.push(addedVal);
                }
                saveExchangesToSession(selected);
            }, 100);
        });

        // Двойной клик в правом списке (убрать)
        $chosenSelect.on('dblclick', 'option', function() {
            var removedVal = $(this).val();
            setTimeout(function() {
                var selected = getSelectedFromChosen();
                selected = selected.filter(function(id) { return id !== removedVal; });
                saveExchangesToSession(selected);
            }, 100);
        });

        // Вкладки
        $('.nav-tabs a').on('shown.bs.tab', function() {
            if (getSelectedFromChosen().length === 0) {
                $('.dynamic-inline').remove();
            }
        });

        return true;
    }

    function init() {
        if (!attachEvents()) {
            setTimeout(attachEvents, 500);
            setTimeout(attachEvents, 1000);
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})(django.jQuery);
