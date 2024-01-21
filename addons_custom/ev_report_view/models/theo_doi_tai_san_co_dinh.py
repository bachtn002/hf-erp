from datetime import datetime
from odoo import api, models, fields, _


class TheoDoiTaiSanCoDinh(models.TransientModel):
    _name = "theo.doi.tai.san.co.dinh"
    _description = "Fixed Asset Tracking"

    tracking_id = fields.Char("ID")
    tents = fields.Char("Name")
    mats = fields.Char("X code")
    nguyengia = fields.Float("Original value", digits=(14, 0))
    gtbatdaukh = fields.Float("Depreciated start value", digits=(14, 0))
    gtdakh = fields.Float("Depreciated value", digits=(14, 0))
    gtkhtrongky = fields.Float("Depreciated Value Period", digits=(14, 0))
    gtconlai = fields.Float("Residual Value", digits=(14, 0))
    gttbtrongky = fields.Float("Average value period", digits=(14, 0))
    ngaymua = fields.Char("Date Buy")
    ngaytinhkh = fields.Char("First Description Date")
    ngaygiam = fields.Char("Reduced date")
    sokyhk = fields.Char("Method number")
    ngayct = fields.Char("Document date")
    soct = fields.Char("License")
    tktaisan = fields.Char("Account Properties")
    tkkhauhao = fields.Char("Account Depreciation")
    tkchiphi = fields.Char("Expense Account")
    mabp = fields.Char("Part Code")
    maphi = fields.Char("Fee Code")
    tenphi = fields.Char("Fee Name")
    tenbp = fields.Char("Part Name")
    trangthai = fields.Char("Status")
    report_id = fields.Char('Report ID')


class TheoDoiTaiSanCoDinhWizard(models.TransientModel):
    _name = "theo.doi.tai.san.co.dinh.wizard"

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
    INSERT INTO theo_doi_tai_san_co_dinh (tracking_id, tents, mats, nguyengia, gtbatdaukh, gtdakh, gtkhtrongky, gtconlai, gttbtrongky, 
    ngaymua, ngaytinhkh, ngaygiam, sokyhk, ngayct, soct, tktaisan, tkkhauhao, tkchiphi, mabp, maphi, tenphi, tenbp, trangthai, report_id)
    select asset_tracking_b.id,
       asset_tracking_b.tents,
       asset_tracking_b.mats,
       asset_tracking_b.nguyengia,
       asset_tracking_b.gtbatdaukh,
       case
           when asset_tracking_b.gtdakh is not null then asset_tracking_b.gtdakh
           else 0 end                           as gtdakh,
       case
           when asset_tracking_b.gtkhtrongky is not null then asset_tracking_b.gtkhtrongky
           else 0 end                           as gtkhtrongky,
       case
           when asset_tracking_b.gtdakh is not null then asset_tracking_b.gtbatdaukh - asset_tracking_b.gtdakh
           else asset_tracking_b.gtbatdaukh end as gtconlai,
       asset_tracking_b.gttbtrongky,
       asset_tracking_b.ngaymua,
       asset_tracking_b.ngaytinhkh,
       asset_tracking_b.ngaygiam,
       asset_tracking_b.sokyhk,
       ct.ngayct,
       ct.soct,
       asset_tracking_b.tktaisan,
       asset_tracking_b.tkkhauhao,
       asset_tracking_b.tkchiphi,
       asset_tracking_b.mabp,
       asset_tracking_b.maphi,
       asset_tracking_b.tenphi,
       asset_tracking_b.tenbp,
       case
           when asset_tracking_b.trangthai = 'open' then 'Đang chạy'
           when asset_tracking_b.trangthai = 'close' then 'Đã đóng'
           when asset_tracking_b.trangthai = 'draft' then 'Dự thảo'
           else null end                        as trangthai,
        %s
