# from odoo import http


# class SimpleModule(http.Controller):
#     @http.route('/simple_module/simple_module', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/simple_module/simple_module/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('simple_module.listing', {
#             'root': '/simple_module/simple_module',
#             'objects': http.request.env['simple_module.simple_module'].search([]),
#         })

#     @http.route('/simple_module/simple_module/objects/<model("simple_module.simple_module"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('simple_module.object', {
#             'object': obj
#         })

