frappe.pages['imaging'].on_page_load = function(wrapper) {

        new xray(wrapper)
}

xray = Class.extend(
        {
                init:function(wrapper){
                        this.page = frappe.ui.make_app_page({
                                parent : wrapper,
                                title: "Imaging",
                                single_column : true
                        });
                        this.groupbyD = []
                        this.currDate =  frappe.datetime.get_today()
                        this.make()

                        // this.grouping_cols()
                },
                make:function(){


                        let me = this


                        $(frappe.render_template(frappe.dashbard_page.body, me)).appendTo(me.page.main)

                },


        }




)
let imaging = `

<iframe
src="http://217.217.217.241:8042/ui/app/index.html#/"
width="100%" height="800px" style="border:1px solid black;"
name="targetframe"
allowTransparency="true"
allowfullscreen = "true"



>
</iframe>


`
frappe.dashbard_page = {
        body : imaging
}
