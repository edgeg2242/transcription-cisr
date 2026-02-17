"""
Exceptions personnalisées pour le pipeline de transcription CISR.
"""


class CISRException(Exception):
    """Exception de base pour toutes les erreurs CISR."""
    pass


class WorkOrderError(CISRException):
    """Erreur lors du traitement d'un Work Order (Workflow 0)."""
    pass


class WorkflowError(CISRException):
    """Erreur lors de l'exécution d'un workflow (Workflows 1-3)."""
    pass


class ValidationError(CISRException):
    """Erreur de validation de données ou de format."""
    pass


class SecurityError(CISRException):
    """Erreur de sécurité (ex: SAR Protégé B)."""
    pass


class UploadError(CISRException):
    """Erreur lors de l'upload FTP/SFTP."""
    pass
