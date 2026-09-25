from sqladmin import BaseView, expose

class DashboardView(BaseView):
    is_index = True
    name = "Home"

    @expose("/", methods=["GET", "HEAD"])
    async def index_page(self, request):
        
        return await self.templates.TemplateResponse(
            request, 
            "dashboard.html",
        )
