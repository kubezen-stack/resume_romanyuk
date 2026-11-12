from datetime import datetime
from typing import Optional

from sqlalchemy import Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app import db

class Post(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    posted: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    category: Mapped[Optional[str]] = mapped_column(
        Enum("news", "publication", "tech", "other")
    )

    def __repr__(self):
        return f"<Post {self.id}: {self.title!r}>"
