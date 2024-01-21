odoo.define('ev_access_export_import.access_export_import', function (require) {
    'use strict';

    var core = require("web.core");
    var ListController = require("web.ListController");
    var DataExport = require("web.DataExport");
    var ImportMenu = require("base_import.ImportMenu");
    const FavoriteMenu = require('web.FavoriteMenu');
    var _t = core._t;


    ListController.include({
        _onDirectExportData() {
            var self = this;
            var actionID = self.controlPanelProps.action.id;
            var modelName = self.controlPanelProps.action.res_model;

            if (actionID === 208 || actionID === 484 || actionID === 55) {
                this.getSession().user_has_group('ev_access_export_import.group_export_res_partner').then(function (has_group) {
                    if (has_group) {
                        return self._rpc({
                            model: 'ir.exports',
                            method: 'search_read',
                            args: [[], ['id']],
                            limit: 1,
                        }).then(() => self._getExportDialogWidget().export())
                    } else {
                        return;
                    }
                });

            } else if (actionID === 209 || actionID === 55) {
                this.getSession().user_has_group('ev_access_export_import.group_export_res_partner_ncc').then(function (has_group) {
                    if (has_group) {
                        return self._rpc({
                            model: 'ir.exports',
                            method: 'search_read',
                            args: [[], ['id']],
                            limit: 1,
                        }).then(() => self._getExportDialogWidget().export())
                    } else {
                        return;
                    }
                });
            } else if (modelName == 'product.product' || modelName == 'product.template') {
                this.getSession().user_has_group('ev_access_export_import.group_export_product').then(function (has_group) {
                    if (has_group) {
                        return self._rpc({
                            model: 'ir.exports',
                            method: 'search_read',
                            args: [[], ['id']],
                            limit: 1,
                        }).then(() => self._getExportDialogWidget().export())
                    } else {
                        return;
                    }
                });
            } else {
                this.getSession().user_has_group('ev_access_export_import.group_export').then(function (has_group) {
                    if (has_group) {
                        return self._rpc({
                            model: 'ir.exports',
                            method: 'search_read',
                            args: [[], ['id']],
                            limit: 1,
                        }).then(() => self._getExportDialogWidget().export())
                    } else {
                        return;
                    }

                });
            }
        }

    });

    DataExport.include({
        _onExportData() {
            var self = this;
            var actionID = self.__parentedParent.controlPanelProps.action.id;
            var modelName = self.record.model;
            if (actionID == 208 || actionID == 484 || actionID === 55) {
                this.getSession().user_has_group('ev_access_export_import.group_export_res_partner').then(function (has_group) {
                    if (has_group) {
                        let exportedFields = self.$('.o_export_field').map((i, field) => ({
                                name: $(field).data('field_id'),
                                label: field.textContent,
                            }
                        )).get();
                        let exportFormat = self.$exportFormatInputs.filter(':checked').val();
                        self._exportData(exportedFields, exportFormat, self.idsToExport);
                    } else {
                        return;
                    }
                });
            } else if (actionID === 209 || actionID === 55) {
                this.getSession().user_has_group('ev_access_export_import.group_export_res_partner_ncc').then(function (has_group) {
                    if (has_group) {
                        let exportedFields = self.$('.o_export_field').map((i, field) => ({
                                name: $(field).data('field_id'),
                                label: field.textContent,
                            }
                        )).get();
                        let exportFormat = self.$exportFormatInputs.filter(':checked').val();
                        self._exportData(exportedFields, exportFormat, self.idsToExport);
                    } else {
                        return;
                    }
                });
            } else if (modelName == 'product.product' || modelName == 'product.template') {
                this.getSession().user_has_group('ev_access_export_import.group_export_product').then(function (has_group) {
                    if (has_group) {
                        let exportedFields = self.$('.o_export_field').map((i, field) => ({
                                name: $(field).data('field_id'),
                                label: field.textContent,
                            }
                        )).get();
                        let exportFormat = self.$exportFormatInputs.filter(':checked').val();
                        self._exportData(exportedFields, exportFormat, self.idsToExport);
                    } else {
                        return;
                    }
                });
            } else {
                this.getSession().user_has_group('ev_access_export_import.group_export').then(function (has_group) {
                    if (has_group) {
                        let exportedFields = self.$('.o_export_field').map((i, field) => ({
                                name: $(field).data('field_id'),
                                label: field.textContent,
                            }
                        )).get();
                        let exportFormat = self.$exportFormatInputs.filter(':checked').val();
                        self._exportData(exportedFields, exportFormat, self.idsToExport);
                    } else {
                        return;
                    }
                })
            }
        }
    });


    class ImportMenuInherit extends ImportMenu {
        _onImportClick() {
            var self = this;

            var actionID = self.env.action.id;
            var modelName = self.env.action.res_model;
            if (actionID == 208 || actionID == 484 || actionID === 55) {
                this.model.env.session.user_has_group('ev_access_export_import.group_import_res_partner').then(function (has_group) {
                    if (has_group) {
                        const action = {
                            type: 'ir.actions.client',
                            tag: 'import',
                            params: {
                                model: self.model.config.modelName,
                                context: self.model.config.context,
                            }
                        };
                        self.trigger('do-action', {action: action});
                    } else {
                        return;
                    }
                })
            } else if (actionID === 209 || actionID === 55) {
                this.model.env.session.user_has_group('ev_access_export_import.group_import_res_partner_ncc').then(function (has_group) {
                    if (has_group) {
                        const action = {
                            type: 'ir.actions.client',
                            tag: 'import',
                            params: {
                                model: self.model.config.modelName,
                                context: self.model.config.context,
                            }
                        };
                        self.trigger('do-action', {action: action});
                    } else {
                        return;
                    }
                })
            } else if (modelName == 'product.product' || modelName == 'product.template') {
                this.model.env.session.user_has_group('ev_access_export_import.group_import_product').then(function (has_group) {
                    if (has_group) {
                        const action = {
                            type: 'ir.actions.client',
                            tag: 'import',
                            params: {
                                model: self.model.config.modelName,
                                context: self.model.config.context,
                            }
                        };
                        self.trigger('do-action', {action: action});
                    } else {
                        return;
                    }
                })
            } else {
                this.model.env.session.user_has_group('ev_access_export_import.group_import').then(function (has_group) {
                    if (has_group) {
                        const action = {
                            type: 'ir.actions.client',
                            tag: 'import',
                            params: {
                                model: self.model.config.modelName,
                                context: self.model.config.context,
                            }
                        };
                        self.trigger('do-action', {action: action});
                    } else {
                        return;
                    }
                })
            }
        }
    }

    FavoriteMenu.registry.add('import-menu', ImportMenuInherit, 1);
    return ImportMenuInherit
});
