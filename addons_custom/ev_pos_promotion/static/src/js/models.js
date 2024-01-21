odoo.define('ev_pos_promotion.models', function (require) {
    "use strict"

    const models = require('point_of_sale.models');
    const now = new Date();
    const date = moment(now).format('YYYY-MM-DD');


    models.load_models([{
        model: 'pos.promotion',
        label: 'Promotion',
        fields: ['name', 'start_date', 'end_date', 'start_time', 'end_time',
                'company_id', 'type', 'partner_groups', 'partner_groups_not', 'partner_ids_not', 'priority', 'product_id', 'check_promotion',
                'x_promotion_condition_or', 'x_partner_not_ids', 'vaction_ids', 'x_promotion_apply_or','promotion_type_id',
                'rule_apply_promotion', 'partner_ids_without_group',
                'apply_all_pos_config', 'apply_manual_pos_config', 'pos_configs',
                'apply_all_res_partner_apply', 'apply_manual_res_partner_apply',
                'apply_all_res_partner_not_apply', 'apply_manual_res_partner_not_apply', 'x_accumulate'],
        domain: (self) => {
            let domain = [
                ['state', '=', 'active'],
                ['start_date', '<=', date],
                ['end_date', '>=', date]
            ];
            if (self.config_id)
                 domain.push('|',['apply_all_pos_config','=', true],['pos_configs', 'in', [self.config_id]]);
            return domain;
        },
        loaded: (self, res) => {
            self.db.addPromotions(res);
        }
    }], {after: 'pos.session'});


    models.load_fields('custom.weekdays',
        ['name', 'code']
    );
    models.load_fields('pos.session',
        ['id', 'name', 'config_id']
    );

    models.load_fields('res.partner',['partner_groups']);
    models.load_models([{
        model: 'custom.weekdays',
        label: 'Customer Weekdays',
        fields: ['name', 'code'],
        loaded: (self, res) => {
            self.db.addCustomWeekdays(res);
        }
    }]);
    return models;

});
