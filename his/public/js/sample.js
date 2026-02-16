frappe.ui.form.on('Sample Collection', {
	refresh(frm) {
		// your code here
		frm.remove_custom_button('View Lab Tests');
		frm.add_custom_button(__("Call"), function(){
		    frm.set_value("que_steps" , "Called")
		    frm.save()
  //perform desired action such as routing to new form or fetching etc.
        })
	},
})