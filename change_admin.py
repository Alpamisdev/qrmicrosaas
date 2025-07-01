from dotenv import load_dotenv
load_dotenv()
import asyncio
import argparse
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import AsyncSessionLocal
from app.models import Admin
from passlib.context import CryptContext
from sqlalchemy.future import select

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

async def update_admin(username: str, password: str):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Admin))
        admin = result.scalars().first()
        if not admin:
            print("No admin user exists to update. Please initialize the database first.")
            return
        admin.username = username
        admin.password_hash = hash_password(password)
        await session.commit()
        print(f"Admin updated: username='{username}', password changed.")

def main():
    parser = argparse.ArgumentParser(description="Update the admin user's username and password.")
    parser.add_argument("--username", required=True, help="New admin username")
    parser.add_argument("--password", required=True, help="New admin password")
    args = parser.parse_args()
    asyncio.run(update_admin(args.username, args.password))

if __name__ == "__main__":
    main() 