from (select id,
             tents,
             mats,
             nguyengia,
             gtbatdaukh,
             gtdakh,
             sum(gtkhtrongky) gtkhtrongky,
             0 as             gtconlai,
             sum(gttbtrongky) gttbtrongky,
             ngaymua,
             ngaytinhkh,
             ngaygiam,
             sokyhk,
--        ngayct,
--        soct,
             tktaisan,
             tkkhauhao,
             tkchiphi,
             mabp,
             maphi,
             tenphi,
             tenbp,
             trangthai
      from (SELECT b.id                             id,
                   b.name                           tents,
                   b.x_code                         mats,
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
                   0                                gtconlai,
                   avg(a.amount_total)              gttbtrongky,
                   to_date(to_char(b.acquisition_date + INTERVAL '7 hours', 'dd/mm/yyyy'),
                           'dd/mm/yyyy')            ngaymua,
                   to_date(to_char(b.first_depreciation_date + INTERVAL '7 hours', 'dd/mm/yyyy'),
                           'dd/mm/yyyy')            ngaytinhkh,
                   case
                       when (select to_date(to_char(am.date + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy')
                             from account_move am
                                      left join account_move_line aml on aml.move_id = am.id
                                      left join account_account amlaa on amlaa.id = aml.account_id
                             WHERE am.asset_id = b.id
                               and am.state = 'posted'
                               and amlaa.code like ('811')) is not null then (select to_date(
                                                                                             to_char(am.date + INTERVAL '7 hours', 'dd/mm/yyyy'),
                                                                                             'dd/mm/yyyy')
                                                                              from account_move am
                                                                                       left join account_move_line aml on aml.move_id = am.id
                                                                                       left join account_account amlaa on amlaa.id = aml.account_id
                                                                              WHERE am.asset_id = b.id
                                                                                and am.state = 'posted'
                                                                                and amlaa.code like ('811'))
                       else (select to_date(to_char(am.date + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy')
                             from account_move am
                                      JOIN account_asset aa on am.asset_id = aa.id
                             WHERE am.asset_id = b.id
                               and am.state = 'posted'
                               and aa.state = 'close'
                             order by am.write_date desc
                             limit 1) end        as ngaygiam,
                   b.method_number                  sokyhk,

                   c.code                           tktaisan,
                   d.code                           tkkhauhao,
                   e.code                           tkchiphi,
                   f.code                           mabp,
                   g.code                           maphi,
                   g.name                           tenphi,
                   f.name                           tenbp,
                   b.state                          trangthai
            from account_move a
                     join account_asset b on b.id = a.asset_id
                     join account_account c on c.id = b.account_asset_id
                     join account_account d on d.id = b.account_depreciation_id
                     join account_account e on e.id = b.account_depreciation_expense_id
                     left join account_analytic_account f on f.id = b.account_analytic_id
                     left join account_expense_item g on g.id = b.x_account_expense_item_id
            WHERE b.x_asset_type = 'assets'
              and a.state = 'posted'
              and b.state in ('open', 'close')
              and to_date(to_char(a.date + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy') >= to_date('%s', 'dd/mm/yyyy')
              and to_date(to_char(a.date + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy') <= to_date('%s', 'dd/mm/yyyy')
            group by b.id, tents, mats, nguyengia, gtbatdaukh, gtdakh, gtconlai, ngaymua,
                     ngaytinhkh, ngaygiam, sokyhk, tktaisan,
                     tkkhauhao, tkchiphi, mabp, maphi, tenphi, tenbp, trangthai
            union all

            SELECT b.id                             id,
                   b.name                           tents,
                   b.x_code                         mats,
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
                   to_date(to_char(b.acquisition_date + INTERVAL '7 hours', 'dd/mm/yyyy'),
                           'dd/mm/yyyy')            ngaymua,
                   to_date(to_char(b.first_depreciation_date + INTERVAL '7 hours', 'dd/mm/yyyy'),
                           'dd/mm/yyyy')            ngaytinhkh,
                   case
                       when (select to_date(to_char(am.date + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy')
                             from account_move am
                                      left join account_move_line aml on aml.move_id = am.id
                                      left join account_account amlaa on amlaa.id = aml.account_id
                             WHERE am.asset_id = b.id
                               and am.state = 'posted'
                               and amlaa.code like ('811')) is not null then (select to_date(
                                                                                             to_char(am.date + INTERVAL '7 hours', 'dd/mm/yyyy'),
                                                                                             'dd/mm/yyyy')
                                                                              from account_move am
                                                                                       left join account_move_line aml on aml.move_id = am.id
                                                                                       left join account_account amlaa on amlaa.id = aml.account_id
                                                                              WHERE am.asset_id = b.id
                                                                                and am.state = 'posted'
                                                                                and amlaa.code like ('811'))
                       else (select to_date(to_char(am.date + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy')
                             from account_move am
                                      JOIN account_asset aa on am.asset_id = aa.id
                             WHERE am.asset_id = b.id
                               and am.state = 'posted'
                               and aa.state = 'close'
                             order by am.write_date desc
                             limit 1) end        as ngaygiam,
                   b.method_number                  sokyhk,
                   c.code                           tktaisan,
                   d.code                           tkkhauhao,
                   e.code                           tkchiphi,
                   f.code                           mabp,
                   g.code                           maphi,
                   g.name                           tenphi,
                   f.name                           tenbp,
                   b.state                          trangthai
            from account_asset b
                     left join account_move a on b.id = a.asset_id
                     join account_account c on c.id = b.account_asset_id
                     join account_account d on d.id = b.account_depreciation_id
                     join account_account e on e.id = b.account_depreciation_expense_id
                     left join account_analytic_account f on f.id = b.account_analytic_id
                     left join account_expense_item g on g.id = b.x_account_expense_item_id
            where b.x_asset_type = 'assets'
              and b.state != 'model'
--               and b.book_value = 0
              and to_date(to_char(b.acquisition_date + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy') >=
                  to_date('%s', 'dd/mm/yyyy')
              and to_date(to_char(b.acquisition_date + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy') <=
                  to_date('%s', 'dd/mm/yyyy')
            group by b.id, tents, mats, nguyengia, gtbatdaukh, gtdakh, gtconlai, gtkhtrongky, ngaymua,
                     ngaytinhkh, ngaygiam, sokyhk,
                     tktaisan, tkkhauhao, tkchiphi, mabp, maphi, tenphi, tenbp
           ) as asset_tracking
      group by id, tents, mats, nguyengia, ngaymua, gtbatdaukh, gtdakh, ngaytinhkh, ngaygiam, sokyhk, tktaisan,
               tkkhauhao, tkchiphi,
               mabp, maphi, tenphi, tenbp, trangthai) asset_tracking_b
         left join
     (select ngayct, soct, id
      from (select k.date ngayct, k.move_name as soct, b.id as id
            from account_asset b
                     join asset_move_line_rel h on h.asset_id = b.id
                     left join account_move_line k on k.id = h.line_id
            where b.x_asset_type = 'assets'
            UNION ALL
            select m.date_import as ngayct, m.name as soct, b.id as id
            from account_asset b
                     left join import_asset_line l on b.id = l.asset_id
                     left join import_asset m on m.id = l.import_asset_id
            where b.x_asset_type = 'assets') as nct
      where ngayct is not null) ct on ct.id = asset_tracking_b.id
    """
        self.env.cr.execute(sql % (report_id, to_date, from_date, to_date, to_date, from_date, to_date))
        self.env.cr.commit()
        return {
            'name': _('Fixed Asset Tracking'),
            'view_mode': 'tree',
            'res_model': 'theo.doi.tai.san.co.dinh',
            'domain': [('report_id', '=', report_id)],
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'search_view_id': self.env.ref('ev_report_view.theo_doi_tai_san_co_dinh_search').id
        }
