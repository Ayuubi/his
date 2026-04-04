// Copyright (c) 2026, Rasiin Tech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Reorder Level Monitor"] = {
  filters: [
    {
      fieldname: "company",
      label: "Company",
      fieldtype: "Link",
      options: "Company",
      default: "Shaafi Hospital",
    },
    {
      fieldname: "warehouse",
      label: "Warehouse",
      fieldtype: "Link",
      options: "Warehouse",
      description: "Leave blank to sum across ALL warehouses."
    },
    {
      fieldname: "status",
      label: "Status",
      fieldtype: "Select",
      options: "\nDANGER\nWARNING\nOK",
      description: "Optional filter"
    },
    {
      fieldname: "item_group",
      label: "Item Group",
      fieldtype: "Link",
      options: "Item Group"
    },
    {
      fieldname: "brand",
      label: "Brand",
      fieldtype: "Link",
      options: "Brand",
	  hidden: 1
    },
    {
      fieldname: "show_all_wh_total",
      label: "Show All-Warehouses Total",
      fieldtype: "Check",
      default: 1,
      description: "When a Warehouse is selected, still show total across ALL warehouses."
    },
    {
      fieldname: "only_stock_items",
      label: "Only Stock Items",
      fieldtype: "Check",
      default: 1
    },
  ],

//   formatter: function (value, row, column, data, default_formatter) {
//     value = default_formatter(value, row, column, data);

//     if (!data) return value;

//     // Color by status (cell styling)
//     if (column.fieldname === "status") {
//       if (data.status === "DANGER") {
//         value = `<span style="color:#b30000;font-weight:700;">${value}</span>`;
//       } else if (data.status === "WARNING") {
//         value = `<span style="color:#b36b00;font-weight:700;">${value}</span>`;
//       } else if (data.status === "OK") {
//         value = `<span style="color:#006b2d;font-weight:700;">${value}</span>`;
//       }
//     }

//     // Optional: highlight entire qty cell too
//     if (column.fieldname === "qty") {
//       if (data.status === "DANGER") {
//         value = `<span style="background:#ffe5e5;padding:2px 6px;border-radius:6px;">${value}</span>`;
//       } else if (data.status === "WARNING") {
//         value = `<span style="background:#fff3cd;padding:2px 6px;border-radius:6px;">${value}</span>`;
//       }
//     }

//     return value;
//   }

formatter: function (value, row, column, data, default_formatter) {
  value = default_formatter(value, row, column, data);
  if (!data) return value;

  // pick strong colors
  const styles = {
    DANGER:  { bg: "#ff3b30", fg: "#ffffff" }, // strong red
    WARNING: { bg: "#ffcc00", fg: "#000000" }, // strong yellow
    OK:      { bg: "#34c759", fg: "#ffffff" }  // green
  };

  const s = data.status;
  const st = styles[s] || null;

  // Strong status text
  if (column.fieldname === "status" && st) {
    return `<span style="font-weight:800;color:${st.bg};">${value}</span>`;
  }

  // Make Qty cell VERY visible (full width)
  if (column.fieldname === "qty" && st) {
    return `
      <div style="
        background:${st.bg};
        color:${st.fg};
        font-weight:800;
        text-align:right;
        padding:6px 8px;
        border-radius:8px;
        width:100%;
        box-sizing:border-box;
      ">${value}</div>`;
  }

  // Optional: also color All WH Total cell if you want
  if (column.fieldname === "all_wh_total" && st) {
    return `
      <div style="
        background:${st.bg}22;   /* light tint */
        color:#111;
        font-weight:700;
        text-align:right;
        padding:6px 8px;
        border-radius:8px;
        width:100%;
        box-sizing:border-box;
      ">${value}</div>`;
  }

  return value;
}
};