frappe.pages["patient-information"].on_page_load = function (wrapper) {
  new WardManagement(wrapper)
}

WardManagement = Class.extend({
  init: function (wrapper) {
    this.page = frappe.ui.make_app_page({
      parent: wrapper,
      title: "Patient Information",
      single_column: true,
    })
    $(".page-head").hide()
    this.make()

    // this.make_grouping_btn()
    // this.grouping_cols()
  },
  make: function () {
    let me = this

    $(frappe.render_template("patient_information", me)).appendTo(me.page.main)
    let room_list = ``
    let ul_nav = $("#nav_ul").empty()
    let room_sel = ""
    let room = ""
  },
})
