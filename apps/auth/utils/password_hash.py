from passlib.context import CryptContext


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
)

def hash_password(password: str) -> str:
    """Хэшируем пароль"""
    return pwd_context.hash(password)

def check_password_hash(plain_password: str, hashed_password: str) -> bool:
    """Проверяем пароль"""
    return pwd_context.verify(plain_password, hashed_password)