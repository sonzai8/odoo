import traceback
import logging
from odoo.addons.dl_wood_traceability.models.dl_wood_dossier import DlWoodDossier

_logger = logging.getLogger(__name__)
original_unlink = DlWoodDossier.unlink

def patched_unlink(self):
    _logger.error("Dossier unlink called! Traceback:\n" + "".join(traceback.format_stack()))
    return original_unlink(self)

DlWoodDossier.unlink = patched_unlink
