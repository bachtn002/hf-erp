odoo.define('ev_helpdesk.question', function(require){
    'use strict';
    var publicWidget = require('web.public.widget');
    const {_t, qweb} = require('web.core');
    const ajax = require('web.ajax');
    var rpc = require('web.rpc');

    publicWidget.registry.portalHelpdeskQuestion = publicWidget.Widget.extend({
        selector: '.ev_helpdesk_custom_card_header',
        events: {
            'click .submit-question-rating-button': '_onCreateQuestionRating',
            'click .button_question_back': '_onButtonQuestionBack',
            'click .create-rating': 'createRating',
            'click .save_question_id_clicked': 'saveQuestionIdClicked',
            'click .modal': '_onCloseModalPopup',
            'click .image-hover': '_onShowPopupImage',
            'click .button_submit_ticket': '_onSubmitTicket',
            'mouseleave .image-hover': '_onMouseleaveImage',
            'mousemove .image-hover': '_onMoveImage',
            'mouseover .image-hover': '_onMoverImage',
            'change .o_input_file': '_onImageChange',
        },

        _onMoverImage: function (ev) {
            var answer_id = parseInt(ev.currentTarget.id);
            var text_mover = '#' + answer_id.toString()

            var image_id = 'damn-preview-' + answer_id.toString()
            var mess_element = document.getElementById(image_id).style.removeProperty('display')
            $(text_mover).mouseover(function () {
                var box = '#damn-box-' + answer_id.toString()
                $(box).show();
            });
        },

        _onMouseleaveImage: function (ev) {
            var answer_id = parseInt(ev.currentTarget.id);
            var text_mover = '#' + answer_id.toString()

            var image_id = 'damn-preview-' + answer_id.toString()
            var mess_element = document.getElementById(image_id).style.display = "none"

            $(text_mover).mouseleave(function () {
                var box = '#damn-box-' + answer_id.toString()
                $(box).hide();
            });
        },

        _onMoveImage: function () {
            $(document).mousemove(function (e) {
                $(".damn-box").offset({
                    left: e.pageX,
                    top: e.pageY + 20
                });
            });
        },


        _onShowPopupImage: function (ev) {
            var answer_id = parseInt(ev.currentTarget.id);
            var modal_id = 'myModal' + answer_id.toString()
            // Get the modal
            var modal = document.getElementById(modal_id);
            // Get the image and insert it inside the modal - use its "alt" text as a caption
            modal.style.display = "block";
        },


        _onCloseModalPopup: function (ev){
            // Get the modal
            var modal = document.getElementById(ev.currentTarget.id)
            // When the user clicks anywhere outside of the modal, close it
            if(ev.target === modal){
                modal.style.display = "none";
            }
        },


        /**
         * @override
         */
        start: function (){
            var self = this;
            this.question_rating_value = null;
            return this._super.apply(this, arguments)
                .then(function () {
                    //remove local storage for history question pages
                    localStorage.removeItem("period_question_list")
                })
        },

        /**
         *
         * @private
         */
        _onButtonQuestionBack: function (ev) {
            ev.stopPropagation()
            var current_question_id = $('.button_question_back').data('id')
             var period_question_list = JSON.parse(localStorage.getItem("period_question_list"));
             if (period_question_list){
                 if(period_question_list.length > 0){
                     // if current question is root => back to my/tickets
                     if (period_question_list[period_question_list.length - 1] === current_question_id) {
                         // remove root question in history pages
                         period_question_list.splice(period_question_list.length - 1);
                         // update local storage with root question removed
                         localStorage.setItem("period_question_list", JSON.stringify(period_question_list));
                         window.history.back();
                     }
                     // else return period page's content
                     var route = '/my/help_custom/' + period_question_list[period_question_list.length - 1]
                     // remove last question in history and update local storage
                     period_question_list.splice(period_question_list.length - 1);
                     localStorage.setItem("period_question_list", JSON.stringify(period_question_list));
                     ajax.jsonRpc(route, 'call').then((value) => {
                         $('.ev_helpdesk_custom_card_header').html(value);
                     });
                 }else{
                     window.history.back();
                 }
             }else{
                 window.history.back();
            }
        },

        _onSubmitTicket: function (ev) {
            //Prevent multiple form submission on multiple clicks
            var btn_submit = $('.button_submit_ticket')[0];
            var ticket_form = $("#ticket_form")

            if(ticket_form[0].checkValidity()){
                btn_submit.disabled = true;
                btn_submit.innerHTML = _t('Đang gửi ...');
                ticket_form.submit();
            }
        },


        saveQuestionIdClicked: function (ev) {
            ev.stopPropagation()
            var question_id = $(ev.currentTarget).data('next_url')
            var new_period_question = $(ev.currentTarget).data('period_question')


            // update with new history page's question content
            var period_question = JSON.parse(localStorage.getItem("period_question_list"));
            if (period_question && period_question !== 'null'){
                period_question.push(new_period_question)
                localStorage.setItem("period_question_list", JSON.stringify(period_question));
            }else{
                localStorage.setItem("period_question_list", JSON.stringify([new_period_question]));
            }
            // save last question click use for create new ticket or rating
            // localStorage.setItem("last_question_clicked", question_id);

            var route = '/my/help_custom/' + question_id
            ajax.jsonRpc(route, 'call').then((value)=>{
                $('.ev_helpdesk_custom_card_header').html(value);
            });
        },


        createRating: function (ev){
            var question_related = $(ev.currentTarget).data('question_related')
            var rating_value = parseInt(ev.currentTarget.id);
            var mess_element = document.getElementById('notify_messages')
            var group_rating_icon = document.getElementsByClassName('group-rating-icon')
            if (!question_related){
                if(mess_element){
                    for (var i = 0; i < group_rating_icon.length; i++) {
                        group_rating_icon[i].style.setProperty('display', 'none')
                    }
                    mess_element.style.removeProperty('display')
                    mess_element.innerHTML = _t("You already rating! Thank you")
                }
            }else if(rating_value){
                this.question_rating_value = rating_value
                //Change header message
                var question_name_div = document.getElementsByClassName('question-name')
                if (question_name_div){
                    question_name_div[0].style.setProperty('display', 'none')
                }
                var message_thanks_div = document.getElementsByClassName('message-thanks')
                if (message_thanks_div){
                    message_thanks_div[0].style.removeProperty('display')
                }
                //Change body
                var group_rating_div = document.getElementsByClassName('group-rating')
                if (group_rating_div){
                    group_rating_div[0].style.setProperty('display', 'none')
                }
                var message_feedback_div = document.getElementsByClassName('message-feedback')
                if (message_feedback_div){
                    message_feedback_div[0].style.removeProperty('display')
                }
            }
        },

        _onCreateQuestionRating: function (ev) {
            var question_related = $(ev.currentTarget).data('question_related')
            var feedbackValue = document.getElementById("feedback-comment").value;

            const url = window.location.protocol + '//' + window.location.host + '/my/tickets'
            rpc.query({
                model: 'question.question',
                method: 'create_question_rating',
                args: [
                    question_related,
                    this.question_rating_value,
                    feedbackValue
                ]
            }).then(() => {
                //Back to manage ticket page
                var mess_element = document.getElementById('notify_messages')
                var message_feedback_div = document.getElementsByClassName('message-feedback')
                if (mess_element) {
                    message_feedback_div[0].style.setProperty('display', 'none')
                    mess_element.style.removeProperty('display')
                    mess_element.innerHTML = _t("Cảm ơn vì đánh giá của bạn")
                }
                setTimeout(function () {
                    window.open(url, '_self');
                }, 3000)

            })

        }
    })
})