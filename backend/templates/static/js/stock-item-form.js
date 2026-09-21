(function () {
    "use strict";

    function StockItemForm(options) {
        this.productUnits = options.productUnits || {};
        this.itemsContainer = document.getElementById(
            options.itemsContainerId || "items-container"
        );
        this.itemTemplate = document.getElementById(
            options.itemTemplateId || "item-row-template"
        );
        this.addItemButton = document.getElementById(
            options.addItemButtonId || "add-item-button"
        );
        this.emptyItemsMessage = document.getElementById(
            options.emptyItemsMessageId || "empty-items-message"
        );
        this.resetFormButton = document.getElementById(
            options.resetFormButtonId || "reset-form-button"
        );

        this.initialize();
    }

    StockItemForm.prototype.initialize = function () {
        if (!this.itemsContainer || !this.itemTemplate) {
            return;
        }

        if (this.addItemButton) {
            this.addItemButton.addEventListener(
                "click",
                this.addItemRow.bind(this)
            );
        }

        if (this.resetFormButton) {
            this.resetFormButton.addEventListener(
                "click",
                this.resetItems.bind(this)
            );
        }

        this.addItemRow();
    };

    StockItemForm.prototype.updateEmptyItemsMessage = function () {
        if (!this.emptyItemsMessage) {
            return;
        }

        var hasItems = this.itemsContainer.children.length > 0;

        this.emptyItemsMessage.classList.toggle(
            "d-none",
            hasItems
        );
    };

    StockItemForm.prototype.populateUnits = function (
        productSelect,
        unitSelect
    ) {
        var productId = productSelect.value;
        var units = this.productUnits[productId] || [];

        unitSelect.innerHTML = "";

        if (!productId || units.length === 0) {
            unitSelect.disabled = true;

            var unavailableOption = document.createElement("option");
            unavailableOption.value = "";
            unavailableOption.textContent = "No units configured";

            unitSelect.appendChild(unavailableOption);
            return;
        }

        unitSelect.disabled = false;

        var placeholder = document.createElement("option");
        placeholder.value = "";
        placeholder.textContent = "Select a unit";

        unitSelect.appendChild(placeholder);

        units.forEach(function (unit) {
            var option = document.createElement("option");

            option.value = unit.id;
            option.textContent =
                unit.name + " (" + unit.symbol + ")";

            unitSelect.appendChild(option);
        });

        if (units.length === 1) {
            unitSelect.value = String(units[0].id);
        }
    };

    StockItemForm.prototype.bindRow = function (rowElement) {
        var productSelect = rowElement.querySelector(
            ".product-select"
        );

        var unitSelect = rowElement.querySelector(
            ".unit-select"
        );

        var removeButton = rowElement.querySelector(
            ".remove-item-button"
        );

        if (productSelect && unitSelect) {
            productSelect.addEventListener(
                "change",
                function () {
                    this.populateUnits(
                        productSelect,
                        unitSelect
                    );
                }.bind(this)
            );
        }

        if (removeButton) {
            removeButton.addEventListener(
                "click",
                function () {
                    rowElement.remove();
                    this.updateEmptyItemsMessage();
                }.bind(this)
            );
        }
    };

    StockItemForm.prototype.addItemRow = function () {
        var row = this.itemTemplate.content.cloneNode(true);
        var rowElement = row.firstElementChild;

        this.bindRow(rowElement);
        this.itemsContainer.appendChild(row);

        this.updateEmptyItemsMessage();
    };

    StockItemForm.prototype.resetItems = function () {
        window.setTimeout(
            function () {
                this.itemsContainer.innerHTML = "";
                this.addItemRow();
            }.bind(this),
            0
        );
    };

    window.StockItemForm = StockItemForm;
})();