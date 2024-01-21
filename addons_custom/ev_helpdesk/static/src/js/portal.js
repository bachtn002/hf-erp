odoo.define('ev_helpdesk.portal', function(require){
    'use strict';
    var publicWidget = require('web.public.widget');
    const {_t, qweb} = require('web.core');
    const ajax = require('web.ajax');
    var rpc = require('web.rpc');

    publicWidget.registry.portalHelpdeskRequest = publicWidget.Widget.extend({
        selector: '.o_portal_submenu',
        events: {
            'click .submit-ticket-rating-button': '_onCreateTicketRating',
            'click .create-rating': 'createRating',
            'click .set-back-to-draft': '_onSetTicketToDraft',
            'click .set-to-cancel': '_onSetTicketToCancel',
        },


        /**
         * @override
         */
        start: function (){
            this.default_root_question = null;
            var self = this;
            return this._super.apply(this, arguments).then(function(){
                self._getRootQuestion()
                self._getColorForStages()
                var create_rating = document.getElementsByClassName('create-rating')
                if (create_rating) {
                    for(var i=0; i<create_rating.length; i++){
                        create_rating[i].addEventListener('click', self.createRating);
                    }
                }
                //add even for button submit
                var submit_rating = document.getElementsByClassName('submit-ticket-rating-button')
                if (submit_rating.length >0) {
                    submit_rating[0].addEventListener('click', self._onCreateTicketRating);

                }
                //add even for button set to daft
                var set_back_to_draft = document.getElementsByClassName('set-back-to-draft')
                if (set_back_to_draft.length >0) {
                    set_back_to_draft[0].addEventListener('click', self._onSetTicketToDraft);

                }
                //add even for button set to daft
                var set_back_to_cancel = document.getElementsByClassName('set-to-cancel')
                if (set_back_to_cancel.length >0) {
                    set_back_to_cancel[0].addEventListener('click', self._onSetTicketToCancel);

                }
            })
        },

        _onCreateTicketRating: function (ev){
            ev.preventDefault();
            var ticket_id = parseInt(localStorage.getItem("current_ticket_id"))
            var ticket_rating_value = parseInt(localStorage.getItem("ticket_rating_value"))
            var mess_element = document.getElementById('notify_messages')
            var feedbackValue = document.getElementById("ticket-feedback-comment").value;
            rpc.query({
                model: 'helpdesk.ticket',
                method: 'create_ticket_rating',
                args: [
                    ticket_id,
                    ticket_rating_value,
                    feedbackValue
                ]
            }).then(() => {
                //hide feedback
                var ticket_message_feedback_div = document.getElementsByClassName('ticket-message-feedback')
                if (ticket_message_feedback_div){
                    ticket_message_feedback_div[0].style.setProperty('display', 'none')
                }
                //Show thanks messages
                mess_element.style.removeProperty('display')
                mess_element.innerHTML = _t("Cảm ơn vì đánh giá của bạn!")
                setTimeout(() => {
                    mess_element.style.setProperty('display', 'none')
                    var ticket_rating_div = document.getElementsByClassName('ticket-rating')
                    if (ticket_rating_div) {
                        ticket_rating_div[0].style.removeProperty('display')
                    }
                }, 5000)
            })
        },

        createRating: function (ev) {
            ev.preventDefault();
            var ticket_related = parseInt($(ev.currentTarget).data('id'))
            var rating_value = parseInt(ev.currentTarget.id);
            var mess_element = document.getElementById('notify_messages')
            if (!rating_value) {
                if (mess_element) {
                    mess_element.style.removeProperty('display')
                    mess_element.innerHTML = _t("There is no such rating value")
                }
            } else{
                //save rating value in localStorage since target is a button submit feedback
                localStorage.setItem("current_ticket_id", ticket_related);
                localStorage.setItem("ticket_rating_value", rating_value);
                //remove rating icon
                var ticket_rating_div = document.getElementsByClassName('ticket-rating')
                if (ticket_rating_div){
                    ticket_rating_div[0].style.setProperty('display', 'none')
                }
                //show feedback
                var ticket_message_feedback_div = document.getElementsByClassName('ticket-message-feedback')
                if (ticket_message_feedback_div){
                    ticket_message_feedback_div[0].style.removeProperty('display')
                }
            }
        },

        _onSetTicketToDraft: function (ev) {
            ev.preventDefault();
            var ticket_related = parseInt($(ev.currentTarget).data('id'))
            rpc.query({
                model: 'helpdesk.ticket',
                method: 'action_set_to_draft',
                args: [[ticket_related]]
            }).then(() => {
                //reload
                window.location.reload();
            })
        },

        _onSetTicketToCancel: function (ev) {
            ev.preventDefault();
            var ticket_related = parseInt($(ev.currentTarget).data('id'))
            rpc.query({
                model: 'helpdesk.ticket',
                method: 'action_set_to_cancel',
                args: [[ticket_related]]
            }).then(() => {
                //reload
                window.location.reload();
            })
        },

        /**
         *
         * @returns {root_question}
         * @private
         */
        _getRootQuestion: function(){
            var self = this;
            return this._rpc({
                'model': 'question.question',
                'method': 'get_root_question',
                'args': [],
            }).then((result)=>{
                self.default_root_question = result
                var url = '/my/helpdesk/'+ this.default_root_question.toString()
                document.getElementById("create-helpdesk-request").href = url;
            })
        },

        /**
         *
         * @returns {root_question}
         * @private
         */
        _getColorForStages: function(){
            var self = this;
            return this._rpc({
                'model': 'helpdesk.stage',
                'method': 'get_color_stages',
                'args': [],
            }).then((result)=>{
                var colors_stages = document.getElementsByClassName('stage-color')
                for(var i=0;i<colors_stages.length; i++){
                    let color_code = result[parseInt(colors_stages[i].id)]
                    colors_stages[i].style.setProperty('background-color',color_code)
                }
            })
        },
    })
})