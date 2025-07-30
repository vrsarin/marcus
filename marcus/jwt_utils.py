from fastapi import Request, HTTPException
from jose import jwt, JWTError

JWT_SECRET = "your-secret-key"
JWT_ALGORITHM = "HS256"

def get_user_id_from_jwt(request: Request) -> str:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header.")
    token = auth_header.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="user_id not found in token.")
        return user_id
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid JWT token.") from exc
