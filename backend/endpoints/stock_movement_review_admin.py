from decimal import Decimal, InvalidOperation

from sqladmin import BaseView, expose
from fastapi import Form
from starlette.concurrency import run_in_threadpool
from starlette.requests import Request

from auth import decode_access_token, is_logged_in
from db import (
    MovementType,
    StockBalance,
    StockMovement,
    make_session,
)
from repo.ProductRepo import ProductRepo
from repo.StoreRepo import StoreRepo
from service.LedgerService import LedgerService
from service.StockService import StockService


class StockMovementReviewAdmin(BaseView):
    name = "Stock Movement Review"

    def is_accessible(self, request: Request) -> bool:
        return is_logged_in(request)

    def is_visible(self, request: Request) -> bool:
        return is_logged_in(request)

    @expose("/stock-movement-review", methods=["GET", "POST"])
    async def stock_movement_review(self, request: Request):
        session = make_session()

        async def render(
            message=None,
            stores=None,
            products=None,
            selected_store_id=None,
            selected_product_id=None,
            movements=None,
            stocktakes=None,
            stock_balance=None,
        ):
            return await self.templates.TemplateResponse(
                request,
                "stock_movement_review.html",
                {
                    "message": message,
                    "stores": stores or [],
                    "products": products or [],
                    "selected_store_id": selected_store_id,
                    "selected_product_id": selected_product_id,
                    "movements": movements or [],
                    "stocktakes": stocktakes or [],
                    "stock_balance": stock_balance,
                },
            )

        stores = [] #default value to prevent UnboundLocalError in case of exception.. oooohhhh this AI nur de predict my comments too na... de make me feel stupid
        products = [] #default value to prevent UnboundLocalError in case of exception

        try:
            stores = await run_in_threadpool(StoreRepo.get_all_stores, session)
            products = await run_in_threadpool(ProductRepo(session=session).get_all_products)

            selected_store_id = request.query_params.get("store_id")
            selected_product_id = request.query_params.get("product_id")

            if request.method == "GET":
                if selected_store_id:
                    selected_store_id = int(selected_store_id)

                    if selected_product_id:
                        selected_product_id = int(selected_product_id)

                        ledger_service = LedgerService(session=session)

                        movements = await run_in_threadpool(
                            ledger_service.get_stock_movements,
                            store_id=selected_store_id,
                            product_id=selected_product_id,
                            limit=200,
                            newest_first=False,
                        )

                        stocktakes = (
                            session.query(StockMovement)
                            .filter(
                                StockMovement.store_id == selected_store_id,
                                StockMovement.product_id == selected_product_id,
                                StockMovement.movement_type == MovementType.STOCKTAKE,
                            )
                            .order_by(
                                StockMovement.movement_date.desc(),
                                StockMovement.id.desc(),
                            )
                            .all()
                        )

                        stock_balance = (
                            session.query(StockBalance)
                            .filter(
                                StockBalance.store_id == selected_store_id,
                                StockBalance.product_id == selected_product_id,
                            )
                            .first()
                        )

                        return await render(
                            stores=stores,
                            products=products,
                            selected_store_id=selected_store_id,
                            selected_product_id=selected_product_id,
                            movements=movements,
                            stocktakes=stocktakes,
                            stock_balance=stock_balance,
                        )

                    return await render(
                        stores=stores,
                        products=products,
                        selected_store_id=selected_store_id,
                    )

                return await render(
                    stores=stores,
                    products=products,
                )

            elif request.method == "POST":
                form = await request.form()
                action = str(form.get("action") or "").strip()

                token = request.session.get("token")
                payload = decode_access_token(token)
                if not payload:
                    return await render(
                        message="Unable to access required user information.",
                        stores=stores,
                        products=products,
                    )

                staff_id = payload.get("staff_id")
                if not staff_id:
                    return await render(
                        message="Unable to access staff_id from auth token.",
                        stores=stores,
                        products=products,
                    )

                stock_service = StockService(session=session)

                store_id:int = int(form.get("store_id"))
                product_id:int = int(form.get("product_id"))

                if action == "edit_movement":
                    movement_id = self._parse_required_int(
                    form.get("movement_id"),
                    "Movement",
                )
                    quantity_delta = self._parse_quantity_delta(
                    form.get("quantity_delta")
                )

                    try:
                        quantity_delta = Decimal(str(quantity_delta))
                    except (InvalidOperation, TypeError, ValueError):
                        raise ValueError("Quantity delta must be a valid number.")

                    remarks = (
                    str(form.get("remarks") or "").strip() or "Historical stock movement corrected from admin view"

                    await run_in_threadpool(
                        stock_service.update_historical_stockmovement,
                        movement_id=movement_id,
                        new_quantity_delta=quantity_delta,
                        recorded_by=staff_id,
                        remarks=remarks,
                    )

                    return await render(
                        message="Stock movement updated successfully.",
                        stores=stores,
                        products=products,
                        selected_store_id=store_id,
                        selected_product_id=product_id,
                    )

                elif action == "link_stocktake":
                    movement_id = self._parse_required_int(
                    form.get("movement_id"),
                    "Movement",
                )
                    stocktake_id = self._parse_required_int(
                    form.get("stocktake_id"),
                    "Stocktake",
                )

                    await run_in_threadpool(
                        stock_service.associate_stock_movement_to_stocktake,
                        movement_id=movement_id,
                        stocktake_id=stocktake_id,
                        recorded_by=staff_id,
                    )

                    return await render(
                        message="Movement linked to stocktake successfully.",
                        stores=stores,
                        products=products,
                        selected_store_id=store_id,
                        selected_product_id=product_id,
                    )

                elif action == "unlink_stocktake":
                    movement_id = self._parse_required_int(
                    form.get("movement_id"),
                    "Movement",
                )

                    await run_in_threadpool(
                        stock_service.remove_association_from_stock_movement,
                        movement_id=movement_id,
                        recorded_by=staff_id,
                    )

                    return await render(
                        message="Movement association removed successfully.",
                        stores=stores,
                        products=products,
                        selected_store_id=store_id,
                        selected_product_id=product_id,
                    )

                raise ValueError("Unsupported stock movement action.")

        except Exception as error:
            return await render(
                message=str(error),
                stores=stores,
                products=products,
                selected_store_id=request.query_params.get("store_id"),
                selected_product_id=request.query_params.get("product_id"),
            )

        finally:
            session.close()