import asyncio
import getpass

from core.db import SessionLocal
from apps.auth.service.auth import AuthService
from apps.auth.domain.roles import Role


async def async_create_admin():
    username = input("Username: ").strip()

    while True:
        password = getpass.getpass(prompt="Password: ")
        password2 = getpass.getpass(prompt="Confirm password: ")

        if not password:
            print("Password cannot be empty")
        elif password != password2:
            print("Passwords do not match")
        else:
            break

    async with SessionLocal() as session:
        service = AuthService(session=session)

        try:
            user = await service.create_admin(
                username=username,
                password=password,
                role=Role.ADMIN,
            )
        except ValueError as e:
            print(e)
            return

        print(f"✅ Superadmin '{user.username}' created successfully")


def main():
    asyncio.run(async_create_admin())


if __name__ == "__main__":
    main()
