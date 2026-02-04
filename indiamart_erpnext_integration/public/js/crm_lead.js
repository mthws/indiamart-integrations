frappe.ui.form.on('CRM Lead', {
    refresh:function (frm) {
		$('div').find('.document-link[data-doctype="Indiamart Lead"]').remove();
		if (frm.is_new() == undefined && frm.doc.query_id_cf!=undefined) {

			frappe.call('indiamart_erpnext_integration.indiamart_erpnext_integration.doctype.indiamart_lead.indiamart_lead.get_connected_indiamart_lead', {
				query_id_cf: frm.doc.query_id_cf
			}).then(r => {
				console.log(r,'r')
				if (r.message && r.message != undefined) {
					let count=r.message.length
					let link = $(`
			<div class="document-link" data-doctype="Indiamart Lead">
				<div class="document-link-badge" data-doctype="Indiamart Lead"> <span class="count">${count}</span> <a
					class="badge-link">Indiamart Lead</a> </div> <span class="open-notification hidden"
				title="Open Indiamart Lead"> </span></div>
			`);

					link.on('click', function () {
						frappe.route_options = {
							'name': ['in', r.message]
						};
						frappe.set_route("List", "Indiamart Lead", "List");

					})
					// Try to append after CRM Deal, or fallback to append to dashboard
                    let target = $('div').find('.document-link[data-doctype="CRM Deal"]');
                    if(target.length > 0){
                        target.after(link);
                    } else {
                         // Fallback: append to the first dashboard section found or last doc link
                         let lastLink = $('div').find('.document-link').last();
                         if(lastLink.length > 0) lastLink.after(link);
                    }
				}
			})
		}  
    }
})