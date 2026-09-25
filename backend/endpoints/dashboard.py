from sqladmin import BaseView, expose

class DashboardView(BaseView):
    is_index = True
    name = "Home"
    icon = "fa fa-home"

    @expose("/", methods=["GET"])
    async def index_page(self, request):
        
        return await self.templates.TemplateResponse(
            request, 
            "index.html",
        )
