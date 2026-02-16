


let headers = {
'Accept': 'application/json',
'Content-Type': 'application/json;charset=UTF-8',
'Authorization': 'token 9716d5613f8642e:5eb6c6cafb793eb'
}
const baseUrl = `${window.location.protocol}//${window.location.host}`;

const url = window.location.href
let url_sp = url.split("/").pop()
let room = url_sp
setInterval(() => {
const options = {
method: 'POST',
headers: {
'Accept': 'application/json',
'Content-Type': 'application/json;charset=UTF-8',
'Authorization': 'token 9716d5613f8642e:5eb6c6cafb793eb'
},
body: JSON.stringify({
room: room,

})
};
fetch(`${baseUrl}/api/method/his.www.get_lab_test.get_ot_rooms` , options)
.then(response => response.json())
.then(r => {
console.log(r.message[0])
document.getElementById("title").innerText = r.message[0].service_unit_type
if(r.message[0].patient){
  document.getElementById("patient").innerText = r.message[0].patient_name
}
else{
  document.getElementById("patient").innerText = "No Patient Found "
}

if(r.message[0].patient){
    update_doc(r.message[0].patient,r.message[0].patient_name)



}

})
},5000)


function update_doc(patient,patient_name){

// test =   get_history(patient ,"imaging")
// console.log(test)

p = localStorage.getItem('patient');

// console.log(p)
if(p && p == patient){



}
else{

   

document.getElementById("p_info").innerHTML = `
    
    <div class="col-xs-12 ">
            <nav>
                <div class="nav nav-tabs nav-fill" id="nav-tab" role="tablist">
                  <a class="nav-item nav-link active"     onclick="get_history('${patient}','imaging')">Imaging</a>
                    <a class="nav-item nav-link active"     onclick="get_history('${patient}','vitals')">Vitals</a>
                    <a class="nav-item nav-link active"     onclick="get_history('${patient}','labs')">Labs</a>
                    
                 </div>
            </nav>
            <div class="tab-content py-3 px-3 px-sm-0" id="nav-tabContent">
                <div class="tab-pane fade show active" id="nav-home" role="tabpanel" aria-labelledby="nav-home-tab">
               <div id = "content">
               
               </div>
                </div>
        
            </div>
        
        </div>

    
    `
    get_history(patient ,"imaging")

localStorage.setItem('patient', patient);
// get_history(patient ,"imaging")

}








}


