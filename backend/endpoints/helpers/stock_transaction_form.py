from datetime import date
from decimal import Decimal, InvalidOperation

from db import (
    Product,
    ProductUnitConversion,
    Store,
    Unit,
)
from auth import decode_access_token
from schema.ReceiveIssueItem import ReceiveIssueItem


class StockTransactionForm:
    """
    Shared form functionality for receiving and dispatching stock.

    This class contains only presentation/form concerns:
    - Loading products, stores, units, and product-unit options
    - Parsing common form values
    - Extracting the authenticated staff member
    - Converting repeated HTML item fields into schema items

    Business rules remain in InventoryService.
    """

    @staticmethod
    def get_form_data(session) -> dict:
        """
        Load data needed by receiving and dispatch forms.

        Returns product_units in this format:

        {
            "1": [
                {
                    "id": 1,
                    "name": "piece",
                    "symbol": "pc",
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

        units = (
            session.query(Unit)
            .order_by(Unit.name.asc())
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

            product_units.setdefault(product_key, [])

            already_included = any(
                unit["id"] == conversion.unit_id
                for unit in product_units[product_key]
            )

            if not already_included:
                product_units[product_key].append(
                    {
                        "id": conversion.unit.id,
                        "name": conversion.unit.name,
                        "symbol": conversion.unit.symbol,
                    }
                )

        return {
            "stores": stores,
            "products": products,
            "units": units,
            "product_units": product_units,
        }

    @staticmethod
    def parse_positive_int(
        value,
        field_name: str,
    ) -> int:
        value = str(value or "").strip()

        try:
            parsed_value = int(value)
        except (TypeError, ValueError):
            raise ValueError(f"{field_name} is invalid.")

        if parsed_value <= 0:
            raise ValueError(f"{field_name} is invalid.")

        return parsed_value

    @staticmethod
    def parse_positive_decimal(
        value,
        field_name: str,
    ) -> Decimal:
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
    def get_authenticated_staff_id(request) -> int:
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
    def parse_items(
        cls,
        form,
    ) -> list[ReceiveIssueItem]:
        """
        Parse repeated product_id, unit_id, and quantity fields.

        Domain validation such as duplicate products, valid dates,
        staff existence, and unit conversion belongs in InventoryService.
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

    @staticmethod
    def add_render_context(
        context: dict,
        request,
        *,
        message: str | None = None,
        message_type: str = "info",
        form_data: dict | None = None,
    ) -> dict:
        """
        Add common values required by stock transaction templates.
        """

        context.update(
            {
                "request": request,
                "message": message,
                "message_type": message_type,
                "form_data": form_data or {},
                "today": date.today().isoformat(),
            }
        )

        return context