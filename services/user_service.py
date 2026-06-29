import logging
from models.db_models import AssignmentGroup, User, db

log = logging.getLogger(__name__)


class UserService:
    @staticmethod
    def list_users(limit=100, offset=0):
        users = User.query.order_by(User.name.asc()).offset(offset).limit(limit).all()
        return [user.to_dict() for user in users]

    @staticmethod
    def create_user(data):
        user = User(
            user_name=data.get("user_name"),
            name=data.get("name") or data.get("user_name"),
            email=data.get("email"),
            active=data.get("active", True),
            department=data.get("department"),
            title=data.get("title"),
        )
        user.set_password(data.get("password", "Password123!"))
        db.session.add(user)
        db.session.commit()
        log.info('User created: username=%s', user.user_name)
        return user.to_dict()

    @staticmethod
    def list_groups(limit=100, offset=0):
        groups = AssignmentGroup.query.order_by(AssignmentGroup.name.asc()).offset(offset).limit(limit).all()
        return [group.to_dict() for group in groups]
