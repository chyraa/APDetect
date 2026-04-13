class User:
    def __init__(self, id, username, email, created_at=None):
        self.id = id
        self.username = username
        self.email = email
        self.created_at = created_at

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "created_at": self.created_at
        }