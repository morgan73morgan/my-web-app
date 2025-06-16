document.addEventListener('DOMContentLoaded', function() {
    // Открытие модалки
    var addBtn = document.getElementById('openAddProgramModal');
    if (addBtn) {
        addBtn.addEventListener('click', function(e) {
            e.preventDefault();
            var modal = new bootstrap.Modal(document.getElementById('addProgramModal'));
            modal.show();
        });
    }
    // Автопоиск для пациента и специалиста через Select2 (если подключён)
    if (window.jQuery && $.fn.select2) {
        $('#id_patient').select2({width:'100%', dropdownParent:$('#addProgramModal')});
        $('#id_specialist').select2({width:'100%', dropdownParent:$('#addProgramModal')});
    }
    // AJAX submit
    var form = document.getElementById('addProgramForm');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            var formData = new FormData(form);
            var submitBtn = form.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            fetch(form.action, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                submitBtn.disabled = false;
                if (data.success) {
                    // Закрыть модалку
                    var modal = bootstrap.Modal.getInstance(document.getElementById('addProgramModal'));
                    modal.hide();
                    form.reset();
                    // Обновить список программ
                    if (data.program_row_html) {
                        var tbody = document.querySelector('table.table tbody');
                        if (tbody) tbody.insertAdjacentHTML('afterbegin', data.program_row_html);
                    } else {
                        window.location.reload();
                    }
                } else if (data.errors_html) {
                    document.querySelector('#addProgramModal .modal-body').innerHTML = data.errors_html;
                }
            })
            .catch(() => {
                submitBtn.disabled = false;
                alert('Ошибка при добавлении программы.');
            });
        });
    }
});
