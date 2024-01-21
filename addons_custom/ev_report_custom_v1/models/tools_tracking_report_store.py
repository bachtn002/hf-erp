from odoo import api, fields, models, _


class ToolsTrackingReportStore(models.Model):
    _name = 'tools.tracking.report.store'
    _description = 'Tools Tracking Report Store'
    _auto = False

    def get_data(self, **kwargs):
        rows = self._get_data_query(**kwargs)

        total_original = 0
        total_start_value = 0
        total_depreciated_value = 0
        total_value_in_period = 0
        total_residual_value = 0
        total_average_depreciation = 0

        for row in rows:
            total_original += row['nguyengia'] or 0
            total_start_value += row['gtbatdaukh'] or 0
            total_depreciated_value += row['gtdakh'] or 0
            total_value_in_period += row['gtkhtrongky'] or 0
            total_residual_value += row['gtconlai'] or 0
            total_average_depreciation += row['gttbtrongky'] or 0

        summary = {
            'total_original': total_original,
            'total_start_value': total_start_value,
            'total_depreciated_value': total_depreciated_value,
            'total_value_in_period': total_value_in_period,
            'total_residual_value': total_residual_value,
            'total_average_depreciation': total_average_depreciation,
        }

        return {'data': rows, 'summary': summary}

    def _get_data_query(self, **kwargs):
        date_from = kwargs.get('from_date').strftime('%d/%m/%Y')
        date_to = kwargs.get('to_date').strftime('%d/%m/%Y')

        sql = """
        select mats, tents, trangthai, nguyengia, gtbatdaukh, gtdakh,
            gtkhtrongky, gtconlai, gttbtrongky, to_char(ngaymua,'dd/mm/yyyy') ngaymua,
            to_char(ngaytinhkh, 'dd/mm/yyyy') ngaytinhkh, coalesce(to_char(ngaygiam,'dd/mm/yyyy'),'') ngaygiam,
            sokyhk, coalesce(to_char(ngayct, 'dd/mm/yyyy'),'') ngayct, soct, tktaisan,tkkhauhao, 
            tkchiphi, mabp, maphi, tenphi, tenbp
        from
        (select asset_tracking_b.id, asset_tracking_b.tents, 
            asset_tracking_b.mats, asset_tracking_b.nguyengia,
            asset_tracking_b.gtbatdaukh,
            case
                when asset_tracking_b.gtdakh is not null 
                then asset_tracking_b.gtdakh
                else 0 end as gtdakh,
            case
                when asset_tracking_b.gtkhtrongky is not null 
                then asset_tracking_b.gtkhtrongky
                else 0 end as gtkhtrongky,
            case
                when asset_tracking_b.gtdakh is not null 
                then asset_tracking_b.gtbatdaukh - asset_tracking_b.gtdakh
            else asset_tracking_b.gtbatdaukh end as gtconlai,
            asset_tracking_b.gttbtrongky, asset_tracking_b.ngaymua,
            asset_tracking_b.ngaytinhkh, asset_tracking_b.ngaygiam,
            asset_tracking_b.sokyhk, ct.ngayct, ct.soct,
            asset_tracking_b.tktaisan, asset_tracking_b.tkkhauhao,
            asset_tracking_b.tkchiphi, asset_tracking_b.mabp,
            asset_tracking_b.maphi, asset_tracking_b.tenphi,
            asset_tracking_b.tenbp,
            case
                when asset_tracking_b.trangthai = 'open' then 'Đang chạy'
                when asset_tracking_b.trangthai = 'close' then 'Đã đóng'
                when asset_tracking_b.trangthai = 'draft' then 'Dự thảo'
            else null end                        as trangthai
        from (select id, tents, mats, nguyengia, gtbatdaukh, gtdakh,
                sum(gtkhtrongky) gtkhtrongky, 0 as gtconlai,
                sum(gttbtrongky) gttbtrongky, ngaymua, ngaytinhkh,
                ngaygiam, sokyhk,
--              ngayct,
--              soct,
                tktaisan, tkkhauhao, tkchiphi, mabp,
                maphi, tenphi, tenbp, trangthai
            from (SELECT b.id id, b.name tents, b.x_code mats, 
                    b.original_value nguyengia,
                    case
                        when b.already_depreciated_amount_import is not null
                        then b.original_value - b.already_depreciated_amount_import
                    else b.original_value end   as gtbatdaukh,
                   (select sum(am.amount_total)
                    from account_move am
                    join account_asset aa on am.asset_id = aa.id
                    where aa.id = b.id
                    and am.state = 'posted'
                    and to_date(to_char(am.date + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy') <=
                        to_date(%s, 'dd/mm/yyyy')) as gtdakh,
                    sum(a.amount_total) gtkhtrongky, 0 gtconlai, avg(a.amount_total) gttbtrongky,
                    to_date(to_char(b.acquisition_date + INTERVAL '7 hours', 'dd/mm/yyyy'),
                           'dd/mm/yyyy')              ngaymua,
                    to_date(to_char(b.first_depreciation_date + INTERVAL '7 hours', 'dd/mm/yyyy'),
                           'dd/mm/yyyy')              ngaytinhkh,
                    case
                        when (select to_date(to_char(am.date + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy')
                            from account_move am
                            left join account_move_line aml on aml.move_id = am.id
                            left join account_account amlaa on amlaa.id = aml.account_id
                            WHERE am.asset_id = b.id
                            and am.state = 'posted'
                            and amlaa.code like ('811')) is not null 
                            then (select to_date(to_char(am.date + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy')
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
                    b.method_number                    sokyhk,
                    c.code                             tktaisan,
                    d.code                             tkkhauhao,
                    e.code                             tkchiphi,
                    f.code                             mabp,
                    g.code                             maphi,
                    g.name                             tenphi,
                    f.name                             tenbp,
                    b.state                            trangthai
                from account_move a
                join account_asset b on b.id = a.asset_id
                join account_account c on c.id = b.account_asset_id
                join account_account d on d.id = b.account_depreciation_id
                join account_account e on e.id = b.account_depreciation_expense_id
                left join account_analytic_account f on f.id = b.account_analytic_id
                left join account_expense_item g on g.id = b.x_account_expense_item_id
            WHERE b.x_asset_type in ('tools', 'expenses')
            and a.state = 'posted'
            and b.state in ('open', 'close')
            and to_date(to_char(a.date + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy') >= to_date(%s, 'dd/mm/yyyy')
            and to_date(to_char(a.date + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy') <= to_date(%s, 'dd/mm/yyyy')
            group by b.id, tents, mats, nguyengia, gtbatdaukh, gtdakh, gtconlai, ngaymua,
                     ngaytinhkh, ngaygiam, sokyhk, tktaisan,
                     tkkhauhao, tkchiphi, mabp, maphi, tenphi, tenbp, trangthai
            union all

            SELECT b.id                               id,
                   b.name                             tents,
                   b.x_code                           mats,
                   b.original_value                   nguyengia,
                   case
                       when b.already_depreciated_amount_import is not null
                           then b.original_value - b.already_depreciated_amount_import
                       else b.original_value end   as gtbatdaukh,
                   (select sum(am.amount_total)
                    from account_move am
                             join account_asset aa on am.asset_id = aa.id
                    where aa.id = b.id
                      and am.state = 'posted'
                      and to_date(to_char(am.date + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy') <=
                          to_date(%s, 'dd/mm/yyyy')) as gtdakh,
                   0                                  gtkhtrongky,
                   0                                  gtconlai,
                   0                                  gttbtrongky,
                   to_date(to_char(b.acquisition_date + INTERVAL '7 hours', 'dd/mm/yyyy'),
                           'dd/mm/yyyy')              ngaymua,
                   to_date(to_char(b.first_depreciation_date + INTERVAL '7 hours', 'dd/mm/yyyy'),
                           'dd/mm/yyyy')              ngaytinhkh,
                   case
                       when (select to_date(to_char(am.date + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy')
                             from account_move am
                                left join account_move_line aml on aml.move_id = am.id
                                left join account_account amlaa on amlaa.id = aml.account_id
                            WHERE am.asset_id = b.id
                            and am.state = 'posted'
                            and amlaa.code like ('811')) is not null 
                            then (select to_date(to_char(am.date + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy')
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
                    b.method_number                    sokyhk,
                    c.code                             tktaisan,
                    d.code                             tkkhauhao,
                    e.code                             tkchiphi,
                    f.code                             mabp,
                    g.code                             maphi,
                    g.name                             tenphi,
                    f.name                             tenbp,
                    b.state                            trangthai
                    from account_asset b
                    left join account_move a on b.id = a.asset_id
                    join account_account c on c.id = b.account_asset_id
                    join account_account d on d.id = b.account_depreciation_id
                    join account_account e on e.id = b.account_depreciation_expense_id
                    left join account_analytic_account f on f.id = b.account_analytic_id
                    left join account_expense_item g on g.id = b.x_account_expense_item_id
            where b.x_asset_type in ('tools', 'expenses')
            and b.state != 'model'
--          and b.book_value = 0
            and to_date(to_char(b.acquisition_date + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy') >=
                to_date(%s, 'dd/mm/yyyy')
            and to_date(to_char(b.acquisition_date + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy') <=
                to_date(%s, 'dd/mm/yyyy')
            group by b.id, tents, mats, nguyengia, gtbatdaukh, gtdakh, gtconlai, gtkhtrongky, ngaymua,
                ngaytinhkh, ngaygiam, sokyhk,
                tktaisan, tkkhauhao, tkchiphi, mabp, maphi, tenphi, tenbp
           ) as asset_tracking
        group by id, tents, mats, nguyengia, ngaymua, gtbatdaukh, gtdakh, ngaytinhkh, ngaygiam, sokyhk, tktaisan,
            tkkhauhao, tkchiphi, mabp, maphi, tenphi, tenbp, trangthai) asset_tracking_b
        left join
            (select ngayct, soct, id
                from (select k.date ngayct, k.move_name as soct, b.id as id
                    from account_asset b
                    join asset_move_line_rel h on h.asset_id = b.id
                    left join account_move_line k on k.id = h.line_id
                    where b.x_asset_type in ('tools', 'expenses')
                    UNION ALL
                    select m.date_import as ngayct, m.name as soct, b.id as id
                    from account_asset b
                    left join import_asset_line l on b.id = l.asset_id
                    left join import_asset m on m.id = l.import_asset_id
                    where b.x_asset_type in ('tools', 'expenses')) as nct
                where ngayct is not null) ct on ct.id = asset_tracking_b.id) as data
        """

        params = (date_to, date_from, date_to, date_to, date_from, date_from)

        self._cr.execute(sql, params)
        return self._cr.dictfetchall()
