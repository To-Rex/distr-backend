from sqladmin import Admin
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse
from config.database import async_session_maker


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username, password = form["username"], form["password"]

        if username == "mxsoft90" and password == "mxsoft90":
            request.session.update({"token": "authenticated_user_token"})
            return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")
        if not token:
            return False
        # Optional: Add logic to verify if the token is still valid
        return True


# Initialize the backend with a secret key for session signing
authentication_backend = AdminAuth(secret_key="hello")
