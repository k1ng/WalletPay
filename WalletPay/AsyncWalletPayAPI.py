from typing import Optional, Dict, List

import aiohttp

from WalletPay.types import OrderPreview
from WalletPay.types import OrderReconciliationItem
from WalletPay.types import WalletPayException
from WalletPay.types.Exception import CreateOrderException, GetOrderPreviewException, GetOrderListException, \
    GetOrderAmountException


class AsyncWalletPayAPI:
    BASE_URL = "https://pay.wallet.tg/wpay/store-api/v1/"

    def __init__(self, api_key: str):
        """
        Initialize the API client.

        :param api_key: The API key to access WalletPay.
        """
        self.api_key = api_key

    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """
        Internal method to perform API requests.

        :param method: HTTP method ("POST" or "GET").
        :param endpoint: API endpoint.
        :param data: Data to send in the request body (for POST requests).
        :return: Response from the API as a dictionary.

        Source: https://docs.wallet.tg/pay/#api
        """
        headers = {
            'Wpay-Store-Api-Key': self.api_key,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        url = self.BASE_URL + endpoint

        try:
            async with aiohttp.ClientSession() as session:
                if method == "POST":
                    async with session.post(url, headers=headers, json=data) as response:
                        response_data = await response.json()
                elif method == "GET":
                    async with session.get(url, headers=headers) as response:
                        response_data = await response.json()
                else:
                    raise WalletPayException("Invalid HTTP method")

                if response.status != 200:
                    raise WalletPayException(response_data.get("message", "Unknown error"))

                return response_data

        except aiohttp.ClientError as e:
            raise WalletPayException(f"API request failed: {e}")

    async def create_order(self, amount: float, currency_code: str, description: str, external_id: str,
                           timeout_seconds: int, customer_telegram_user_id: str,
                           return_url: Optional[str] = None, fail_return_url: Optional[str] = None,
                           custom_data: Optional[Dict] = None) -> OrderPreview:
        """
        Create a new order.

        :param amount: Order amount.
        :param currency_code: Currency code (e.g., "USD").
        :param description: Order description.
        :param external_id: External ID of the order.
        :param timeout_seconds: Payment waiting time in seconds.
        :param customer_telegram_user_id: Telegram user ID.
        :param return_url: URL for redirection after successful payment.
        :param fail_return_url: URL for redirection after failed payment.
        :param custom_data: Additional order data.

        :return: OrderPreview object with information about the created order.

        Source: https://docs.wallet.tg/pay/#create-order
        """
        data = {
            "amount": {
                "currencyCode": currency_code,
                "amount": amount
            },
            "description": description,
            "externalId": external_id,
            "timeoutSeconds": timeout_seconds,
            "customerTelegramUserId": customer_telegram_user_id
        }
        if return_url:
            data["returnUrl"] = return_url
        if fail_return_url:
            data["failReturnUrl"] = fail_return_url
        if custom_data:
            data["customData"] = custom_data

        response_data = await self._make_request("POST", "order", data)
        if response_data.get("status") == "SUCCESS":
            return OrderPreview(response_data.get("data"))
        raise CreateOrderException(response_data, "Failed to create order")

    async def get_order_preview(self, order_id: str) -> OrderPreview:
        """
        Retrieve order information.

        :param order_id: Order ID.
        :return: OrderPreview object with information about the order.

        Source: https://docs.wallet.tg/pay/#get-order-preview
        """
        response_data = await self._make_request("GET", f"order/preview?id={order_id}")
        if response_data.get("status") == "SUCCESS":
            return OrderPreview(response_data.get("data"))
        raise GetOrderPreviewException(response_data, "Failed to retrieve order preview")

    async def get_order_list(self, offset: int, count: int) -> List[OrderReconciliationItem]:
        """
        Retrieve a list of orders.

        :param offset: Pagination offset.
        :param count: Number of orders to return.
        :return: List of OrderReconciliationItem objects.

        Source: https://docs.wallet.tg/pay/#get-order-list
        """
        response_data = await self._make_request("GET", f"reconciliation/order-list?offset={offset}&count={count}")
        if response_data.get("status") == "SUCCESS":
            orders_data = response_data.get("data", {}).get("items", [])
            return [OrderReconciliationItem(order_data) for order_data in orders_data]
        raise GetOrderListException(response_data, "Failed to retrieve order list")

    async def get_order_amount(self) -> int:
        """
        Retrieve the total amount of all orders.

        :return: Total order amount.

        Source: https://docs.wallet.tg/pay/#get-order-amount
        """
        response_data = await self._make_request("GET", "reconciliation/order-amount")
        if response_data.get("status") == "SUCCESS":
            return int(response_data.get("data", {}).get("totalAmount"))
        raise GetOrderAmountException(response_data, "Failed to retrieve order amount")
