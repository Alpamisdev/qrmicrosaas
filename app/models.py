from sqlalchemy import (
    String,
    Text,
    DateTime,
    ForeignKey,
    Table,
    Enum,
    func,
    Boolean,
    Column,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base
import enum


# ==================================================
# Post statuses
# ==================================================
class PostStatus(enum.Enum):
    draft = "draft"
    published = "published"


# ==================================================
# User
# ==================================================
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    google_id: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    picture: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


# ==================================================
# Admin
# ==================================================
class Admin(Base):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))


# ==================================================
# Tag
# ==================================================
class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)

    posts: Mapped[list["Post"]] = relationship(
        "Post",
        secondary="post_tags",
        back_populates="tags",
        cascade="all, delete",
    )


# ==================================================
# Category
# ==================================================
class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)

    posts: Mapped[list["Post"]] = relationship(
        "Post",
        back_populates="category",
        cascade="all, delete",
    )


# ==================================================
# Posts
# ==================================================
class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    excerpt: Mapped[str] = mapped_column(String(300))
    content: Mapped[str] = mapped_column(Text)

    seo_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    seo_description: Mapped[str | None] = mapped_column(String(300), nullable=True)

    status: Mapped[PostStatus] = mapped_column(
        Enum(PostStatus), nullable=False, index=True, default=PostStatus.draft
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"))
    category: Mapped["Category | None"] = relationship("Category", back_populates="posts")

    tags: Mapped[list["Tag"]] = relationship(
        "Tag",
        secondary="post_tags",
        back_populates="posts",
    )


# ==================================================
# Table of relationship between posts and tags
# ==================================================
post_tags = Table(
    "post_tags",
    Base.metadata,
    Column("post_id", ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


# ==================================================
# Global site settings
# ==================================================
class SiteSettings(Base):
    __tablename__ = "site_settings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    site_name: Mapped[str] = mapped_column(String(100), nullable=False, default="My Site")
    google_analytics_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    ad_block_code: Mapped[str | None] = mapped_column(Text, nullable=True)
