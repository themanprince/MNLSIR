from sqladmin import BaseView, expose
from starlette.requests import Request
from auth import is_logged_in


class DashboardView(BaseView):
    name = "Home"
    
    def is_accessible(self, request: Request) -> bool:
        return is_logged_in(request)

    def is_visible(self, request: Request) -> bool:
        return is_logged_in(request)


    @expose("/dashboard", methods=["GET", "HEAD"])
    async def index_page(self, request):
        
        return await self.templates.TemplateResponse(
            request, 
            "dashboard.html",
        )
