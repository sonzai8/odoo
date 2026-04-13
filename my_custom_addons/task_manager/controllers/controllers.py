# from odoo import http


# class TaskManager(http.Controller):
#     @http.route('/task_manager/task_manager', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/task_manager/task_manager/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('task_manager.listing', {
#             'root': '/task_manager/task_manager',
#             'objects': http.request.env['task_manager.task_manager'].search([]),
#         })

#     @http.route('/task_manager/task_manager/objects/<model("task_manager.task_manager"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('task_manager.object', {
#             'object': obj
#         })

