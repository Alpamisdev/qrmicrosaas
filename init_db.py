import asyncio
from app.db import engine, Base, AsyncSessionLocal
from app.models import Admin
from passlib.context import CryptContext
from sqlalchemy.future import select

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

async def create_all():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("All tables created successfully.")

    # Insert default admin if not exists
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Admin).where(Admin.username == "qradmin"))
        admin = result.scalar_one_or_none()
        if not admin:
            admin = Admin(username="qradmin", password_hash=hash_password("1234"))
            session.add(admin)
            await session.commit()
            print("Default admin 'qradmin' created with password '1234'.")
        else:
            print("Default admin 'qradmin' already exists.")

if __name__ == "__main__":
    asyncio.run(create_all()) 