# -*- coding: utf-8 -*-


from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError, except_orm


class DataWarehouse(models.Model):
    _name = 'ev.data.warehouse'
    _order = 'create_date desc'
    _inherit = 'mail.thread'

    def _default_company(self):
        return self.env.user.company_id.id

    name = fields.Char('Name')
    date = fields.Date('Date', default=lambda self: fields.Date.today())
    company_id = fields.Many2one('res.company', string="Company", default=_default_company, track_visibility='always')
    lines = fields.One2many('ev.data.location', 'data_warehouse_id', string="Lines")
    state = fields.Selection([('draft', 'Draft'), ('get_data', 'Get Data'), ('done', 'Done')],
                             'State', default="draft")
    type = fields.Selection([('start','Start'),('daily','Daily')])


    def unlink(self):
        for record in self:
            if record.state == 'done':
                raise UserError(
                    _('You cannot delete record state Done.'))
        return super(DataWarehouse, self).unlink()


    def action_load_data(self):
        self.ensure_one()
        date_time_str = str(self.date) + ' 23:59:59'
        date_time_obj = datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S')
        sql = """
            INSERT INTO ev_data_location(name, data_warehouse_id, location_id,
            create_date, create_uid,write_uid,write_date,company_id)
            SELECT 
                complete_name,
                (%d) as data_warehouse_id,
                id location_id,
                now() as create_date,
                (%d) as create_uid,
                (%d) as write_uid,
                now() as write_date,
                (%d) company_id
            FROM stock_location
            where 
            active = 't'
            and company_id = %d
            and usage = 'internal';
        """
        params = (
            self.id, self.env.user.id, self.env.user.id, self.company_id.id, self.company_id.id)
        self._cr.execute(sql % params)
        for line in self.lines:
            line.date = date_time_obj
            sql1 = """
            INSERT INTO ev_data_location_detail(data_location_id, product_id, location_id, create_date, create_uid,write_uid,write_date,company_id)
            SELECT 
            (%d) data_location_id,
            product_id, (%d) location_id, now() as create_date,
            (%d) as create_uid,
            (%d) as write_uid,
            now() as write_date,
            (%d) company_id
            FROM(
            SELECT * FROM
            (SELECT
                pp.id as product_id,
                to_char(SUM(quantity), 'FM9999999999.9999990') tonkho
             FROM stock_quant quant
                JOIN product_product pp ON quant.product_id = pp.id
                             LEFT JOIN stock_production_lot spl ON spl.id = quant.lot_id
             WHERE quant.location_id = %d
             GROUP BY pp.id, spl.id) quantity_quant
         EXCEPT
         SELECT
                product_id,
                to_char(sum(ton_kho), 'FM9999999999.9999990') tonkho
        FROM(SELECT
            a1.product_id,
            sum(sl) ton_kho
        FROM
            (
                SELECT p.id product_id, l.id lot_id, 
                -sum(case when u1.id = u2.id then sml.qty_done else sml.qty_done * round(1/u1.factor,5) / round(1/u2.factor,5) end) sl
                    FROM stock_move_line sml
                    LEFT JOIN product_product p on sml.product_id = p.id
                    LEFT JOIN stock_production_lot l on sml.lot_id = l.id
                    INNER JOIN product_product pp ON sml.product_id = pp.id 
                    INNER JOIN product_template ptl ON ptl.id =  pp.product_tmpl_id
                    LEFT JOIN uom_uom u1 ON u1.id =  sml.product_uom_id
                    INNER JOIN uom_uom u2 ON u2.id =  ptl.uom_id
                    WHERE (sml.date + INTERVAL '7 hours' ) <= '%s'
                    AND sml.state = 'done'
                    AND sml.location_id = %d
                    AND sml.location_dest_id != %d
                    and ptl.type = 'product'
                    GROUP BY p.id, l.id
                    UNION ALL
                    SELECT p.id product_id, l.id lot_id,
                    sum(case when u1.id = u2.id then sml.qty_done else sml.qty_done * round(1/u1.factor,5) / round(1/u2.factor,5) end) sl
                    FROM stock_move_line sml
                    LEFT JOIN product_product p on sml.product_id = p.id
                    LEFT JOIN stock_production_lot l on sml.lot_id = l.id
                    INNER JOIN product_product pp ON sml.product_id = pp.id 
                    INNER JOIN product_template ptl ON ptl.id =  pp.product_tmpl_id
                    LEFT JOIN uom_uom u1 ON u1.id =  sml.product_uom_id
                    INNER JOIN uom_uom u2 ON u2.id =  ptl.uom_id
                    WHERE (sml.date + INTERVAL '7 hours' ) <= '%s'
                    AND sml.state = 'done'
                    AND sml.location_id != %d
                    AND sml.location_dest_id = %d
                    and ptl.type = 'product'
                    GROUP BY p.id, l.id
                    ) a1
                    GROUP BY a1.product_id, a1.lot_id) a
                    --WHERE a.ton_kho <> 0
                    GROUP BY product_id
                    UNION
                    SELECT * FROM
                    (SELECT
                product_id,
                to_char(sum(ton_kho), 'FM9999999999.9999990') tonkho
        FROM(SELECT
            a1.product_id,
            sum(sl) ton_kho
            FROM
                    (
                SELECT p.id product_id, l.id lot_id, 
                -sum(case when u1.id = u2.id then sml.qty_done else sml.qty_done * round(1/u1.factor,5) / round(1/u2.factor,5) end) sl
                    FROM stock_move_line sml
                    LEFT JOIN product_product p on sml.product_id = p.id
                    LEFT JOIN stock_production_lot l on sml.lot_id = l.id
                    INNER JOIN product_product pp ON sml.product_id = pp.id 
                    INNER JOIN product_template ptl ON ptl.id =  pp.product_tmpl_id
                    LEFT JOIN uom_uom u1 ON u1.id =  sml.product_uom_id
                    INNER JOIN uom_uom u2 ON u2.id =  ptl.uom_id
                    WHERE (sml.date + INTERVAL '7 hours' ) <= '%s'
                    AND sml.state = 'done'
                    AND sml.location_id = %d
                    AND sml.location_dest_id != %d
                    and ptl.type = 'product'
                    GROUP BY p.id, l.id
                    UNION ALL
                    SELECT p.id product_id, l.id lot_id,
                    sum(case when u1.id = u2.id then sml.qty_done else sml.qty_done * round(1/u1.factor,5) / round(1/u2.factor,5) end) sl
                    FROM stock_move_line sml
                    LEFT JOIN product_product p on sml.product_id = p.id
                    LEFT JOIN stock_production_lot l on sml.lot_id = l.id
                    INNER JOIN product_product pp ON sml.product_id = pp.id 
                    INNER JOIN product_template ptl ON ptl.id =  pp.product_tmpl_id
                    LEFT JOIN uom_uom u1 ON u1.id =  sml.product_uom_id
                    INNER JOIN uom_uom u2 ON u2.id =  ptl.uom_id
                    WHERE (sml.date + INTERVAL '7 hours' ) <= '%s'
                    AND sml.state = 'done'
                    AND sml.location_id != %d
                    AND sml.location_dest_id = %d
                    and ptl.type = 'product'
                    GROUP BY p.id, l.id
                    ) a1
                    GROUP BY a1.product_id) a
                    --WHERE a.ton_kho <> 0
                    GROUP BY product_id) quantity_move
                    EXCEPT 
                    SELECT
                         pp.id as product_id,
                         to_char(SUM(quantity), 'FM9999999999.9999990') tonkho
                 FROM stock_quant quant
                    JOIN product_product pp ON quant.product_id = pp.id
                 WHERE quant.location_id = %d
                 GROUP BY pp.id) a;
            """
            params1 = (
                line.id,line.location_id.id, self.env.user.id, self.env.user.id, self.company_id.id,line.location_id.id, date_time_obj,
                line.location_id.id, line.location_id.id,date_time_obj, line.location_id.id, line.location_id.id,
                date_time_obj, line.location_id.id, line.location_id.id, date_time_obj, line.location_id.id,
                line.location_id.id, line.location_id.id
            )
            self._cr.execute(sql1 % params1)
            self._cr.commit()
            self._calculate_data_detail(line, date_time_obj)
        self.state = 'get_data'

    def _calculate_data_detail(self, line, date):
        sql="""
        UPDATE  ev_data_location_detail a
         SET qty_quant = case when d.qty <> 0 then d.qty else 0 end
         FROM ev_data_location_detail b
         INNER JOIN (SELECT c.product_id product_id, c.location_id location_id, sum(c.quantity) qty
         FROM stock_quant c, ev_data_location e, ev_data_location_detail f
         WHERE 
         c.product_id = f.product_id 
         and c.location_id = e.location_id 
         and e.id = f.data_location_id 
         and e.id = %d
         GROUP BY c.product_id, c.location_id) d 
         ON b.location_id = d.location_id
         and b.product_id = d.product_id
         WHERE 
         a.id = b.id;
         UPDATE ev_data_location_detail a
         SET qty_move = case when d.qty <> 0 then d.qty else 0 end
         FROM ev_data_location_detail b
         INNER JOIN (SELECT
            a.location_id,
            a.product_id,
            sum(a.ton_kho) qty
            FROM(SELECT
            a1.location_id,
            a1.product_id,
            sum(sl) ton_kho
            FROM
            (
        SELECT sml.location_id location_id, p.id product_id, l.id lot_id,
        -sum(case when u1.id = u2.id then sml.qty_done else sml.qty_done * round(1/u1.factor,5) / round(1/u2.factor,5) end) sl
            FROM stock_move_line sml
            LEFT JOIN product_product p on sml.product_id = p.id
            LEFT JOIN stock_production_lot l on sml.lot_id = l.id
            INNER JOIN product_product pp ON sml.product_id = pp.id 
            INNER JOIN product_template ptl ON ptl.id =  pp.product_tmpl_id
            LEFT JOIN uom_uom u1 ON u1.id =  sml.product_uom_id
            INNER JOIN uom_uom u2 ON u2.id =  ptl.uom_id
            WHERE (sml.date + INTERVAL '7 hours' ) <= '%s'
            AND sml.state = 'done'
            AND sml.location_id = %d
            AND sml.location_dest_id != %d
            GROUP BY sml.location_id, p.id, l.id
            UNION ALL
            SELECT sml.location_dest_id location_id, p.id product_id, l.id lot_id,
            sum(case when u1.id = u2.id then sml.qty_done else sml.qty_done * round(1/u1.factor,5) / round(1/u2.factor,5) end) sl
            FROM stock_move_line sml
            LEFT JOIN product_product p on sml.product_id = p.id
            LEFT JOIN stock_production_lot l on sml.lot_id = l.id
            INNER JOIN product_product pp ON sml.product_id = pp.id 
            INNER JOIN product_template ptl ON ptl.id =  pp.product_tmpl_id
            LEFT JOIN uom_uom u1 ON u1.id =  sml.product_uom_id
            INNER JOIN uom_uom u2 ON u2.id =  ptl.uom_id
            WHERE (sml.date + INTERVAL '7 hours' ) <= '%s'
            AND sml.state = 'done'
            AND sml.location_id != %d
            AND sml.location_dest_id = %d
            GROUP BY sml.location_dest_id, p.id, l.id
            ) a1
            GROUP BY a1.product_id, a1.location_id) a, ev_data_location b, ev_data_location_detail c
            WHERE 
            -- a.ton_kho <> 0 and 
            a.product_id = c.product_id
            and b.id = c.data_location_id
            and b.id = %d
            GROUP BY a.product_id, a.location_id) d
            ON b.location_id = d.location_id
            and b.product_id = d.product_id 
            WHERE 
            a.id = b.id;
            update ev_data_location_detail a
            set date = b.date, company_id = b.company_id
            from ev_data_location b
            where 
            a.data_location_id = b.id
            and b.id = %d;
            update ev_data_location_detail a
            set qty_quant = 0
            from ev_data_location b
            where a.data_location_id = b.id
            and a.qty_quant is NULL
            and b.id = %d;
            update ev_data_location_detail a
            set qty_move = 0
            from ev_data_location b
            where a.data_location_id = b.id
            and a.qty_move is NULL
            and b.id = %d;
            DELETE FROM ev_data_location_detail a
            USING ev_data_location b
            WHERE a.qty_quant = 0
            and a.qty_move = 0
            and a.data_location_id = b.id
            and b.id = %d;
            update ev_data_location_detail a
            set qty_difference = case when a.qty_quant < a.qty_move then (a.qty_move-a.qty_quant) else (a.qty_quant-a.qty_move) end
            from ev_data_location b
            where a.data_location_id = b.id
            and b.id = %d;
        """
        params = (line.id, date, line.location_id.id, line.location_id.id, date, line.location_id.id, line.location_id.id, line.id,
                  line.id, line.id, line.id, line.id, line.id)
        self._cr.execute(sql % params)
        self._cr.commit()

    def _get_move_values(self, qty, location_id, location_dest_id, line_detail):
        self.ensure_one()
        date = self.date
        return {
            'name': line_detail.product_id.name or '',
            'product_id': line_detail.product_id.id,
            'product_uom': line_detail.product_id.uom_id.id,
            'product_uom_qty': qty,
            'date_deadline': date,
            'date': date,
            'company_id': self.company_id.id,
            'x_update_data': True,
            'state': 'draft',
            'location_id': location_id,
            'location_dest_id': location_dest_id,
            'move_line_ids': [(0, 0, {
                'product_id': line_detail.product_id.id,
                'product_uom_qty': 0,  # bypass reservation here
                'product_uom_id': line_detail.product_id.uom_id.id,
                'qty_done': qty,
                'location_id': location_id,
                'location_dest_id': location_dest_id,
                'date': date,
                'state': 'draft'
            })]
        }


    def action_update(self):
        self.ensure_one()
        for line in self.lines:
            for line_detail in line.lines:
                diff = line_detail.qty_quant - line_detail.qty_move
                if diff < 0:
                    vals = self._get_move_values(abs(diff), line_detail.location_id.id,
                                                 line_detail.product_id.property_stock_inventory.id, line_detail)
                elif diff > 0:
                    vals = self._get_move_values(abs(diff), line_detail.product_id.property_stock_inventory.id,
                                                 line.location_id.id, line_detail)
                move_id = self.env['stock.move'].create(vals)
                line_detail.stock_move_id = move_id
                sql="""
                update stock_move set state = 'done' where id = %d;
                update stock_move_line a
                set state = 'done'
                from stock_move b
                where 
                b.id = a.move_id
                and b.id = %d;
                """
                self._cr.execute(sql % (move_id.id, move_id.id))
        self.state = 'done'
        self.action_update_daily_manual()

    def check_data_daily(self):
        today = datetime.today()
        today_get = datetime.strftime(today + timedelta(hours=7), '%Y-%m-%d')
        today_view = datetime.strftime(today + timedelta(hours=7), '%Y-%m-%d %H:%M:%S')
        date_time_str = today_get + ' 23:59:59'
        date_time_obj = datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S')
        check_quant = self.create({
            'name': 'Kiểm tra dữ liệu ngày ' + today_view,
            'date': today_get,
            'company_id': self.env.user.company_id.id,
            'state': 'draft',
            'type': 'daily'
        })
        # check_quant.action_load_data()
        # check_quant.action_update_daily_manual()
        sql = """
                INSERT INTO ev_data_location(name, data_warehouse_id, location_id,
                create_date, create_uid,write_uid,write_date,company_id)
                SELECT
                    complete_name,
                    (%d) as data_warehouse_id,
                    id location_id,
                    now() as create_date,
                    (%d) as create_uid,
                    (%d) as write_uid,
                    now() as write_date,
                    (%d) company_id
                FROM stock_location
                where
                active = 't'
                and company_id = %d
                and usage = 'internal'
                order by id;
                """
        params = (
            check_quant.id, self.env.user.id, self.env.user.id, check_quant.company_id.id, check_quant.company_id.id)
        self._cr.execute(sql % params)
        self._cr.commit()
        for line in check_quant.lines:
            line.date = date_time_obj
            sql1 = """
                    INSERT INTO ev_data_location_detail(data_location_id, product_id, location_id, create_date, create_uid,write_uid,write_date,company_id)
                    SELECT
                    (%d) data_location_id,
                    product_id, (%d) location_id, now() as create_date,
                    (%d) as create_uid,
                    (%d) as write_uid,
                    now() as write_date,
                    (%d) company_id
                    FROM(
                    SELECT * FROM
                    (SELECT
                        pp.id as product_id,
                        to_char(SUM(quantity), 'FM9999999999.9999990') tonkho
                     FROM stock_quant quant
                        JOIN product_product pp ON quant.product_id = pp.id
                                     LEFT JOIN stock_production_lot spl ON spl.id = quant.lot_id
                     WHERE quant.location_id = %d
                     GROUP BY pp.id, spl.id) quantity_quant
                 EXCEPT
                 SELECT
                        product_id,
                        to_char(sum(ton_kho), 'FM9999999999.9999990') tonkho
                FROM(SELECT
                    a1.product_id,
                    sum(sl) ton_kho
                FROM
                    (
                        SELECT p.id product_id, l.id lot_id,
                        -sum(case when u1.id = u2.id then sml.qty_done else sml.qty_done * round(1/u1.factor,5) / round(1/u2.factor,5) end) sl
                            FROM stock_move_line sml
                            LEFT JOIN product_product p on sml.product_id = p.id
                            LEFT JOIN stock_production_lot l on sml.lot_id = l.id
                            INNER JOIN product_product pp ON sml.product_id = pp.id
                            INNER JOIN product_template ptl ON ptl.id =  pp.product_tmpl_id
                            LEFT JOIN uom_uom u1 ON u1.id =  sml.product_uom_id
                            INNER JOIN uom_uom u2 ON u2.id =  ptl.uom_id
                            WHERE (sml.date + INTERVAL '7 hours' ) <= '%s'
                            AND sml.state = 'done'
                            AND sml.location_id = %d
                            AND sml.location_dest_id != %d
                            and ptl.type = 'product'
                            GROUP BY p.id, l.id
                            UNION ALL
                            SELECT p.id product_id, l.id lot_id,
                            sum(case when u1.id = u2.id then sml.qty_done else sml.qty_done * round(1/u1.factor,5) / round(1/u2.factor,5) end) sl
                            FROM stock_move_line sml
                            LEFT JOIN product_product p on sml.product_id = p.id
                            LEFT JOIN stock_production_lot l on sml.lot_id = l.id
                            INNER JOIN product_product pp ON sml.product_id = pp.id
                            INNER JOIN product_template ptl ON ptl.id =  pp.product_tmpl_id
                            LEFT JOIN uom_uom u1 ON u1.id =  sml.product_uom_id
                            INNER JOIN uom_uom u2 ON u2.id =  ptl.uom_id
                            WHERE (sml.date + INTERVAL '7 hours' ) <= '%s'
                            AND sml.state = 'done'
                            AND sml.location_id != %d
                            AND sml.location_dest_id = %d
                            and ptl.type = 'product'
                            GROUP BY p.id, l.id
                            ) a1
                            GROUP BY a1.product_id, a1.lot_id) a
                            GROUP BY product_id
                            UNION
                            SELECT * FROM
                            (SELECT
                        product_id,
                        to_char(sum(ton_kho), 'FM9999999999.9999990') tonkho
                FROM(SELECT
                    a1.product_id,
                    sum(sl) ton_kho
                    FROM
                            (
                        SELECT p.id product_id, l.id lot_id,
                        -sum(case when u1.id = u2.id then sml.qty_done else sml.qty_done * round(1/u1.factor,5) / round(1/u2.factor,5) end) sl
                            FROM stock_move_line sml
                            LEFT JOIN product_product p on sml.product_id = p.id
                            LEFT JOIN stock_production_lot l on sml.lot_id = l.id
                            INNER JOIN product_product pp ON sml.product_id = pp.id
                            INNER JOIN product_template ptl ON ptl.id =  pp.product_tmpl_id
                            LEFT JOIN uom_uom u1 ON u1.id =  sml.product_uom_id
                            INNER JOIN uom_uom u2 ON u2.id =  ptl.uom_id
                            WHERE (sml.date + INTERVAL '7 hours' ) <= '%s'
                            AND sml.state = 'done'
                            AND sml.location_id = %d
                            AND sml.location_dest_id != %d
                            and ptl.type = 'product'
                            GROUP BY p.id, l.id
                            UNION ALL
                            SELECT p.id product_id, l.id lot_id,
                            sum(case when u1.id = u2.id then sml.qty_done else sml.qty_done * round(1/u1.factor,5) / round(1/u2.factor,5) end) sl
                            FROM stock_move_line sml
                            LEFT JOIN product_product p on sml.product_id = p.id
                            LEFT JOIN stock_production_lot l on sml.lot_id = l.id
                            INNER JOIN product_product pp ON sml.product_id = pp.id
                            INNER JOIN product_template ptl ON ptl.id =  pp.product_tmpl_id
                            LEFT JOIN uom_uom u1 ON u1.id =  sml.product_uom_id
                            INNER JOIN uom_uom u2 ON u2.id =  ptl.uom_id
                            WHERE (sml.date + INTERVAL '7 hours' ) <= '%s'
                            AND sml.state = 'done'
                            AND sml.location_id != %d
                            AND sml.location_dest_id = %d
                            and ptl.type = 'product'
                            GROUP BY p.id, l.id
                            ) a1
                            GROUP BY a1.product_id) a
                            GROUP BY product_id) quantity_move
                            EXCEPT
                            SELECT
                                 pp.id as product_id,
                                 to_char(SUM(quantity), 'FM9999999999.9999990') tonkho
                         FROM stock_quant quant
                            JOIN product_product pp ON quant.product_id = pp.id
                         WHERE quant.location_id = %d
                         GROUP BY pp.id) a;
                    """
            params1 = (
                line.id, line.location_id.id, self.env.user.id, self.env.user.id, check_quant.company_id.id,
                line.location_id.id, date_time_obj,
                line.location_id.id, line.location_id.id, date_time_obj, line.location_id.id, line.location_id.id,
                date_time_obj, line.location_id.id, line.location_id.id, date_time_obj, line.location_id.id,
                line.location_id.id, line.location_id.id
            )
            self._cr.execute(sql1 % params1)
            self._cr.commit()
            check_quant._calculate_data_detail(line, date_time_obj)
        check_quant._action_update_daily(check_quant)

    def _action_update_daily(self, check_quant):
        self.ensure_one()
        quant_obj = self.env['stock.quant'].sudo()
        for line in check_quant.lines:
            for line_detail in line.lines:
                if line_detail.product_id.type == 'product':
                    if line_detail.qty_move > line_detail.qty_quant and line_detail.qty_quant > 0:
                        stock_quant = quant_obj.search(
                            [('product_id', '=', line_detail.product_id.id),
                             ('location_id', '=', line_detail.location_id.id)], limit=1)
                        if stock_quant:
                            stock_quant.quantity = stock_quant.quantity + (line_detail.qty_move - line_detail.qty_quant)
                            stock_quant.x_update_data = True
                            line_detail.stock_quant_id = stock_quant.id
                        else:
                            quant = quant_obj.create({
                                'product_id': line_detail.product_id.id,
                                'quantity': (line_detail.qty_move),
                                'company_id': line_detail.company_id.id,
                                'location_id': line_detail.location_id.id,
                                'reserved_quantity': 0,
                                'x_update_data': True
                            })
                            line_detail.stock_quant_id = quant.id
                    else:
                        stock_quant = quant_obj.search(
                            [('product_id', '=', line_detail.product_id.id),
                             ('location_id', '=', line_detail.location_id.id)], limit=1)
                        if stock_quant:
                            stock_quant.quantity = stock_quant.quantity - (line_detail.qty_quant - line_detail.qty_move)
                            stock_quant.x_update_data = True
                            line_detail.stock_quant_id = stock_quant.id
                        else:
                            quant = quant_obj.create({
                                'product_id': line_detail.product_id.id,
                                'quantity': (line_detail.qty_move),
                                'company_id': line_detail.company_id.id,
                                'location_id': line_detail.location_id.id,
                                'reserved_quantity': 0,
                                'x_update_data': True
                            })
                            line_detail.stock_quant_id = quant.id
        check_quant.state = 'done'

    def check_data_manual(self):
        today = datetime.today()
        today_get = datetime.strftime(today + timedelta(hours=7), '%Y-%m-%d')
        today_view = datetime.strftime(today + timedelta(hours=7), '%Y-%m-%d %H:%M:%S')
        date_time_str = today_get + ' 23:59:59'
        date_time_obj = datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S')
        # check_quant = self.create({
        #     'name': 'Kiểm tra dữ liệu ngày ' + today_view,
        #     'date': today_get,
        #     'company_id': self.env.user.company_id.id,
        #     'state': 'draft',
        #     'type': 'daily'
        # })
        # sql = """
        #         INSERT INTO ev_data_location(name, data_warehouse_id, location_id,
        #         create_date, create_uid,write_uid,write_date,company_id)
        #         SELECT
        #             complete_name,
        #             (%d) as data_warehouse_id,
        #             id location_id,
        #             now() as create_date,
        #             (%d) as create_uid,
        #             (%d) as write_uid,
        #             now() as write_date,
        #             (%d) company_id
        #         FROM stock_location
        #         where
        #         active = 't'
        #         and company_id = %d
        #         and usage = 'internal';
        #         """
        # params = (
        #     self.id, self.env.user.id, self.env.user.id, self.company_id.id, self.company_id.id)
        # self._cr.execute(sql % params)
        for line in self.lines:
            line.date = date_time_obj
            sql1 = """
                    INSERT INTO ev_data_location_detail(data_location_id, product_id, location_id, create_date, create_uid,write_uid,write_date,company_id)
                    SELECT 
                    (%d) data_location_id,
                    product_id, (%d) location_id, now() as create_date,
                    (%d) as create_uid,
                    (%d) as write_uid,
                    now() as write_date,
                    (%d) company_id
                    FROM(
                    SELECT * FROM
                    (SELECT
                        pp.id as product_id,
                        to_char(SUM(quantity), 'FM9999999999.9999990') tonkho
                     FROM stock_quant quant
                        JOIN product_product pp ON quant.product_id = pp.id
                                     LEFT JOIN stock_production_lot spl ON spl.id = quant.lot_id
                     WHERE quant.location_id = %d
                     GROUP BY pp.id, spl.id) quantity_quant
                 EXCEPT
                 SELECT
                        product_id,
                        to_char(sum(ton_kho), 'FM9999999999.9999990') tonkho
                FROM(SELECT
                    a1.product_id,
                    sum(sl) ton_kho
                FROM
                    (
                        SELECT p.id product_id, l.id lot_id,
                        -sum(case when u1.id = u2.id then sml.qty_done else sml.qty_done * round(1/u1.factor,5) / round(1/u2.factor,5) end) sl
                            FROM stock_move_line sml
                            LEFT JOIN product_product p on sml.product_id = p.id
                            LEFT JOIN stock_production_lot l on sml.lot_id = l.id
                            INNER JOIN product_product pp ON sml.product_id = pp.id 
                            INNER JOIN product_template ptl ON ptl.id =  pp.product_tmpl_id
                            LEFT JOIN uom_uom u1 ON u1.id =  sml.product_uom_id
                            INNER JOIN uom_uom u2 ON u2.id =  ptl.uom_id
                            WHERE (sml.date + INTERVAL '7 hours' ) <= '%s'
                            AND sml.state = 'done'
                            AND sml.location_id = %d
                            AND sml.location_dest_id != %d
                            and ptl.type = 'product'
                            GROUP BY p.id, l.id
                            UNION ALL
                            SELECT p.id product_id, l.id lot_id,
                            sum(case when u1.id = u2.id then sml.qty_done else sml.qty_done * round(1/u1.factor,5) / round(1/u2.factor,5) end) sl
                            FROM stock_move_line sml
                            LEFT JOIN product_product p on sml.product_id = p.id
                            LEFT JOIN stock_production_lot l on sml.lot_id = l.id
                            INNER JOIN product_product pp ON sml.product_id = pp.id 
                            INNER JOIN product_template ptl ON ptl.id =  pp.product_tmpl_id
                            LEFT JOIN uom_uom u1 ON u1.id =  sml.product_uom_id
                            INNER JOIN uom_uom u2 ON u2.id =  ptl.uom_id
                            WHERE (sml.date + INTERVAL '7 hours' ) <= '%s'
                            AND sml.state = 'done'
                            AND sml.location_id != %d
                            AND sml.location_dest_id = %d
                            and ptl.type = 'product'
                            GROUP BY p.id, l.id
                            ) a1
                            GROUP BY a1.product_id, a1.lot_id) a
                            GROUP BY product_id
                            UNION
                            SELECT * FROM
                            (SELECT
                        product_id,
                        to_char(sum(ton_kho), 'FM9999999999.9999990') tonkho
                FROM(SELECT
                    a1.product_id,
                    sum(sl) ton_kho
                    FROM
                            (
                        SELECT p.id product_id, l.id lot_id,
                        -sum(case when u1.id = u2.id then sml.qty_done else sml.qty_done * round(1/u1.factor,5) / round(1/u2.factor,5) end) sl
                            FROM stock_move_line sml
                            LEFT JOIN product_product p on sml.product_id = p.id
                            LEFT JOIN stock_production_lot l on sml.lot_id = l.id
                            INNER JOIN product_product pp ON sml.product_id = pp.id 
                            INNER JOIN product_template ptl ON ptl.id =  pp.product_tmpl_id
                            LEFT JOIN uom_uom u1 ON u1.id =  sml.product_uom_id
                            INNER JOIN uom_uom u2 ON u2.id =  ptl.uom_id
                            WHERE (sml.date + INTERVAL '7 hours' ) <= '%s'
                            AND sml.state = 'done'
                            AND sml.location_id = %d
                            AND sml.location_dest_id != %d
                            and ptl.type = 'product'
                            GROUP BY p.id, l.id
                            UNION ALL
                            SELECT p.id product_id, l.id lot_id,
                            sum(case when u1.id = u2.id then sml.qty_done else sml.qty_done * round(1/u1.factor,5) / round(1/u2.factor,5) end) sl
                            FROM stock_move_line sml
                            LEFT JOIN product_product p on sml.product_id = p.id
                            LEFT JOIN stock_production_lot l on sml.lot_id = l.id
                            INNER JOIN product_product pp ON sml.product_id = pp.id 
                            INNER JOIN product_template ptl ON ptl.id =  pp.product_tmpl_id
                            LEFT JOIN uom_uom u1 ON u1.id =  sml.product_uom_id
                            INNER JOIN uom_uom u2 ON u2.id =  ptl.uom_id
                            WHERE (sml.date + INTERVAL '7 hours' ) <= '%s'
                            AND sml.state = 'done'
                            AND sml.location_id != %d
                            AND sml.location_dest_id = %d
                            and ptl.type = 'product'
                            GROUP BY p.id, l.id
                            ) a1
                            GROUP BY a1.product_id) a
                            GROUP BY product_id) quantity_move
                            EXCEPT 
                            SELECT
                                 pp.id as product_id,
                                 to_char(SUM(quantity), 'FM9999999999.9999990') tonkho
                         FROM stock_quant quant
                            JOIN product_product pp ON quant.product_id = pp.id
                         WHERE quant.location_id = %d
                         GROUP BY pp.id) a;
                    """
            params1 = (
                line.id, line.location_id.id, self.env.user.id, self.env.user.id, self.company_id.id,
                line.location_id.id, date_time_obj,
                line.location_id.id, line.location_id.id, date_time_obj, line.location_id.id, line.location_id.id,
                date_time_obj, line.location_id.id, line.location_id.id, date_time_obj, line.location_id.id,
                line.location_id.id, line.location_id.id
            )
            self._cr.execute(sql1 % params1)
            self._calculate_data_detail(line, date_time_obj)
        self._action_update_daily_manual()

    def action_update_daily_manual(self):
        self.ensure_one()
        quant_obj = self.env['stock.quant'].sudo()
        for line in self.lines:
            for line_detail in line.lines:
                if line_detail.product_id.tracking in ('serial', 'lot'):
                    line_detail.unlink()
                    continue
                if line_detail.product_id.type == 'product':
                    if line_detail.qty_move > line_detail.qty_quant and line_detail.qty_quant > 0:
                        stock_quant = quant_obj.search(
                            [('product_id', '=', line_detail.product_id.id),
                             ('location_id', '=', line_detail.location_id.id)], limit=1)
                        if stock_quant:
                            stock_quant.sudo().quantity = stock_quant.sudo().quantity + (line_detail.qty_move - line_detail.qty_quant)
                            stock_quant.sudo().x_update_data = True
                            line_detail.stock_quant_id = stock_quant.sudo().id
                        else:
                            quant = quant_obj.create({
                                'product_id': line_detail.product_id.id,
                                'quantity': (line_detail.qty_move),
                                'company_id': line_detail.company_id.id,
                                'location_id': line_detail.location_id.id,
                                'reserved_quantity': 0,
                                'x_update_data': True
                            })
                            line_detail.stock_quant_id = quant.sudo().id
                    else:
                        stock_quant = quant_obj.search(
                            [('product_id', '=', line_detail.product_id.id),
                             ('location_id', '=', line_detail.location_id.id)], limit=1)
                        if stock_quant:
                            stock_quant.sudo().quantity = stock_quant.sudo().quantity - (line_detail.qty_quant - line_detail.qty_move)
                            stock_quant.sudo().x_update_data = True
                            line_detail.stock_quant_id = stock_quant.sudo().id
                        else:
                            quant = quant_obj.create({
                                'product_id': line_detail.product_id.id,
                                'quantity': (line_detail.qty_move),
                                'company_id': line_detail.company_id.id,
                                'location_id': line_detail.location_id.id,
                                'reserved_quantity': 0,
                                'x_update_data': True
                            })
                            line_detail.stock_quant_id = quant.sudo().id
        self.state = 'done'


