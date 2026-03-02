(function($) {
    $(document).ready(function() {
        // Оборачиваем каждый инлайн в контейнер с табом
        $('.inline-group').each(function(index) {
            var $group = $(this);
            var title = $group.find('h2').first().text();

            // Создаем структуру табов
            var $tabsContainer = $('<div class="exchange-tabs-container"></div>');
            var $tabButton = $('<div class="exchange-tab" data-tab="tab-' + index + '">' + title + '</div>');
            var $tabContent = $('<div class="exchange-tab-content" id="tab-' + index + '"></div>');

            // Перемещаем содержимое инлайна в таб
            $group.wrap($tabsContainer);
            $tabContent.append($group.clone());
            $group.replaceWith($tabContent);
            $tabsContainer.prepend($tabButton);
        });

        // Обработчик переключения табов
        $('.exchange-tab').click(function() {
            var tabId = $(this).data('tab');

            // Убираем активный класс со всех
            $('.exchange-tab').removeClass('active');
            $('.exchange-tab-content').removeClass('active');

            // Активируем текущий таб
            $(this).addClass('active');
            $('#' + tabId).addClass('active');
        });

        // Активируем первый таб
        $('.exchange-tab').first().addClass('active');
        $('.exchange-tab-content').first().addClass('active');

        // Добавляем кнопки "Добавить ордер" для каждого таба
        $('.exchange-tab-content').each(function() {
            var $content = $(this);
            var $table = $content.find('table');

            if ($table.length) {
                var $addButton = $('<button type="button" class="add-order-btn">+ Добавить ордер</button>');
                $content.prepend($addButton);

                $addButton.click(function() {
                    // Находим пустую форму или клонируем последнюю
                    var $lastRow = $table.find('tbody tr').last();
                    var $newRow = $lastRow.clone();

                    // Очищаем значения в новой строке
                    $newRow.find('input, select').each(function() {
                        if ($(this).is('select')) {
                            $(this).val('');
                        } else if ($(this).attr('type') !== 'hidden') {
                            $(this).val('');
                        }
                    });

                    $table.find('tbody').append($newRow);

                    // Обновляем индексы (если нужно)
                    updateFormIndices($table);
                });
            }
        });

        // Функция обновления индексов форм (если используется __prefix__)
        function updateFormIndices($table) {
            var totalForms = $table.closest('form').find('[name$="TOTAL_FORMS"]');
            if (totalForms.length) {
                var count = $table.find('tbody tr').length;
                totalForms.val(count);
            }
        }
    });
})(django.jQuery);