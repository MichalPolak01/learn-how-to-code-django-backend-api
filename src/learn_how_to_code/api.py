from ninja_extra import NinjaExtraAPI

api = NinjaExtraAPI(urls_namespace='myapi')

api.add_router("", "authentication.api.router", tags=["Authentication"])
api.add_router("/courses", "course.api.router", tags=["Courses"])
api.add_router("/courses", "module.api.router", tags=["Modules"])
api.add_router("", "lesson.api.router", tags=["Lessons"])
api.add_router("/lessons", "lesson_content.api.router", tags=["Lesson Content"])