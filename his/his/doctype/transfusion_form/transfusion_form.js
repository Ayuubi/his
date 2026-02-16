// Copyright (c) 2023, Rasiin Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on('TRANSFUSION FORM', {
	refresh: function(frm) {
		var nestedData = [
			{id:1, ABO:"-", RH:"-", HBsAg:"-", HCV:"-", HIV:"-", VDRL:"-"},
			{id:1, ABO:"-", RH:"-", HBsAg:"-", HCV:"-", HIV:"-", VDRL:"-"},
		]

		//define table
var table = new Tabulator("#inv", {
    height:"311px",
    layout:"fitColumns",
    columnDefaults:{
      resizable:true,
    },
    data:nestedData,
    columns:[
		   {//create column group
            title:"Blood Group",
            columns:[
            {title:"ABO", field:"ABO"},
			{title:"RH", field:"RH"},
		

			
            ],
        },

		 {//create column group
            title:"Screening",
            columns:[
           
			{title:"HBsAg", field:"HBsAg"},
			{title:"HCV", field:"HCV"},
			{title:"HIV", field:"HIV"},
			{title:"VDRL", field:"VDRL"},

			
			
			

			
            ],
        },
		{title:"LAB TECHNICIAN", field:"tech"},
		{title:"Hour", field:"Hour"}
		
  
    ],
    rowFormatter:function(row){
        //create and style holder elements
       var holderEl = document.createElement("div");
       var tableEl = document.createElement("div");

       holderEl.style.boxSizing = "border-box";
       holderEl.style.padding = "10px 30px 10px 10px";
       holderEl.style.borderTop = "1px solid #333";
       holderEl.style.borderBotom = "1px solid #333";
       

       tableEl.style.border = "1px solid #333";

    //    holderEl.appendChild(tableEl);

       row.getElement().appendChild(holderEl);

    //    var subTable = new Tabulator(tableEl, {
    //        layout:"fitColumns",
    //        data:row.getData().serviceHistory,
		
    //     //    columns:[
    //     //    {title:"ABO", field:"ABO"},
    //     //    {title:"RH", field:"RH"},
    //     //    {title:"HBsAg", field:"HBsAg"},
	// 	//    {title:"HCV", field:"HCV"},
    //     //    {title:"HIV", field:"HIV"},
    //     //    {title:"VDRL", field:"VDRL"},
	// 	//    {title:"LAB TECHNICIAN", field:"tech"},
	// 	// {title:"Hour", field:"Hour"}
    //     //    ]
    //    })
    },
});

	}
});
