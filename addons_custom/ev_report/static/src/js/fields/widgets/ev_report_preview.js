odoo.define("ev_report.EVReportPreview", function (require) {
    "use strict";

    var FieldHtml = require("web_editor.field.html");
    var field_registry = require("web.field_registry");
    var core = require("web.core");
    var rpc = require("web.rpc");

    var qweb = core.qweb;
    var _lt = core._lt;

    var EVReportPreview = FieldHtml.extend({
        description: _lt("Report Preview"),
        className: "oe_form_field oe_form_field_html ev_report_preview",
        events: _.extend(
            {
                "click .ev_btn_zoom_in": "_onClickToggleZoom",
                "click .ev_btn_zoom_out": "_onClickToggleZoom",
                "change .js_item_per_page": "_onChangeItemPerPage",
                "change .js_current_page": "_onChangeCurrentPage",
            },
            FieldHtml.prototype.events
        ),
        /**
         * @override
         */
        init: function (parent, name, record, options) {
            this._super.apply(this, arguments);
            this.isPreviewZoom = false;
            this.currentPage = record.data.current_page;
            this.totalPage = record.data.total_page;
            this.itemPerPage = record.data.item_per_page;
            this.hidePaging = record.data.hide_paging;
        },

        //--------------------------------------------------------------------------
        // Handle
        //--------------------------------------------------------------------------

        _onClickToggleZoom: function (e) {
            this.isPreviewZoom = !this.isPreviewZoom;
            this._zoomPreviewView();
            this._renderPreviewTopBar();
        },

        _onChangeItemPerPage: function (ev) {
            let input = $(ev.currentTarget);
            let itemPerPage = this._getInputValueNumber(input);
            if (itemPerPage == this.itemPerPage) return;
            this.itemPerPage = itemPerPage;
            this._renderPreviewTopBar();
            this._reloadReport();
        },

        _onChangeCurrentPage: function (ev) {
            let input = $(ev.currentTarget);
            let currentPage = this._getInputValueNumber(input);
            if (currentPage == this.currentPage) return;
            this.currentPage = currentPage;
            if (currentPage > this.totalPage) {
                currentPage = this.totalPage;
            }
            this.currentPage = currentPage;
            this._renderPreviewTopBar();
            this._reloadReport();
        },

        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------

        /**
         * @private
         */
        _renderReadonly: function () {
            this._super.apply(this, arguments);
            if (this.value) {
                this._renderPreviewTopBar();
                this._applyTableStyle();
            }
        },

        _renderPreviewTopBar: function () {
            let $oldTopBar = this.$el.find(".ev_preview_top_bar");
            if ($oldTopBar) {
                $oldTopBar.remove();
            }
            let $previewTopBar = $(
                qweb.render("ev_report.EVReportTopBar", { widget: this })
            );
            $previewTopBar.prependTo(this.$el);
        },

        _applyTableStyle: function () {
            let table_widths = [];
            let $trs = this.$el.find("table.dataframe thead tr");
            $trs.each((i, tr) => {
                table_widths[i] = 0;
                $(tr)
                    .find("th")
                    .each((j, th) => {
                        table_widths[i] += $(th).width() || 100;
                    });
            });
            this.$el
                .find("table.dataframe")
                .css({ width: Math.max(...table_widths) + "px" });
        },

        _getInputValueNumber: function (input) {
            let val = input.val();
            let num = "";
            for (let i = 0; i < val.length; i++) {
                if (isNaN(val.charAt(i))) continue;
                num += val.charAt(i);
            }
            num = parseInt(num);
            input.val(num);
            return num;
        },

        _zoomPreviewView: function () {
            if (this.isPreviewZoom) {
                this.$el.addClass("ev_zoom");
            } else {
                this.$el.removeClass("ev_zoom");
            }
        },

        _reloadReport: function () {
            var ids = this.recordData.id ? [this.recordData.id] : [];
            var vals = {
                item_per_page: this.itemPerPage,
                current_page: this.currentPage,
            };
            var self = this;
            rpc.query({
                model: this.model,
                method: "paging_config",
                args: [ids, vals],
            }).then(function (result) {
                self.itemPerPage = result.item_per_page;
                self.currentPage = result.current_page;
                self.totalPage = result.total_page;
                self.value = result.preview_html;
                self._renderReadonly();
            });
        },
    });

    field_registry.add("ev_report_preview", EVReportPreview);

    return EVReportPreview;
});
