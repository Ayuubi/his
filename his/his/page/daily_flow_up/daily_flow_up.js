frappe.pages['daily-flow-up'].on_page_load = function(wrapper) {
    new Dialyisis(wrapper);
}

Dialyisis = Class.extend({
    init: function(wrapper) {
        this.page = frappe.ui.make_app_page({
            parent: wrapper,
            title: "Daily Flow UP",
            single_column: true
        });
        this.groupbyD = [];
        this.selectedDate = frappe.datetime.get_today(); // Set today's date as default
        this.filterTypeValue = 'flowdate'; // Default to Flow UP Date
        this.make();
    },
    make: function() {
        let me = this;

        // Filter selection for Flow UP Date or Work Date
        this.filterType = this.page.add_field({
            fieldtype: 'Select',
            fieldname: 'filter_type',
            label: "Filter By",
            options: [
                { value: 'flowdate', label: 'Flow UP Today' },
                { value: 'date', label: 'Worked Today' }
            ],
            default: 'flowdate', // Default to Flow UP Date
            change: () => {
                this.filterTypeValue = this.filterType.get_value();
                me.setupdata_table(); // Fetch data based on selection
            }
        });

        // Single Date field for both filters
        let dateField = this.page.add_field({
            fieldtype: 'Date',
            fieldname: 'date',
            label: "Select Date",
            default: this.selectedDate, // Automatically set to today's date
            change: () => {
                this.selectedDate = dateField.get_value();
                me.setupdata_table(); // Fetch data when date changes
            }
        });

        // Call setupdata_table to load data automatically on page load
        me.setupdata_table();
        
        $(frappe.render_template(frappe.dashbard_page.body, me)).appendTo(me.page.main);
    },

    setupdata_table: function() {
        let selectedFilter = this.filterType.get_value();
        let selectedDate = this.selectedDate;

        // Only fetch data if a filter type is selected and a date is provided
        if (this.filterTypeValue && selectedDate) {
            let filterArgs = {
                flowdate: selectedFilter === 'flowdate' ? selectedDate : null,
                date: selectedFilter === 'date' ? selectedDate : null
            };

            frappe.call({
                method: "his.api.get_orders.get_dialysis",
                args: filterArgs,
                callback: function(r) {
                    let tbldata = r.message;

                    let columns = [
                        { title: "No", field: "id", formatter: "rownum" },
                        { title: "PID", field: "patient", headerFilter: "input" },
                        { title: "Patient Name", field: "patient_name", headerFilter: "input" },
                        { title: "Last", field: "lastDate", headerFilter: "input" },
                        { title: "Flow UP", field: "Today", headerFilter: "input" },
                        { title: "Age", field: "age", headerFilter: "input" },
                        { title: "Entry Weight", field: "entry_weight", headerFilter: "input" },
                        { title: "Target Weight", field: "target_weight", headerFilter: "input" },
                        { title: "Exit Weight", field: "exit_weight", headerFilter: "input" }
                    ];

                    this.table = new Tabulator("#daily", {
                        layout: "fitDataStretch",
                        rowHeight: 30,
                        columns: columns,
                        data: tbldata
                    });

                    this.table.on("rowClick", function(e, rows) {
                        frappe.new_doc("Dialysis History", { patient: rows._row.data.patient, practitioner: rows._row.data.department });
                    });
                }
            });
        }
    }
});

// HTML Template
let emergen = `
<div class="container">
    <div class="row">
        <div id="daily" style="min-width: 100%"></div>
    </div>
</div>
`;

frappe.dashbard_page = {
    body: emergen
};

// Date formatter
formatter = function(cell, formatterParams, onRendered) {
    return frappe.datetime.prettyDate(cell.getValue(), 1);
}