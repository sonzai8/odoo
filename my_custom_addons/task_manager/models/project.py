from odoo import models, fields

class Project(models.Model):
    _name = 'task.project'
    _description = 'Project'

    name = fields.Char(string="Project Name", required=True)
    task_ids = fields.One2many('task.manager', 'project_id', string='Tasks')