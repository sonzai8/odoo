from odoo import models, fields, api


class Task(models.Model):
    _name = 'task.manager'
    _description = 'task.manager'

    name = fields.Char(string="Task Name", required=True)
    description = fields.Text(string="Description")
    deadline = fields.Date(string="Deadline")
    
    status = fields.Selection(
        [
            ('todo', 'To Do'),
            ('in_progress', 'In Progress'),
            ('done', 'Done'),
        ],
        default='todo',
    )
    user_id = fields.Many2one('res.users', string='Assigned To')
    project_id = fields.Many2one('task.project', string='Project')
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100

