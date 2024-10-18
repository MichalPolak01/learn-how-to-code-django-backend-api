from ninja_extra import NinjaExtraAPI

api = NinjaExtraAPI()

api.add_router("", "authentication.api.router", tags=["Authentication"])