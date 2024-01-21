# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from io import BytesIO, StringIO
from odoo.addons.web.controllers.main import serialize_exception, content_disposition
import os
import zipfile
import logging
import base64
from datetime import date

_logger = logging.getLogger(__name__)


class WordTemplate(http.Controller):

    @http.route('/to_loan_management/wizard/<string:id>', type='http', auth="public")
    def download(self, id=False, **kwargs):
        template_wizard = request.env['template.bank.wizard'].browse(int(id))
        docs_templ = template_wizard.word_template_id
        disbursement_id = template_wizard.borrow_disbursement_id
        disbursement_dt_id = template_wizard.disbursement_detail_id
        if template_wizard.disbursement_payment_match_id:
            finalDoc = template_wizard.action_print_doc(disbursement_id, docs_templ, template_wizard)
        elif template_wizard.disbursement_detail_id:
            finalDoc = template_wizard.action_print_doc_2(disbursement_id, docs_templ, template_wizard,
                                                          disbursement_dt_id)
        file_name = docs_templ.name_display + '.doc'
        with open(finalDoc.name, 'rb') as f:
            content = base64.b64encode(f.read())
            return request.make_response(base64.b64decode(content), [
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
                ('Content-Disposition', content_disposition(file_name))])

    @http.route('/to_loan_management/bidv/<string:id>', type='http', auth="public")
    def download_bidv(self, id=False, **kwargs):
        reponds = BytesIO()
        archive = zipfile.ZipFile(reponds, 'w', zipfile.ZIP_DEFLATED)
        disbursement_id = request.env['loan.borrow.disbursement'].browse(int(id))
        disbursement_dt_ids = disbursement_id.disbursement_dt_ids
        if disbursement_dt_ids:
            list_partner = []
            item = 1
            for line in disbursement_dt_ids:
                # Cam kết nợ chứng từ BIDV
                finalDoc = disbursement_id.cam_ket_no_chung_tu_bidv(line, disbursement_id)
                demo = str(line.partner_id.name) + ' - ' + str(item)
                archive.write(finalDoc.name, r'%s\Cam kết nợ chứng từ (BIDV).docx' % demo)
                os.unlink(finalDoc.name)

                # Giấy giải ngân USD BIDV
                if item == 1:
                    finalDoc = disbursement_id.giay_giai_ngan_usd_bidv(disbursement_id)
                    archive.write(finalDoc.name, r'Giấy giải ngân USD (BIDV).docx')
                    os.unlink(finalDoc.name)

                # Giấy giải ngân VND BIDV
                if item == 1:
                    finalDoc = disbursement_id.giay_giai_ngan_vnd_bidv(disbursement_id)
                    archive.write(finalDoc.name, r'Giấy giải ngân VND (BIDV).docx')
                    os.unlink(finalDoc.name)

                # Hợp đồng mua bán ngoại tệ BIDV
                if item == 1:
                    finalDoc = disbursement_id.hop_dong_mua_ban_ngoai_te_bidv(disbursement_id)
                    archive.write(finalDoc.name, r'Hợp đồng mua bán ngoại tệ (BIDV).docx')
                    os.unlink(finalDoc.name)

                # Lệnh chuyển tiền BIDV
                if line.partner_id.id not in list_partner:
                    finalDoc = disbursement_id.lenh_chuyen_tien_bidv(line, disbursement_id)
                    demo = str(line.partner_id.name)
                    archive.write(finalDoc.name, r'Lệnh chuyển tiền (BIDV) - %s.docx' % demo)
                    os.unlink(finalDoc.name)

                # Ủy nhiệm chi BIDV
                finalDoc = disbursement_id.uy_nhiem_chi_bidv(line, disbursement_id)
                demo = str(line.partner_id.name) + ' - ' + str(item)
                archive.write(finalDoc.name, r'%s\Ủy nhiệm chi (BIDV).docx' % demo)
                os.unlink(finalDoc.name)

                list_partner.append(line.partner_id.id)
                item += 1
            archive.close()
            reponds.flush()
            ret_zip = reponds.getvalue()
            reponds.close()
            finalDoc.name = 'HoSoTinDung-BIDV-%s.zip' % date.today().strftime("%d/%m/%Y")
            return request.make_response(ret_zip,
                                         [('Content-Type', 'application/zip'),
                                          ('Content-Disposition', content_disposition(finalDoc.name))])

    @http.route('/to_loan_management/vcb/<string:id>', type='http', auth="public")
    def download_vcb(self, id=False, **kwargs):
        reponds = BytesIO()
        archive = zipfile.ZipFile(reponds, 'w', zipfile.ZIP_DEFLATED)
        disbursement_id = request.env['loan.borrow.disbursement'].browse(int(id))
        disbursement_dt_ids = disbursement_id.disbursement_dt_ids
        list_partner = []
        item = 1
        for line in disbursement_dt_ids:
            # Đơn xin nợ chứng từ
            # finalDoc = disbursement_id.don_xin_no_chung_tu_vcb(line, disbursement_id)
            # demo = str(line.partner_id.name) + ' - ' + str(item)
            # archive.write(finalDoc.name, r'%s\Đơn xin nợ chứng từ.docx' % demo)
            # os.unlink(finalDoc.name)

            # Cam kết trả chứng từ VCB
            finalDoc = disbursement_id.cam_ket_tra_chung_tu_vcb(line, disbursement_id)
            demo = str(line.partner_id.name) + ' - ' + str(item)
            archive.write(finalDoc.name, r'%s\Cam kết trả chứng từ.docx' % demo)
            os.unlink(finalDoc.name)

            if item == 1:
                finalDoc = disbursement_id.giay_nhan_no_vcb(disbursement_id)
                archive.write(finalDoc.name, r'Giấy nhận nợ.docx')
                os.unlink(finalDoc.name)

            if item == 1:
                finalDoc = disbursement_id.giay_de_nghi_mua_ngoai_te_vcb(disbursement_id)
                archive.write(finalDoc.name, r'Giấy đề nghị mua ngoại tệ.docx')
                os.unlink(finalDoc.name)

            if item == 1:
                finalDoc = disbursement_id.hop_dong_mua_ban_ngoai_te_vcb(disbursement_id)
                archive.write(finalDoc.name, r'Hợp đồng mua, bán ngoại tệ.docx')
                os.unlink(finalDoc.name)

            # Lệnh chuyển tiền VCB
            if line.partner_id.id not in list_partner:
                finalDoc = disbursement_id.lenh_chuyen_tien_vcb(line, disbursement_id)
                demo = str(line.partner_id.name)
                archive.write(finalDoc.name, r'Lệnh chuyển tiền - %s.docx' % demo)
                os.unlink(finalDoc.name)

            # Ủy nhiệm chi VCB
            finalDoc = disbursement_id.uy_nhiem_chi_vcb(line, disbursement_id)
            demo = str(line.partner_id.name) + ' - ' + str(item)
            archive.write(finalDoc.name, r'%s\Ủy nhiệm chi.docx' % demo)
            os.unlink(finalDoc.name)

            list_partner.append(line.partner_id.id)
            item += 1
        archive.close()
        reponds.flush()
        ret_zip = reponds.getvalue()
        reponds.close()

        finalDoc.name = 'HoSoTinDung-VCB-%s.zip' % date.today().strftime("%d/%m/%Y")
        return request.make_response(ret_zip,
                                     [('Content-Type', 'application/zip'),
                                      ('Content-Disposition', content_disposition(finalDoc.name))])

    @http.route('/to_loan_management/vtb/<string:id>', type='http', auth="public")
    def download_vtb(self, id=False, **kwargs):
        reponds = BytesIO()
        archive = zipfile.ZipFile(reponds, 'w', zipfile.ZIP_DEFLATED)
        disbursement_id = request.env['loan.borrow.disbursement'].browse(int(id))
        disbursement_dt_ids = disbursement_id.disbursement_dt_ids
        list_partner = []
        item = 1
        for line in disbursement_dt_ids:

            # Giấy đề nghị mua ngoại tệ
            if item == 1:
                finalDoc = disbursement_id.de_nghi_mua_ngoai_te_vtb(disbursement_id)
                archive.write(finalDoc.name, r'Giấy đề nghị mua ngoại tệ.docx')
                os.unlink(finalDoc.name)

            # Lệnh chuyển tiền VTB
            if line.partner_id.id not in list_partner:
                finalDoc = disbursement_id.lenh_chuyen_tien_vtb(line, disbursement_id)
                demo = str(line.partner_id.name)
                archive.write(finalDoc.name, r'Lệnh chuyển tiền - %s.docx' % demo)
                os.unlink(finalDoc.name)

            # Giấy nhận nợ USD VTB
            if item == 1:
                finalDoc = disbursement_id.giay_nhan_no_vtb_usd(disbursement_id)
                archive.write(finalDoc.name, r'Giấy nhận nợ USD.docx')
                os.unlink(finalDoc.name)

            # Giấy nhận nợ VND VTB
            if item == 1:
                finalDoc = disbursement_id.giay_nhan_no_vtb_vnd(disbursement_id)
                archive.write(finalDoc.name, r'Giấy nhận nợ VND.docx')
                os.unlink(finalDoc.name)

            # Ủy nhiệm chi BIDV
            finalDoc = disbursement_id.uy_nhiem_chi_vtb(line, disbursement_id)
            demo = str(line.partner_id.name) + ' - ' + str(item)
            archive.write(finalDoc.name, r'%s\Ủy nhiệm chi.docx' % demo)
            os.unlink(finalDoc.name)

            list_partner.append(line.partner_id.id)
            item += 1
        archive.close()
        reponds.flush()
        ret_zip = reponds.getvalue()
        reponds.close()

        finalDoc.name = 'HoSoTinDung-%s.zip' % date.today().strftime("%d/%m/%Y")
        return request.make_response(ret_zip,
                                     [('Content-Type', 'application/zip'),
                                      ('Content-Disposition', content_disposition(finalDoc.name))])

    @http.route('/to_loan_management/unc/<string:id>', type='http', auth="public")
    def download_unc(self, id=False, **kwargs):
        template_wizard = request.env['wizard.choose.word.template'].browse(int(id))
        docs_templ = template_wizard.word_template_id
        refund_payment_id = template_wizard.refund_payment_id
        finalDoc = template_wizard.action_print_uy_nhiem_chi_refund(refund_payment_id, docs_templ)
        file_name = docs_templ.name_display + '.doc'
        with open(finalDoc.name, 'rb') as f:
            content = base64.b64encode(f.read())
            return request.make_response(base64.b64decode(content), [
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
                ('Content-Disposition', content_disposition(file_name))])