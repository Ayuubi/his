// Copyright (c) 2023, Rasiin Tech and contributors
// For license information, please see license.txt
// Return true if SigWeb is present
function sigweb_ready() {
  return (typeof window.SetTabletState === 'function') &&
         (typeof window.GetSigImageB64 === 'function');
}

// Ensure SigWeb is present (since we included via hooks, we just check)
async function ensureSigWebLoaded() {
  if (!sigweb_ready()) {
    throw new Error("SigWebTablet.js not loaded or blocked by CSP");
  }
}

// Open a dialog that captures signature and returns a data URL
async function openSignatureDialog() {
  await ensureSigWebLoaded();

  return new Promise((resolve, reject) => {
    const d = new frappe.ui.Dialog({
      title: "Capture Signature",
      fields: [
        { fieldtype: "HTML", fieldname: "html", options:
          `<div style="margin-bottom:8px">Sign on the pad, then click <b>Done</b>.</div>
           <canvas id="sig-canvas" width="500" height="150"
                   style="border:1px solid #d0d4d9;border-radius:6px;"></canvas>
           <div class="mt-3">
             <button type="button" class="btn btn-sm btn-secondary" id="sig-clear">Clear</button>
           </div>`
        }
      ],
      primary_action_label: "Done",
      primary_action: () => {
        try {
          if (typeof NumberOfTabletPoints === 'function' && NumberOfTabletPoints() === 0) {
            frappe.msgprint("Please sign before clicking Done.");
            return;
          }
          GetSigImageB64((b64) => {
            try { SetTabletState(0, ctx, 0); } catch (e) {}
            try { Reset(); } catch (e) {}
            d.hide();
            if (!b64) return reject(new Error("No signature captured"));
            resolve('data:image/png;base64,' + b64);
          });
        } catch (e) {
          try { SetTabletState(0, ctx, 0); } catch (e2) {}
          try { Reset(); } catch (e3) {}
          d.hide();
          reject(e);
        }
      },
      secondary_action_label: "Cancel",
      secondary_action: () => {
        try { SetTabletState(0, ctx, 0); } catch (e) {}
        try { Reset(); } catch (e) {}
        d.hide();
        reject(new Error("Cancelled"));
      }
    });

    d.show();

    // set up canvas + start capture
    const canvas = d.$wrapper.find('#sig-canvas')[0];
    const ctx = canvas.getContext('2d');

    // (optional) tune output size; helps match canvas
    if (typeof SetDisplayXSize === 'function') SetDisplayXSize(canvas.width);
    if (typeof SetDisplayYSize === 'function') SetDisplayYSize(canvas.height);

    // Start tablet polling
    SetTabletState(1, ctx, 50);

    // Clear button
    d.$wrapper.find('#sig-clear').on('click', function() {
      try { ClearTablet(); } catch (e) {}
      // Some builds use ClearSigWindow(); either works if present
      if (typeof ClearSigWindow === 'function') ClearSigWindow();
    });

    // Safety: stop capture if dialog is closed without actions
    d.onhide = () => {
      try { SetTabletState(0, ctx, 0); } catch (e) {}
      try { Reset(); } catch (e) {}
    };
  });
}

// Capture FINGERPRINT via SigIDExtLite (returns data URL). requestType: 3 = PNG image
function captureTopazFingerprint() {
  return new Promise((resolve, reject) => {
    function onResponse(event) {
      try {
        const raw = event.target.getAttribute('SigIDExtLiteResponseAttributes');
        const out = JSON.parse(raw || '{}');
        document.removeEventListener('SigIDExtLiteResponseEvent', onResponse);
        if (out.status && out.outputString) {
          resolve('data:image/png;base64,' + out.outputString);
        } else {
          reject(new Error(out.message || 'Fingerprint capture failed / cancelled'));
        }
      } catch (e) {
        document.removeEventListener('SigIDExtLiteResponseEvent', onResponse);
        reject(e);
      }
    }
    document.addEventListener('SigIDExtLiteResponseEvent', onResponse, false);

    const message = { requestType: 3, winPositionMode: 2 }; // center the capture dialog
    const el = document.createElement('SigIDExtLiteDataElement');
    el.setAttribute('SigIDExtLiteRequestAttributes', JSON.stringify(message));
    document.documentElement.appendChild(el);
    const evt = document.createEvent('Events');
    evt.initEvent('SigIDExtLiteRequestEvent', true, false);
    el.dispatchEvent(evt);
  });
}

// Optional: enroll template instead of just image
function enrollFingerprintTemplate() {
  return new Promise((resolve, reject) => {
    function onResponse(event) {
      const raw = event.target.getAttribute('SigIDExtLiteResponseAttributes');
      const out = JSON.parse(raw || '{}');
      document.removeEventListener('SigIDExtLiteResponseEvent', onResponse);
      if (out.status && out.outputString) resolve(out.outputString); // base64 template
      else reject(new Error(out.message || 'Enrollment failed'));
    }
    document.addEventListener('SigIDExtLiteResponseEvent', onResponse, false);
    const message = { requestType: 1, winPositionMode: 2 };
    const el = document.createElement('SigIDExtLiteDataElement');
    el.setAttribute('SigIDExtLiteRequestAttributes', JSON.stringify(message));
    document.documentElement.appendChild(el);
    const evt = document.createEvent('Events');
    evt.initEvent('SigIDExtLiteRequestEvent', true, false);
    el.dispatchEvent(evt);
  });
}

// Attach a captured dataURL to a specific child-row field via server method below
async function attach_to_child(opts) {
  const r = await frappe.call({
    method: 'his.api.save_biometrics.save_image_to_child',
    args: opts
  });
  return r?.message;
}

frappe.ui.form.on('Consent Surgery Form', {
    refresh: function(frm) {
        if (!frm.is_new()) {
            frm.add_custom_button(__('Print Consent Form'), function() {
    // This sets the default print format for this session and opens the dialog
    frm.meta.default_print_format = "Consent Form Endoscopy";
    frm.print_doc();
});
        }
    }
});
frappe.ui.form.on('Representors', {
  // Button fieldname: capture_signature
  capture_signature: async function (frm, cdt, cdn) {
    try {
      const data_url = await openSignatureDialog();
      const file_url = await attach_to_child({
        parent_doctype: frm.doctype,
        parent_name: frm.docname,
        child_doctype: cdt,
        child_name: cdn,
        fieldname: 'signature',
        data_url
      });
      await frappe.model.set_value(cdt, cdn, 'signature', file_url);
      frm.refresh_field('representors'); // update your table fieldname if different
    } catch (e) {
      console.error(e);
      frappe.msgprint(__('Signature capture failed: {0}', [e.message || e]));
    }
  },


  // Button fieldname: capture_fingerprint
  capture_fingerprint: async function (frm, cdt, cdn) {
    try {
      const row = locals[cdt][cdn];
      const data_url = await captureTopazFingerprint();
      const file_url = await attach_to_child({
        parent_doctype: frm.doctype,
        parent_name: frm.docname,
        child_doctype: cdt,
        child_name: cdn,
        fieldname: 'fingerprint',      // Attach field on the child row
        data_url
      });
      await frappe.model.set_value(cdt, cdn, 'fingerprint', file_url);
      frm.refresh_field('representors'); // replace with your table fieldname if different
    } catch (e) {
      console.error(e);
      frappe.msgprint(__('Fingerprint capture failed: {0}', [e.message || e]));
    }
  }
});

