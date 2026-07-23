from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import RLock
from typing import Any
from uuid import UUID

from apps.api.app.core.ids import uuid7
from apps.api.app.core.security import new_token, token_hash


@dataclass
class User:
    id: UUID
    role: str


@dataclass
class Invitation:
    token_hash: str
    role: str
    expires_at: datetime
    used_at: datetime | None = None


@dataclass
class Session:
    token_hash: str
    user_id: UUID
    expires_at: datetime


@dataclass
class IdempotencyRecord:
    owner_id: UUID
    route: str
    key_hash: str
    request_fingerprint: str
    status_code: int
    response: dict[str, Any]
    expires_at: datetime


class MemoryStore:
    """Unit-test/local-demo adapter. It is forbidden in production."""

    backend_name = "memory"

    def __init__(self):
        self.lock = RLock()
        self.users: dict[UUID, User] = {}
        self.invitations: dict[str, Invitation] = {}
        self.sessions: dict[str, Session] = {}
        self.profiles: dict[UUID, dict[str, Any]] = {}
        self.idempotency: dict[tuple[UUID, str, str], IdempotencyRecord] = {}

    def reset(self) -> None:
        with self.lock:
            self.__init__()

    def create_invitation(self, role: str = "member", ttl_hours: int = 24) -> str:
        token = new_token()
        self.invitations[token_hash(token)] = Invitation(
            token_hash=token_hash(token),
            role=role,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=ttl_hours),
        )
        return token

    def accept_invitation(self, token: str) -> tuple[User, str]:
        now = datetime.now(timezone.utc)
        invitation = self.invitations.get(token_hash(token))
        if invitation is None or invitation.used_at is not None or invitation.expires_at <= now:
            raise ValueError("invalid_or_expired_invitation")
        invitation.used_at = now
        user = User(id=uuid7(), role=invitation.role)
        session_token = new_token()
        session = Session(
            token_hash=token_hash(session_token),
            user_id=user.id,
            expires_at=now + timedelta(hours=12),
        )
        self.users[user.id] = user
        self.sessions[session.token_hash] = session
        return user, session_token

    def authenticate(self, session_token: str | None) -> User | None:
        if not session_token:
            return None
        session = self.sessions.get(token_hash(session_token))
        if session is None or session.expires_at <= datetime.now(timezone.utc):
            return None
        return self.users.get(session.user_id)

    def revoke_session(self, session_token: str | None) -> None:
        if session_token:
            self.sessions.pop(token_hash(session_token), None)

    def close(self) -> None:
        return None


store = MemoryStore()