class DataLocation(models.Model):
    _name = 'ev.data.location'

    name = fields.Char('Name')
    data_warehouse_id = fields.Many2one('ev.data.warehouse', 'Data Warehouse', ondelete='cascade')
    location_id = fields.Many2one('stock.location', 'Location')
    date = fields.Date('Date')
    company_id = fields.Many2one('res.company', string="Company")
    lines = fields.One2many('ev.data.location.detail','data_location_id','Lines')


class DataLocationDetail(models.Model):
    _name = 'ev.data.location.detail'

    name = fields.Char('Name')
    data_location_id = fields.Many2one('ev.data.location', 'Data Location', ondelete='cascade')
    location_id = fields.Many2one('stock.location', 'Location')
    product_id = fields.Many2one('product.product', 'Product')
    date = fields.Date('Date')
    uom_id = fields.Many2one('product.uom', "Product Uom")
    qty_move = fields.Float('Quantity Move', digits='Product Unit of Measure')
    qty_quant = fields.Float('Quantity Quant', digits='Product Unit of Measure')
    qty_difference = fields.Float('Quantity Difference', digits='Product Unit of Measure')
    stock_move_id = fields.Many2one('stock.move', 'Stock move')
    stock_quant_id = fields.Many2one('stock.quant', 'Stock quant')
    company_id = fields.Many2one('res.company', string="Company")
