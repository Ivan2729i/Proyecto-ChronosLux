document.addEventListener("DOMContentLoaded", () => {
    const checkoutForm = document.getElementById("checkout-form");

    const paymentInputs = document.querySelectorAll(
        'input[name="metodo_pago"]'
    );

    const cardFields = document.getElementById(
        "card-payment-fields"
    );

    const paypalFields = document.getElementById(
        "paypal-payment-fields"
    );

    const addressModal = document.getElementById(
        "address-modal"
    );

    const addressForm = document.getElementById(
        "address-form"
    );

    const addressList = document.getElementById(
        "address-list"
    );

    const saveAddressButton = document.getElementById(
        "save-address-button"
    );

    const placeOrderButton = document.getElementById(
        "place-order-button"
    );

    const addressGeneralError = document.getElementById(
        "address-general-error"
    );

    const cardNumberInput = document.getElementById(
        "numero_tarjeta"
    );

    const cardholderInput = document.getElementById(
        "nombre_titular"
    );

    const cvvInput = document.getElementById(
        "cvv"
    );

    const expirationMonthInput = document.getElementById(
        "fecha_vencimiento_mes"
    );

    const expirationYearInput = document.getElementById(
        "fecha_vencimiento_anio"
    );

    function populateExpirationYears() {
        if (!expirationYearInput) {
            return;
        }

        // Evita duplicados si la función llega a ejecutarse más de una vez
        expirationYearInput.innerHTML = '<option value="">Año</option>';

        const currentYear = new Date().getFullYear();
        const maximumYear = currentYear + 15;

        for (let year = currentYear; year <= maximumYear; year++) {
            const option = document.createElement("option");

            option.value = year;
            option.textContent = year;

            expirationYearInput.appendChild(option);
        }
    }

    populateExpirationYears();

    function formatCardNumber() {
        if (!cardNumberInput) {
            return;
        }

        const digits = cardNumberInput.value
            .replace(/\D/g, "")
            .slice(0, 16);

        cardNumberInput.value = digits
            .replace(/(\d{4})(?=\d)/g, "$1 ");
    }

    function validateCardNumber() {
        if (!cardNumberInput) {
            return true;
        }

        const digits = cardNumberInput.value.replace(/\D/g, "");

        const isValid = digits.length === 16;

        cardNumberInput.setCustomValidity(
            isValid
                ? ""
                : "El número de tarjeta debe contener exactamente 16 dígitos."
        );

        return isValid;
    }

    function validateCardholder() {
        if (!cardholderInput) {
            return true;
        }

        const value = cardholderInput.value
            .trim()
            .replace(/\s+/g, " ");

        const words = value
            .split(" ")
            .filter(Boolean);

        const validCharacters =
            /^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ' -]+$/.test(value);

        let errorMessage = "";

        if (value.length < 3) {
            errorMessage =
                "El nombre del titular debe tener al menos 3 caracteres.";
        } else if (words.length < 2) {
            errorMessage =
                "Debes ingresar por lo menos nombre y apellido.";
        } else if (!validCharacters) {
            errorMessage =
                "El nombre del titular solo puede contener letras, espacios, apóstrofes o guiones.";
        }

        cardholderInput.setCustomValidity(errorMessage);

        return errorMessage === "";
    }

    function filterCvv() {
        if (!cvvInput) {
            return;
        }

        cvvInput.value = cvvInput.value
            .replace(/\D/g, "")
            .slice(0, 3);
    }

    function validateCvv() {
        if (!cvvInput) {
            return true;
        }

        const isValid = /^[0-9]{3}$/.test(cvvInput.value);

        cvvInput.setCustomValidity(
            isValid
                ? ""
                : "El CVV debe contener exactamente 3 números."
        );

        return isValid;
    }

    function validateExpirationDate() {
        if (
            !expirationMonthInput ||
            !expirationYearInput
        ) {
            return true;
        }

        expirationMonthInput.setCustomValidity("");
        expirationYearInput.setCustomValidity("");

        if (
            !expirationMonthInput.value ||
            !expirationYearInput.value
        ) {
            expirationMonthInput.setCustomValidity(
                "Selecciona el mes y el año de vencimiento."
            );

            return false;
        }

        const selectedMonth = Number(
            expirationMonthInput.value
        );

        const selectedYear = Number(
            expirationYearInput.value
        );

        const currentDate = new Date();
        const currentMonth = currentDate.getMonth() + 1;
        const currentYear = currentDate.getFullYear();

        const isExpired =
            selectedYear < currentYear ||
            (
                selectedYear === currentYear &&
                selectedMonth < currentMonth
            );

        if (isExpired) {
            expirationMonthInput.setCustomValidity(
                "La tarjeta ya está vencida."
            );

            return false;
        }

        return true;
    }



    function setPaymentSectionState(section, active) {
        if (!section) {
            return;
        }

        section.classList.toggle("hidden", !active);

        section
            .querySelectorAll("input, select")
            .forEach((field) => {
                field.disabled = !active;
                field.required = active;

                // Evita que un campo oculto conserve errores anteriores
                if (!active) {
                    field.setCustomValidity("");
                }
            });
    }

    function updatePaymentFields() {
        const selectedPayment = document.querySelector(
            'input[name="metodo_pago"]:checked'
        );

        if (!selectedPayment) {
            return;
        }

        const isCard =
            selectedPayment.value === "tarjeta_credito" ||
            selectedPayment.value === "tarjeta_debito";

        const isPaypal =
            selectedPayment.value === "paypal";

        setPaymentSectionState(cardFields, isCard);
        setPaymentSectionState(paypalFields, isPaypal);
    }


    paymentInputs.forEach((input) => {
        input.addEventListener(
            "change",
            updatePaymentFields
        );
    });

    updatePaymentFields();


    if (cardNumberInput) {
        cardNumberInput.addEventListener("input", () => {
            formatCardNumber();
            validateCardNumber();
        });

        cardNumberInput.addEventListener(
            "blur",
            validateCardNumber
        );
    }

    if (cardholderInput) {
        cardholderInput.addEventListener(
            "input",
            validateCardholder
        );

        cardholderInput.addEventListener(
            "blur",
            validateCardholder
        );
    }

    if (cvvInput) {
        cvvInput.addEventListener("input", () => {
            filterCvv();
            validateCvv();
        });

        cvvInput.addEventListener(
            "blur",
            validateCvv
        );
    }

    if (expirationMonthInput) {
        expirationMonthInput.addEventListener(
            "change",
            validateExpirationDate
        );
    }

    if (expirationYearInput) {
        expirationYearInput.addEventListener(
            "change",
            validateExpirationDate
        );
    }


    function clearAddressErrors() {
        document
            .querySelectorAll("[data-error-for]")
            .forEach((element) => {
                element.textContent = "";
            });

        if (addressGeneralError) {
            addressGeneralError.textContent = "";
            addressGeneralError.classList.add("hidden");
        }
    }

    function showGeneralAddressError(message) {
        if (!addressGeneralError) {
            return;
        }

        addressGeneralError.textContent = message;
        addressGeneralError.classList.remove("hidden");
    }

    function showAddressErrors(errors) {
        clearAddressErrors();

        Object.entries(errors).forEach(
            ([fieldName, fieldErrors]) => {
                const messages = fieldErrors
                    .map((error) => error.message)
                    .join(" ");

                const fieldErrorElement =
                    document.querySelector(
                        `[data-error-for="${fieldName}"]`
                    );

                if (fieldErrorElement) {
                    fieldErrorElement.textContent = messages;
                } else {
                    showGeneralAddressError(messages);
                }
            }
        );
    }

    function openAddressModal() {
        if (!addressModal) {
            return;
        }

        clearAddressErrors();

        addressModal.classList.remove("hidden");
        addressModal.classList.add("flex");
        document.body.classList.add("overflow-hidden");

        const firstInput = addressModal.querySelector(
            "input:not([type='hidden'])"
        );

        if (firstInput) {
            firstInput.focus();
        }
    }

    function closeAddressModal() {
        if (!addressModal) {
            return;
        }

        addressModal.classList.add("hidden");
        addressModal.classList.remove("flex");
        document.body.classList.remove("overflow-hidden");
    }

    document
        .querySelectorAll("[data-open-address-modal]")
        .forEach((button) => {
            button.addEventListener(
                "click",
                openAddressModal
            );
        });

    document
        .querySelectorAll("[data-close-address-modal]")
        .forEach((element) => {
            element.addEventListener(
                "click",
                closeAddressModal
            );
        });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            closeAddressModal();
        }
    });

    function createAddressElement(domicilio) {
        document
            .querySelectorAll(
                'input[name="domicilio_seleccionado"]'
            )
            .forEach((radio) => {
                radio.checked = false;
            });

        const label = document.createElement("label");

        label.className =
            "flex items-center p-4 border rounded-lg " +
            "cursor-pointer hover:border-blue-500";

        const radio = document.createElement("input");

        radio.type = "radio";
        radio.name = "domicilio_seleccionado";
        radio.value = domicilio.id;
        radio.required = true;
        radio.checked = true;
        radio.className = "mr-4";

        const information = document.createElement("div");

        const mainText = document.createElement("p");

        mainText.className = "font-semibold";

        let addressText =
            `${domicilio.calle} #${domicilio.num_ext}`;

        if (domicilio.num_int) {
            addressText += ` Int. ${domicilio.num_int}`;
        }

        mainText.textContent = addressText;

        const secondaryText = document.createElement("p");

        secondaryText.className =
            "text-sm text-gray-600";

        secondaryText.textContent =
            `${domicilio.colonia}, ` +
            `${domicilio.estado}, ` +
            `C.P. ${domicilio.cp}`;

        information.appendChild(mainText);
        information.appendChild(secondaryText);

        label.appendChild(radio);
        label.appendChild(information);

        return label;
    }

    function addAddressToCheckout(domicilio) {
        const noAddressMessage = document.getElementById(
            "no-address-message"
        );

        const noAddressWarning = document.getElementById(
            "no-address-warning"
        );

        if (noAddressMessage) {
            noAddressMessage.remove();
        }

        if (noAddressWarning) {
            noAddressWarning.remove();
        }

        const addressElement =
            createAddressElement(domicilio);

        addressList.appendChild(addressElement);

        const hasCart =
            placeOrderButton.dataset.hasCart === "true";

        placeOrderButton.disabled = !hasCart;
    }

    if (addressForm) {
        addressForm.addEventListener(
            "submit",
            async (event) => {
                event.preventDefault();

                clearAddressErrors();

                const originalButtonText =
                    saveAddressButton.textContent;

                saveAddressButton.disabled = true;
                saveAddressButton.textContent =
                    "Guardando...";

                try {
                    const response = await fetch(
                        addressForm.action,
                        {
                            method: "POST",
                            body: new FormData(addressForm),
                            headers: {
                                "X-Requested-With":
                                    "XMLHttpRequest"
                            },
                            credentials: "same-origin"
                        }
                    );

                    const data = await response.json();

                    if (!response.ok || !data.success) {
                        if (data.errors) {
                            showAddressErrors(data.errors);
                        } else {
                            showGeneralAddressError(
                                "No fue posible guardar el domicilio."
                            );
                        }

                        return;
                    }

                    addAddressToCheckout(data.domicilio);

                    addressForm.reset();
                    closeAddressModal();

                } catch (error) {
                    console.error(
                        "Error al guardar domicilio:",
                        error
                    );

                    showGeneralAddressError(
                        "Ocurrió un error al guardar el domicilio."
                    );

                } finally {
                    saveAddressButton.disabled = false;
                    saveAddressButton.textContent =
                        originalButtonText;
                }
            }
        );
    }

    if (checkoutForm) {
        checkoutForm.addEventListener(
            "submit",
            (event) => {
                const selectedPayment = document.querySelector(
                    'input[name="metodo_pago"]:checked'
                );

                const isCard =
                    selectedPayment &&
                    (
                        selectedPayment.value === "tarjeta_credito" ||
                        selectedPayment.value === "tarjeta_debito"
                    );

                if (isCard) {
                    // Limpia errores viejos antes de volver a validar
                    cardNumberInput.setCustomValidity("");
                    cardholderInput.setCustomValidity("");
                    expirationMonthInput.setCustomValidity("");
                    expirationYearInput.setCustomValidity("");
                    cvvInput.setCustomValidity("");

                    const cardNumberIsValid =
                        validateCardNumber();

                    const cardholderIsValid =
                        validateCardholder();

                    const expirationIsValid =
                        validateExpirationDate();

                    const cvvIsValid =
                        validateCvv();

                    if (
                        !cardNumberIsValid ||
                        !cardholderIsValid ||
                        !expirationIsValid ||
                        !cvvIsValid
                    ) {
                        event.preventDefault();

                        const firstInvalidField =
                            checkoutForm.querySelector(":invalid");

                        if (firstInvalidField) {
                            firstInvalidField.focus();
                            firstInvalidField.reportValidity();
                        }

                        return;
                    }
                }

                const selectedAddress = document.querySelector(
                    'input[name="domicilio_seleccionado"]:checked'
                );

                if (!selectedAddress) {
                    event.preventDefault();

                    openAddressModal();

                    showGeneralAddressError(
                        "Debes registrar una dirección antes de continuar."
                    );
                }
            }
        );
    }
});
