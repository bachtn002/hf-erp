odoo.define('ev_helpdesk..portal.chatter', function (require){
    'use strict';
    var portalChatter = require('portal.chatter');
    var PortalChatter = portalChatter.PortalChatter;

/**
 * PortalChatter
 *
 * Extends Frontend Chatter to handle rating
 */
PortalChatter.include({
    events: _.extend({}, PortalChatter.prototype.events, {
        'click .show_image': '_onShowPopupImage',
        'click .modal': '_onCloseModalPopup',
    }),
    xmlDependencies: (PortalChatter.prototype.xmlDependencies || [])
        .concat([
            '/ev_helpdesk/static/src/xml/portal_chatter.xml',
        ]),


    _onShowPopupImage: function (ev) {
        var attachment = parseInt(ev.currentTarget.id);
        var modal_id = 'myModal' + attachment.toString()
        // Get the modal
        var modal = document.getElementById(modal_id);
        // Get the image and insert it inside the modal - use its "alt" text as a caption
        modal.style.display = "block";
    },

    _onCloseModalPopup: function (ev) {
        // Get the modal
        var modal = document.getElementById(ev.currentTarget.id)
        // When the user clicks anywhere outside of the modal, close it
        if (ev.target === modal) {
            modal.style.display = "none";
        }
    },
})
})