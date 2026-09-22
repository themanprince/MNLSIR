from datetime import date
from decimal import Decimal, InvalidOperation

from sqladmin import BaseView
from starlette.requests import Request
from starlette.responses import RedirectResponse

from auth import decode_access_token, is_logged_in
from db import (
    Product,
    ProductUnitConversion,
    Store,
    Unit,
    make_session,
)
from exceptions import ReceiveIssueStockError
from schema.ReceiveIssueItem import ReceiveIssueItem


class StockTransactionAdmin(BaseView):
    """
    Shared admin view and form helper for stock transactions.

    Subclasses are responsible only for:
    - defining their template;
    - exposing their route;
    - constructing the appropriate request schema;
    - calling the appropriate InventoryService method.

    This class owns the common form and HTTP concerns:
    - authentication;
    - loading stores, products, and product units;
    - parsing store IDs and item rows;
    - identifying the authenticated staff member;
    - rendering forms;
    - committing, rolling back, and closing sessions.
    """

    template_name: str
    transaction_name: str

    def is_accessible(self, request: Request) -> bool:
        return is_logged_in(request)

    def is_visible(self, request: Request) -> bool:
        return is_logged_in(request)

    @staticmethod
    def get_form_data(session) -> dict:
        """
        Load the data required by goods receiving, issue, and dispatch forms.

        The product_units mapping is consumed by StockItemForm in the browser:

        {
            "product_id": [
                {
                    "id": 1,
                    "name": "piece",
                    "symbol": "pc"
                }
            ]
        }
        """
        stores = (
            session.query(Store)
            .order_by(Store.name.asc())
            .all()
        )

        products = (
            session.query(Product)
            .join(Unit, Product.base_unit_id == Unit.id)
            .order_by(Product.name.asc())
            .all()
        )

        conversions = (
            session.query(ProductUnitConversion)
            .join(Unit, ProductUnitConversion.unit_id == Unit.id)
            .order_by(
                ProductUnitConversion.product_id,
                Unit.name.asc(),
            )
            .all()
        )

        product_units = {
            str(product.id): [
                {
                    "id": product.base_unit.id,
                    "name": product.base_unit.name,
                    "symbol": product.base_unit.symbol,
                }
            ]
            for product in products
        }

        for conversion in conversions:
            product_key = str(conversion.product_id)
            units = product_units.setdefault(product_key, [])

            if not any(
                unit["id"] == conversion.unit_id
                for unit in units
            ):
                units.append(
                    {
                        "id": conversion.unit_id,
                        "name": conversion.unit.name,
                        "symbol": conversion.unit.symbol,
                    }
                )

        return {
            "stores": stores,
            "products": products,
            "product_units": product_units,
        }

    @staticmethod
    def parse_positive_int(value, field_name: str) -> int:
        value = str(value or "").strip()

        try:
            parsed_value = int(value)
        except (TypeError, ValueError):
            raise ValueError(f"{field_name} is invalid.")

        if parsed_value <= 0:
            raise ValueError(f"{field_name} is invalid.")

        return parsed_value

    @staticmethod
    def parse_positive_decimal(value, field_name: str) -> Decimal:
        value = str(value or "").strip()

        if not value:
            raise ValueError(f"{field_name} is required.")

        try:
            parsed_value = Decimal(value)
        except (InvalidOperation, ValueError):
            raise ValueError(
                f"{field_name} must be a valid number."
            )

        if not parsed_value.is_finite():
            raise ValueError(
                f"{field_name} must be a finite number."
            )

        if parsed_value <= 0:
            raise ValueError(
                f"{field_name} must be greater than zero."
            )

        return parsed_value

    @staticmethod
    def parse_date(value, field_name: str) -> date:
        value = str(value or "").strip()

        if not value:
            raise ValueError(f"{field_name} is required.")

        try:
            return date.fromisoformat(value)
        except ValueError:
            raise ValueError(f"{field_name} is invalid.")

    @staticmethod
    def get_authenticated_staff_id(request: Request) -> int:
        token = request.session.get("token")
        payload = decode_access_token(token)

        if not payload:
            raise PermissionError(
                "Your session has expired. Please sign in again."
            )

        staff_id = payload.get("staff_id")

        if not staff_id:
            raise PermissionError(
                "Unable to identify the staff member recording "
                "this transaction."
            )

        try:
            return int(staff_id)
        except (TypeError, ValueError):
            raise PermissionError(
                "The authenticated staff identity is invalid."
            )

    @classmethod
    def parse_items(cls, form) -> list[ReceiveIssueItem]:
        """
        Convert the repeated HTML item fields into schema objects.

        Business rules such as stock availability, unit conversion,
        duplicate products, and staff existence remain in InventoryService.
        """
        product_ids = form.getlist("product_id")
        unit_ids = form.getlist("unit_id")
        quantities = form.getlist("quantity")

        if not product_ids:
            raise ValueError(
                "Add at least one product to the transaction."
            )

        if not (
            len(product_ids)
            == len(unit_ids)
            == len(quantities)
        ):
            raise ValueError(
                "The transaction line items are incomplete."
            )

        items = []

        for index, (
            product_id_value,
            unit_id_value,
            quantity_value,
        ) in enumerate(
            zip(
                product_ids,
                unit_ids,
                quantities,
            ),
            start=1,
        ):
            product_id = cls.parse_positive_int(
                product_id_value,
                f"Product on line {index}",
            )

            unit_id = cls.parse_positive_int(
                unit_id_value,
                f"Unit on line {index}",
            )

            quantity = cls.parse_positive_decimal(
                quantity_value,
                f"Quantity on line {index}",
            )

            items.append(
                ReceiveIssueItem(
                    product_id=product_id,
                    unit_id=unit_id,
                    quantity=quantity,
                )
            )

        return items

    async def _render(
        self,
        request: Request,
        session,
        *,
        message: str | None = None,
        message_type: str = "info",
        form_data: dict | None = None,
    ):
        context = self.get_form_data(session)

        context.update(
            {
                "request": request,
                "message": message,
                "message_type": message_type,
                "form_data": form_data or {},
                "today": date.today().isoformat(),
            }
        )

        return await self.templates.TemplateResponse(
            request,
            self.template_name,
            context,
        )

    async def handle_transaction(self, request: Request):
        """
        Handle the shared GET/POST lifecycle.

        The subclass supplies the transaction-specific _record method.
        Everything else is common to receiving, issuing, and dispatching.
        """
        session = make_session()
        form = None

        try:
            if request.method == "GET":
                return await self._render(
                    request,
                    session,
                )

            form = await request.form()

            document = self._record(
                request,
                session,
                form,
            )

            # Loading form data starts a SQLAlchemy transaction. Commit
            # explicitly after the service successfully records the document.
            session.commit()

            return await self._render(
                request,
                session,
                message=(
                    f"{self.transaction_name} #{document.id} "
                    "was recorded successfully."
                ),
                message_type="success",
            )

        except PermissionError:
            session.rollback()

            return RedirectResponse(
                url="/admin/login",
                status_code=303,
            )

        except (
            ValueError,
            InvalidOperation,
            ReceiveIssueStockError,
        ) as error:
            session.rollback()

            # Preserve the scalar fields when redisplaying a failed form.
            # Repeated item values are intentionally not reconstructed here;
            # StockItemForm creates a fresh editable row.
            form_data = {}

            if form is not None:
                form_data = {
                    "store_id": form.get("store_id", ""),
                    "date": form.get("date", ""),
                    "source_party": form.get("source_party", ""),
                    "dest_party": form.get("dest_party", ""),
                    "destination_vessel": form.get(
                        "destination_vessel",
                        "",
                    ),
                    "remarks": form.get("remarks", ""),
                }

            return await self._render(
                request,
                session,
                message=str(error),
                message_type="danger",
                form_data=form_data,
            )

        except Exception:
            session.rollback()

            return await self._render(
                request,
                session,
                message=(
                    f"The {self.transaction_name.lower()} could not "
                    "be recorded. Please try again or contact "
                    "an administrator."
                ),
                message_type="danger",
            )

        finally:
            session.close()

    def _record(self, request, session, form):
        """
        Construct and submit the transaction-specific request.

        Each subclass implements this because receiving, issuing, and
        dispatching use different request fields and service methods.
        """
        raise NotImplementedError