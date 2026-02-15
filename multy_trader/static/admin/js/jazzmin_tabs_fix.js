// Ждем полной загрузки страницы
window.addEventListener('load', function() {
    // Проверяем что Bootstrap есть
    if (typeof bootstrap === 'undefined') {
        console.error('Bootstrap not loaded');
        return;
    }
    
    // Даем микросекунду на все прочее
    setTimeout(function() {
        // Инициализируем вкладки
        document.querySelectorAll('.nav-tabs .nav-link').forEach(function(tabEl) {
            // Удаляем старые обработчики
            var newTab = tabEl.cloneNode(true);
            tabEl.parentNode.replaceChild(newTab, tabEl);
            
            // Добавляем новые
            newTab.addEventListener('click', function(e) {
                e.preventDefault();
                var tab = new bootstrap.Tab(this);
                tab.show();
            });
        });
        
        // Показываем первую вкладку
        var firstTab = document.querySelector('.nav-tabs .nav-link');
        if (firstTab) {
            var tab = new bootstrap.Tab(firstTab);
            tab.show();
        }
        
        console.log('Tabs initialized');
    }, 100);
});