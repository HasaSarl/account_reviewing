import openerp
from openerp import netsvc, tools, pooler
from openerp.osv import fields, osv
from openerp.tools.translate import _

class account_reviewing_line(osv.osv):
    _name = 'account.reviewing.line'

    _columns = {
	'invoice_id': fields.many2one('account.invoice','Invoice',required=True,readonly=True, ondelete='cascade'),
	'number': fields.related('invoice_id','number', type='char', string='Invoice number'),
	'create_invoice_date': fields.date('Invoice create date'),
	'write_invoice_date': fields.date('Invoice last write date'),
	'date_invoice': fields.related('invoice_id', 'date_invoice', type='date', string='Invoice date'),
	'amount_tax':fields.related('invoice_id', 'amount_tax', type='float', string='Tax amount'),
	'amount_untaxed': fields.related('invoice_id', 'amount_untaxed', type='float', string='Amount without tax'),
	'amount_total': fields.related('invoice_id', 'amount_total', type='float', string='Amount'),
	'amount_residual_on_date': fields.float('Amount residual on the chosen date'),
	'partner_id': fields.related('invoice_id', 'partner_id', type='many2one', relation='res.partner', string='Partner'),
	'account_reviewing_id':fields.many2one('account.reviewing', 'Account reviewing', required=True, ondelete='cascade'),
    }

    _defaults = {
	'amount_residual_on_date' : 0.0
    }

class account_reviewing(osv.osv):
    _name = 'account.reviewing'

    _columns = {
	'name': fields.char('Review name', size=30),
	'date_review': fields.date('Date review'),
        'invoice_line': fields.one2many('account.reviewing.line', 'account_reviewing_id', 'Review Lines', readonly=True),
        'type': fields.selection([
            ('out_invoice','Customer Invoice'),
            ('in_invoice','Supplier Invoice'),
            ('out_refund','Customer Refund'),
            ('in_refund','Supplier Refund'),
            ],'Type', select=True),
    }

    def create_review(self, cr, uid, ids, context):


	review_id = self.browse(cr, uid, ids)[0]
	line_pool = self.pool.get('account.reviewing.line')
        line_ids = [line.id for line in review_id.invoice_line]
        line_pool.unlink(cr, uid, line_ids, context=context)
	name = review_id.name
	date = review_id.date_review
	type = review_id.type
	query = """SELECT i.number, i.create_date, i.write_date, balance from account_invoice i \
			LEFT JOIN (select vl.name, SUM(vl.amount), MAX(i.amount_total), MAX(i.amount_total) - SUM(vl.amount) balance from account_voucher_line vl \
			JOIN account_voucher v ON (vl.voucher_id = v.id) \
			LEFT JOIN account_move_line ml ON (vl.move_line_id = ml.id) \
			LEFT JOIN account_move m ON (ml.move_id = m.id) \
			LEFT JOIN account_invoice i ON (m.id = i.move_id) \
			WHERE v.state='posted' \
			AND v.date <= '%s' \
			AND i.type = '%s'\
			GROUP BY vl.name \
			HAVING SUM(vl.amount) + 1 < MAX(i.amount_total) \
			AND SUM(vl.amount) > 0 \
			ORDER BY MAX(v.date) desc) AS vl ON (number = vl.name) \
			LEFT JOIN res_partner p ON (i.partner_id = p.id) \
			WHERE number NOT IN \
			(select vl.name FROM account_voucher_line vl \
			JOIN account_voucher v ON (vl.voucher_id = v.id) \
			LEFT JOIN account_move_line ml ON (vl.move_line_id = ml.id) \
			LEFT JOIN account_move m ON (ml.move_id = m.id) \
			LEFT JOIN account_invoice i ON (m.id = i.move_id) \
			WHERE v.state='posted' \
			AND v.date <= '%s' \
			AND i.type = '%s' \
			GROUP BY vl.name \
			HAVING SUM(vl.amount) + 1 >= MAX(i.amount_total) \
			ORDER BY MAX(v.date) desc) \
			AND date_invoice <= '%s' \
			AND type='%s'""" % (date, type, date, type, date, type)
	cr.execute(query)
	for obj in cr.fetchall():
	    vals = {}
	    number, create_date, write_date, balance = obj
	    vals['invoice_id'] = self.pool.get('account.invoice').search(cr, uid, [('number', '=',number)])[0]
	    vals['account_reviewing_id'] = review_id.id
	    vals['create_invoice_date'] = create_date
	    vals['write_invoice_date'] = write_date
	    if balance:
   	        vals['amount_residual_on_date'] = balance
	    review_line = self.pool.get('account.reviewing.line').create(cr, uid, vals)
	return review_id
