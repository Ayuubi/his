frappe.ui.form.on('Sales Invoice', {
  refresh(frm) {
		if (frm.doc.docstatus !== 0 || frm.doc.workflow_state != "Approved") return;

		const editable_fields = ['is_pos', 'payments'];
		frm.fields
			.forEach(field => {
				if (editable_fields.includes(field.df.fieldname)) return;
				frm.set_df_property(field.df.fieldname, "read_only", 1);
			});
	},
    on_submit: function(frm) {
       
           //  let url= `${frappe.urllib.get_base_url()}/printview?doctype=Sales Invoice&name=${frm.doc.name}&trigger_print=1&settings=%7B%7D&_lang=en`;
            //  let url= `${frappe.urllib.get_base_url()}/printview?doctype=Sales Invoice&name=${frm.doc.name}&trigger_print=1&settings=%7B%7D&_lang=en`;
            //  window.open(url, '_blank');
        },
        onload(frm) {
          if (frm.is_new() && frm.doc.patient) {
      // 			frm.trigger('toggle_payment_fields');
            frappe.call({
              method: 'frappe.client.get',
              args: {
                doctype: 'Patient',
                name: frm.doc.patient
              },
              callback: function(data) {
                  
                
                      //   alert(data.message.is_insurance)
                          if (data.message.is_insurance){

                                            let d = new frappe.ui.Dialog({

                              title: `This patient in insurance <strong>${frm.doc.patient}</strong> is in insurance <strong>${data.message.ref_insturance} </strong> do you want to Charge Patient or insurance

                                <br>

                              `,
                              fields: [
                              {
                               label: 'Insurance',
                               fieldname: 'btn',
                               fieldtype: 'HTML',
                               options: `<button type="button" class="btn btn-success" style="background-color:green" onclick='$(".modal-dialog").hide()'>Patient</button>
                                        <button type="button" class="btn btn-danger" onclick='frappe.model.set_value("${frm.doctype}", "${frm.docname}", "is_insurance", 1); $(".modal-dialog").hide()'>insurance</button>`,
                               
                               }]

                                
                                
                          });

                          d.show();
                              // frappe.warn('This patient in insurance ',
                              //         '<strong>'+frm.doc.patient+ '</strong>'+ ' is in insurance <strong>'+ data.message.ref_insturance+ '</strong>'+ ' do you want to Charge Patient or insurance',
                              //         () => {
                              //             frappe.model.set_value(frm.doctype, frm.docname, 'is_insurance', 1);
                              //             frappe.model.set_value(frm.doctype, frm.docname, 'insurance', data.message.ref_insturance);
                              //             frappe.model.set_value(frm.doctype, frm.docname, 'insurance_id', data.message.insurance_number);

                              //             // action to perform if Continue is selected
                              //         },
                              //         'insurance',
                              //         true // Sets dialog as minimizable
                              //     )
                              
                          }
              }
            });
          }
        },
        discount_amount:function(frm){
          setTimeout(() => {
            // alert(percentage(frm.doc.discount_amount , frm.doc.base_total))
            // if(!additional_discount_percentage){
              frm.set_value("percentage" , percentage(frm.doc.discount_amount , frm.doc.base_total))

            // }
           

            
          }, 100);
       
        },
        additional_discount_percentage:function(frm){
          frm.set_value("percentage" , frm.doc.additional_discount_percentage)


        }
        
         
        
    })


frappe.ui.form.on('Sales Invoice Item', {
      refresh(frm) {
        // your code here
      },
      
      //     item_code: function(frm ,  cdt , cdn){
      //     let row = locals[cdt][cdn]
      //    // console.log(row)
      //    frappe.db.get_value("Retail Setup" , "Retail Setup" , "allow_retail").then( r =>{
      //        if (r.message.allow_retail) {
      //         frappe.db.get_value("Item" , row.item_code , "strep").then( item_st =>{
      //         console.log(r)
      //         if (frappe.user_roles.includes('Tafaariiq') && item_st.message.strep) {
      //             setTimeout(() => {
      //                 frappe.model.set_value(cdt, cdn, "uom", "Strep");
      //                 console.log("Delayed for 1 second.");
      //               }, 1000);
      //        //alert("we need this")
             
      //        //row.uom = "Strep";
      //        //frm.refresh_field("items")
             
      //    }
      //     })
      //        }
      //    })
         
      // }
      
    })

    function percentage(partialValue, totalValue) {
      // alert( (100 * partialValue) / totalValue)
      return (100 * partialValue) / totalValue;
   } 