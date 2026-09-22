from sqladmin import BaseView, expose
from starlette.concurrency import run_in_threadpool
from starlette.requests import Request
from decimal import Decimal, InvalidOperation
import logging
from db import Unit, ProductUnitConversion
from db import make_session
from auth import is_logged_in, decode_access_token
from repo.StoreRepo import StoreRepo
from repo.ProductRepo import ProductRepo
from service.LedgerService import LedgerService, SortOrder
from service.InventoryService import InventoryService



class InventoryAdmin(BaseView):
    name = "Inventory"

    def is_accessible(self, request: Request) -> bool:
        return is_logged_in(request)

    def is_visible(self, request: Request) -> bool:
        return is_logged_in(request)

    @expose("/inventory", methods=["GET", "POST"])
    async def get_inventory_view(self, request):
        session = make_session()

        async def return_template_with_info(message, products, stores, product_units):
            return await self.templates.TemplateResponse(request, "inventory.html", {"message": message, "products": products, "stores": stores, "product_units": product_units})

        try:
            products = await run_in_threadpool(ProductRepo(session = session).get_all_products)
            stores = await run_in_threadpool(StoreRepo.get_all_stores, session = session)
            conversions = await run_in_threadpool(
                lambda: session.query(ProductUnitConversion)
                .join(Unit, ProductUnitConversion.unit_id == Unit.id)
                .order_by(ProductUnitConversion.product_id, Unit.name.asc())
                .all()
            )

            product_units = {}
            
            for product in products:
                    product_units[str(product["id"])] = [
                    {
                        "id": product["base_unit_id"],
                        "name": "Base unit",
                        "symbol": product["base_unit_symbol"],
                    }
                ]

            for conversion in conversions:
                product_key = str(conversion.product_id)
            
                product_units.setdefault(product_key, [])
            
                if not any(
                    unit["id"] == conversion.unit_id
                    for unit in product_units[product_key]
                ):
                    product_units[product_key].append(
                        {
                            "id": conversion.unit_id,
                            "name": conversion.unit.name,
                            "symbol": conversion.unit.symbol,
                        }
                    )

            if request.method == "GET":
                store_id = request.query_params.get("store_id")
                if store_id:
                    store_id = int(store_id)
                    ledger_service = LedgerService(session = session)
                    inventory = await run_in_threadpool(ledger_service.get_stock_balances, store_id = store_id, sort_order = SortOrder.ALPHABETICAL_ORDER)
                    return await self.templates.TemplateResponse(request, "inventory.html", {"store_is_selected": True, "inventory": inventory, "products": products, "stores": stores, "product_units": product_units})
                else:
                    return await self.templates.TemplateResponse(request, "inventory.html", {"products": products, "stores": stores, "product_units": product_units})

            elif request.method == "POST":
                
                inventory_service = InventoryService(session = session)

                token = request.session.get("token")
                payload = decode_access_token(token)
                if not payload:
                    return await return_template_with_info(message="Unable to access required info from user's auth token. Contact Admin", products=products, stores=stores, product_units=product_units)

                staff_id = payload.get("staff_id")

                if not staff_id:
                    return await return_template_with_info(message="Unable to access staff_id from user's auth token. Contact Admin", products=products, stores=stores, product_units=product_units)

                form = await request.form()
                store_id = int(form.get("store_id"))
                product_id = int(form.get("product_id"))
                quantity = float(form.get("quantity"))
                unit_id = int(form.get("unit_id"))
                remarks = form.get("remarks")
                
                try:
                    quantity = Decimal(str(form.get("quantity")))
                except (InvalidOperation, TypeError, ValueError):
                    raise ValueError("Quantity must be a valid number.")
                
                if not quantity.is_finite():
                    raise ValueError("Quantity must be finite.")

                await run_in_threadpool(inventory_service.submit_stocktake, 
                    recorded_by = staff_id,
                    store_id = store_id,
                    product_id = product_id,
                    target_quantity = Decimal(quantity),
                    target_unit_id = unit_id,
                    remarks = remarks
                )

                return await return_template_with_info(message="Inventory Taking Successful", products=products, stores=stores, product_units=product_units)

        except Exception as err:
            return await return_template_with_info(message=str(err), stores=[], products=[], product_units=[])

        finally:
            session.close()
