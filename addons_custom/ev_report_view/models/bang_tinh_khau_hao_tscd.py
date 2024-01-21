from datetime import datetime

from odoo import api, fields, models, _


class BangTinhKhauHaoTSCD(models.TransientModel):
    _name = "bang.tinh.khau.hao.tscd"

    tents = fields.Char("Name")
    mats = fields.Char("X code")
    ts_id = fields.Char("ID")
    ngaytinhkh = fields.Char("First Description Date")
    sokyhk = fields.Char("Method number")
    nguyengia = fields.Float("Original value", digits=(14, 0))
    gtbatdaukh = fields.Float("Depreciated start value", digits=(14, 0))
    gtdakh = fields.Float("Depreciated value", digits=(14, 0))
    gtkhtrongky = fields.Float("Depreciated Value Period", digits=(14, 0))
    gtconlai = fields.Float("Residual Value", digits=(14, 0))
    gttbtrongky = fields.Float("Average value period", digits=(14, 0))
    trangthai = fields.Char("Status")
    report_id = fields.Char()


class BangTinhKhauHaoTSCDWizard(models.TransientModel):
    _name = "bang.tinh.khau.hao.tscd.wizard"

    from_date = fields.Date('From date')
    to_date = fields.Date('To date')

    def create_report(self):
        self.ensure_one()
        from_date = self.from_date.strftime("%d/%m/%Y")
        if self.to_date:
            to_date = self.to_date.strftime("%d/%m/%Y")
        else:
            to_date = from_date

        t = datetime.now().strftime('%Y%m%d%H%M%S')
        report_id = f'{t}.{self.env.user.id}'

        sql = """
INSERT INTO
    bang_tinh_khau_hao_tscd (
        tents,
        mats,
        ts_id,
        ngaytinhkh,
        sokyhk,
        nguyengia,
        gtbatdaukh,
        gtdakh,
        gtkhtrongky,
        gtconlai,
        gttbtrongky,
        trangthai,
        report_id
    )
select tents,
       mats,
       id,
       ngaytinhkh,
       sokyhk,
       nguyengia,
       gtbatdaukh,
       case
           when gtdakh is not null then gtdakh
           else 0 end    as  gtdakh,
       sum(gtkhtrongky)      gtkhtrongky,
       case
           when gtdakh is not null then gtbatdaukh - gtdakh
           else gtbatdaukh end as gtconlai,
       sum(gttbtrongky)      gttbtrongky,
       case
           when trangthai = 'open' then 'Đang chạy'
           when trangthai = 'close' then 'Đã đóng'
           when trangthai = 'draft' then 'Dự thảo'
           else null end as  trangthai,
           %s
from (SELECT b.name                           tents,
             b.x_code                         mats,
             b.id                             id,
             to_date(to_char(b.first_depreciation_date + INTERVAL '7 hours', 'dd/mm/yyyy'),
                     'dd/mm/yyyy')            ngaytinhkh,
             b.method_number                  sokyhk,
             b.original_value                 nguyengia,
             case
                 when b.already_depreciated_amount_import is not null
                     then b.original_value - b.already_depreciated_amount_import
                 else b.original_value end as gtbatdaukh,
             (select sum(am.amount_total)
              from account_move am
                       join account_asset aa on am.asset_id = aa.id
              where aa.id = b.id
                and am.state = 'posted'
                and to_date(to_char(am.date + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy') <=
                    to_date('%s', 'dd/mm/yyyy')
              )                     as gtdakh,
             sum(a.amount_total)              gtkhtrongky,
             0                             as gtconlai,
             avg(a.amount_total)              gttbtrongky,
             b.state                          trangthai
      from account_move a
               join account_asset b on b.id = a.asset_id
      WHERE b.x_asset_type = 'assets'
        and a.state = 'posted'
        and b.state in ('open', 'close')
        and to_date(to_char(a.date + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy') >= to_date('%s', 'dd/mm/yyyy')
        and to_date(to_char(a.date + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy') <= to_date('%s', 'dd/mm/yyyy')
      group by b.id, tents, mats, nguyengia, gtbatdaukh, gtdakh, gtconlai, ngaytinhkh, trangthai

      union all

      SELECT b.name                           tents,
             b.x_code                         mats,
             b.id                             id,
             to_date(to_char(b.first_depreciation_date + INTERVAL '7 hours', 'dd/mm/yyyy'),
                     'dd/mm/yyyy')            ngaytinhkh,
             b.method_number                  sokyhk,
             b.original_value                 nguyengia,
             case
                 when b.already_depreciated_amount_import is not null
                     then b.original_value - b.already_depreciated_amount_import
                 else b.original_value end as gtbatdaukh,
             (select sum(am.amount_total)
              from account_move am
                       join account_asset aa on am.asset_id = aa.id
              where aa.id = b.id
                and am.state = 'posted'
                and to_date(to_char(am.date + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy') <=
                    to_date('%s', 'dd/mm/yyyy')
              )                     as gtdakh,
             0                                gtkhtrongky,
             0                                gtconlai,
             0                                gttbtrongky,
             b.state                          trangthai

      from account_asset b
               left join account_move a on b.id = a.asset_id
               join account_account c on c.id = b.account_asset_id
      where b.x_asset_type = 'assets'
        and b.state != 'model'
--         and b.original_value = 0
        and to_date(to_char(b.first_depreciation_date + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy') >=
            to_date('%s', 'dd/mm/yyyy')
        and to_date(to_char(b.first_depreciation_date + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy') <=
            to_date('%s', 'dd/mm/yyyy')
      group by b.id, tents, mats, nguyengia, ngaytinhkh, gtdakh, sokyhk, gtbatdaukh, trangthai
     ) as asset_tracking
group by id, tents, mats, nguyengia, gtbatdaukh, ngaytinhkh, sokyhk, gtdakh, trangthai
        """
        self.env.cr.execute(sql % (report_id
                                   , to_date
                                   , from_date
                                   , to_date
                                   , to_date
                                   , from_date
                                   , to_date))
        self.env.cr.commit()
        return {
            'name': _('Spreadsheet depreciation'),
            'view_mode': 'tree',
            'res_model': 'bang.tinh.khau.hao.tscd',
            'domain': [('report_id', '=', report_id)],
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'search_view_id': self.env.ref('ev_report_view.bang_tinh_khau_hao_tscd_search').id
        }
