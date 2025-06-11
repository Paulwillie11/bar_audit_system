from datetime import datetime
from models import AuditLog
from database import db_session

def log_action(username, user_role, action_type, old_value=None, new_value=None):
    """Logs an action to the AuditLog table."""
    try:
        log = AuditLog(
            username=username,
            user_role=user_role,
            action_type=action_type,
            old_value=str(old_value) if old_value is not None else None,
            new_value=str(new_value) if new_value is not None else None
        )
        db_session.add(log)
        db_session.commit()
    except Exception as e:
        print(f"Error logging action: {e}")
        db_session.rollback()
