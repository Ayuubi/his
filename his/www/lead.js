frappe.ready(function() {
    $('#lead-form').on('submit', function(e) {
        e.preventDefault();
        let $btn = $(this).find('button[type="submit"]');
        $btn.prop('disabled', true).text('Diraya...');

        let data = {
            full_name: $('#full_name').val(),
         
            mobile_number: $('#mobile_number').val(),
            district: $('#district').val(),
            sex: $('input[name="sex"]:checked').val(),
            // age: $('#age').val()
        };

        frappe.call({
            method: 'his.api.lead.create_new_lead', 
            args: data,
            callback: function(r) {
                $btn.prop('disabled', false).text('Submit');
                if (!r.exc) {
                    $('#lead-form').hide();
                    $('#form-message').html('<div class="form-card text-center"><h3>Waad Mahadsantahay!</h3><p>Xogta waa la keydiyay.</p></div>');
                }
            }
        });
    });
});