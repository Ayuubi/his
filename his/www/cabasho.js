frappe.ready(function() {
    $('#cabasho-form').on('submit', function(e) {
        e.preventDefault();

        let $btn = $(this).find('button[type="submit"]');
        $btn.prop('disabled', true).text('Sending...');

        let data = {
            message_type: $('input[name="message_type"]:checked').val(),
            department: $('input[name="department"]:checked').val(),
            details: $('#details').val(),
            phone_number: $('#phone_number').val()
        };

        // Call backend API with the exact path to your new api.py file
        frappe.call({
            method: 'his.api.cabasho.create_feedback_issue', // <-- UPDATED PATH
            args: data,
            callback: function(r) {
                $btn.prop('disabled', false).text('Submit');
                
                if (!r.exc) {
                    $('#cabasho-form').hide();
                    $('#form-message').html(`
                        <div class="form-card form-header text-center py-5">
                            <h3 class="text-success">Waad Mahadsantahay!</h3>
                            <p>Fariintaada si guul leh ayaa loo diray.</p>
                            <button class="btn btn-submit mt-3" onclick="location.reload()">Dir Fariin Kale</button>
                        </div>
                    `);
                } else {
                    frappe.msgprint({
                        title: 'Cilad',
                        indicator: 'red',
                        message: 'Fariinta lama dirin. Fadlan isku day markale.'
                    });
                }
            }
        });
    });
});