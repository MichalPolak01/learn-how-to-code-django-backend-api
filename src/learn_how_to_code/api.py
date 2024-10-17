from ninja_extra import NinjaExtraAPI
from ninja_jwt.controller import NinjaJWTDefaultController

api = NinjaExtraAPI()

api.add_router("", "authentication.api.router", tags=["Authentication"])