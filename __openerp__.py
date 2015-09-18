# __openerp__.py
{
    'name': "Account reviewing",
    'description': "Get invoice state at any point in time",
    'category': 'Accounting & Finance',
    "version" : "1.0",
    "author" : "Anthony Ramirez, Hasa",
    'depends': ['account', 'account_voucher'],
    'update_xml': ['account_reviewing_view.xml'],
    "installable": True,
    "active": True,
}