function get_history(patient ,tab) {



const options = {
method: 'POST',
headers: {
'Accept': 'application/json',
'Content-Type': 'application/json;charset=UTF-8',
'Authorization': 'token 9716d5613f8642e:5eb6c6cafb793eb'
},
body: JSON.stringify({
patient: patient,

})
};

const options_no_body = {
method: 'POST',
headers: headers
};
fetch(`${baseUrl}/api/method/his.dashboard_and_history.p_history.get_p_histy` , options)
.then(response => response.json())
.then(r => {
let tbldata = []
let lab_data = []

// frappe.call({
//     method: "his.dashboard_and_history.p_history.get_p_histy", //dotted path to server method
//     args : {"patient" : patient},
//     callback: function(r) {
// console.log(r)
  let columns =  r.message[0][tab]
   let data = r.message[1][tab]
 
   if(tab == "labs"){

    data.forEach(element => {
        let options_no= {
        method: 'POST',
       headers : headers,
       body :JSON.stringify({
        name : element.name
       })
    };
        fetch(`${baseUrl}/api/method/his.www.get_lab_test.get_lab_doc` , options_no)
        
        // frappe.db.get_doc("Lab Result" , element.name).then( r => {
            .then(response => response.json())
            .then(r => {
                r = r.message
                console.log(r)
            if(r.template == "CBC"){
                lab_data.push({"date": r.date , "practitioner": r.practitioner, "test": "CBC"})

            }
            
            r.normal_test_items.forEach(result => {

                lab_data.push({"date": r.date , "practitioner": r.practitioner, "test": result.test ,"lab_test_name":result.lab_test_name , "lab_test_event" : result.lab_test_event , "result_value" : result.result_value})

            })
        })
        
    });
    setTimeout(() => {
    
        columns = [{title : "Date" , field : "date"},{title : "Practitioner" , field : "practitioner"},{title : "Test" , field : "test"} , {title : "Test Name" , field : "lab_test_name"} ,  {title : "Event" , field : "lab_test_event"} , {title : "Result" , field : "result_value"}  ]
        setup_datatable(columns , lab_data , "date" , tab)
       }, 200);
   }


else if(tab == "imaging"){

// console.log(data)
if(!data.lenght){

var cols = `
                
                <div class = "col-4 mr-3" >No Image To Display</div>   
                `
                
                document.getElementById("content").innerHTML = `
                <div class = "row">
                  ${cols}

                  </idv>
                  `
}
    data.forEach(element => {

        let options_no= {
        method: 'POST',
       headers : headers,
       body :JSON.stringify({
        name : element.name
       })
    };
        fetch(`${baseUrl}/api/method/his.www.get_lab_test.get_file` , options_no)
        
        // frappe.db.get_doc("Lab Result" , element.name).then( r => {

            .then(response => response.json())
           
            .then(r => {
          
       
            // setup_datatable([] , [] , false , false , true)
                r = r.message
                // console.log("this is " , r)
             
               
                cols = ``
               
             
                  r.forEach(image => {
                  console.log(image.file_url)
                  cols += `
                
                <div class = "col-4 mr-3" ><img width="500" height="600" src = "${baseUrl}/${image.file_url}" alt = "No Image" /></div>
                
                `
                
                document.getElementById("content").innerHTML = `
                <div class = "row">
                  ${cols}

                  </idv>
                  `
                })
              
                
               
             
                  
            
        
        })
        
    });
    // setTimeout(() => {
    
    // 	columns = [{title : "Date" , field : "date"},{title : "Practitioner" , field : "practitioner"},{title : "Test" , field : "test"} , {title : "Test Name" , field : "lab_test_name"} ,  {title : "Event" , field : "lab_test_event"} , {title : "Result" , field : "result_value"}  ]
    // 	setup_datatable(columns , lab_data , "date" , tab)
    //    }, 200);



// else{

// //  alert()
                
             
//                   document.getElementById("content").innerHTML = `
//                   <div class = "row">
                  
//                     <div class = "col-6"> <h1> No Images To Display </h1></div>
//                     </div>
//                   `
// }
   }


    else{

    if(columns){
    
        setup_datatable(columns , data , false , tab)
    }
    else{
        
        setup_datatable([] , [] , false , tab)

    }
}


})


}




function setup_datatable(columns , data , group , tabid ){


// console.log(data)



this.table = {}
let groupBy = []
if(group){
groupBy.push(group)
}

this.table = new Tabulator(`#content`, {
// layout:"fitDataFill",
layout:"fitDataFill",
//  layout:"fitColumns",
// responsiveLayout:"collapse",
 rowHeight:30, 
 placeholder:"No Data Available",
//  selectable:true,
//  dataTree:true,
//  dataTreeStartExpanded:true,
 groupStartOpen:false,
 printAsHtml:true,
//  printHeader:`<img src = '/private/files/WhatsApp Image 2022-10-20 at 6.19.02 PM.jpeg'>`,
 printFooter:"<h2>Example Table Footer<h2>",
 groupBy:groupBy,
 groupHeader:function(value, count, data, group){
     //value - the value all members of this group share
     //count - the number of rows in this group
     //data - an array of all the row data objects in this group
     //group - the group component for the group

     return value + "<span style=' margin-left:0px;'>(" + count + "   )</span>";
 },
 groupToggleElement:"header",
//  groupBy:groupbyD.length >0 ? groupbyD : "",
//  textDirection: frappe.utils.is_rtl() ? "rtl" : "ltr",

 columns: columns,
 
 // [
 // 	{formatter:"rowSelection", titleFormatter:"rowSelection", hozAlign:"center", headerSort:false, cellClick:function(e, cell){
 // 		cell.getRow().toggleSelect();
 // 	  }},
 // 	{
 // 		title:"Name", field:"name", width:200,
 // 	},
 // 	{title:"Group", field:"item_group", width:200},
 // ],
 // [
 // {title:"Name", field:"name" , formatter:"link" , formatterParams:{
 // 	labelField:"name",
 // 	urlPrefix:`/app/${doct}/`,
     
 // }},
 // {title:"Customer", field:"customer" },
 // {title:"Total", field:"net_total" , bottomCalc:"sum",},

 // ],
 
 data: data
});

}
