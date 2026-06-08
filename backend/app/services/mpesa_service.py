"""
M-Pesa Daraja API service layer.

Handles:
- OAuth token generation
- STK Push (Lipa na M-Pesa Online)
- Callback verification and processing
- Transaction status tracking

SAFETY:
- DEMO_PAYMENT_MODE=true always sends KSh 1 to Safaricom,
  while preserving the original displayed amount in the DB.
- No credentials are hardcoded; all come from environment variables.
"""
import os
import base64
import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any

import requests

from ..extensions import db
from ..models import Payment, Order, Appointment

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config from environment
# ---------------------------------------------------------------------------
_CONSUMER_KEY = os.getenv("MPESA_CONSUMER_KEY", "")
_CONSUMER_SECRET = os.getenv("MPESA_CONSUMER_SECRET", "")
_SHORTCODE = os.getenv("MPESA_SHORTCODE", "174379")
_PASSKEY = os.getenv("MPESA_PASSKEY", "")
_CALLBACK_URL = os.getenv("MPESA_CALLBACK_URL", "")
_ENV = os.getenv("MPESA_ENV", "sandbox").lower()
_DEMO_MODE = os.getenv("DEMO_PAYMENT_MODE", "true").lower() in ("1", "true", "yes")
_DEFAULT_PHONE = os.getenv("MPESA_DEFAULT_PHONE", "")

_BASE_URL = (
    "https://sandbox.safaricom.co.ke"
    if _ENV == "sandbox"
    else "https://api.safaricom.co.ke"
)

# ---------------------------------------------------------------------------
# Demo amount safety
# ---------------------------------------------------------------------------
DEMO_STK_AMOUNT = 1


def _get_access_token() -> str:
    """Fetch OAuth access token from Daraja."""
    url = f"{_BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
    credentials = base64.b64encode(
        f"{_CONSUMER_KEY}:{_CONSUMER_SECRET}".encode()
    ).decode()
    headers = {"Authorization": f"Basic {credentials}"}
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    token = data.get("access_token")
    if not token:
        raise RuntimeError(f"No access_token in Daraja response: {data}")
    return token


def _generate_password(timestamp: str) -> str:
    """Generate the Base64-encoded password for STK push."""
    raw = f"{_SHORTCODE}{_PASSKEY}{timestamp}"
    return base64.b64encode(raw.encode()).decode()


def normalize_phone(phone: str) -> str:
    """
    Normalize Kenyan phone numbers to 2547XXXXXXXX format.
    Supports: 0712..., 254712..., +254712...
    """
    cleaned = phone.strip().replace(" ", "").replace("-", "")
    if cleaned.startswith("+"):
        cleaned = cleaned[1:]
    if cleaned.startswith("0"):
        cleaned = "254" + cleaned[1:]
    if not cleaned.startswith("254"):
        # Assume it's missing country code and starts with 7/1
        cleaned = "254" + cleaned
    return cleaned


def is_valid_kenyan_phone(phone: str) -> bool:
    """Basic validation for Kenyan mobile numbers in 254XXXXXXXXX format."""
    if not phone:
        return False
    # Must be 12 digits starting with 2547 or 2541 or 2542
    return len(phone) == 12 and phone.startswith("254") and phone[3] in "712"


def get_demo_phone() -> str:
    """Return the default demo phone number from env."""
    return normalize_phone(_DEFAULT_PHONE or "254712345678")


def stk_push(
    payment_id: int,
    amount: float,
    phone_number: str,
    description: str = "MediAssist AI Payment",
) -> Dict[str, Any]:
    """
    Initiate an M-Pesa STK Push (Lipa na M-Pesa Online).

    DEMO MODE:
    - The *displayed* amount is stored on the Payment record.
    - The *actual* STK push amount is always 1 KSh when DEMO_PAYMENT_MODE is enabled.

    Returns:
        dict with keys: success (bool), message (str), checkout_request_id (str|None),
                        merchant_request_id (str|None), response_code (str|None)
    """
    token = _get_access_token()
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    password = _generate_password(timestamp)

    # Safety: demo mode always charges 1 KSh
    stk_amount = DEMO_STK_AMOUNT if _DEMO_MODE else int(round(amount))
    if stk_amount < 1:
        stk_amount = 1

    payload = {
        "BusinessShortCode": _SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": stk_amount,
        "PartyA": phone_number,
        "PartyB": _SHORTCODE,
        "PhoneNumber": phone_number,
        "CallBackURL": _CALLBACK_URL,
        "AccountReference": f"MA{payment_id}",
        "TransactionDesc": description[:20] if description else "Payment",
    }

    url = f"{_BASE_URL}/mpesa/stkpush/v1/processrequest"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    logger.info(
        "STK Push -> payment_id=%s phone=%s displayed_amount=%s stk_amount=%s",
        payment_id,
        phone_number,
        amount,
        stk_amount,
    )

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=45)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.RequestException as exc:
        logger.exception("STK Push request failed for payment_id=%s", payment_id)
        return {
            "success": False,
            "message": f"M-Pesa request failed: {exc}",
            "checkout_request_id": None,
            "merchant_request_id": None,
            "response_code": None,
        }

    response_code = data.get("ResponseCode")
    response_desc = data.get("ResponseDescription", "No description")
    checkout_request_id = data.get("CheckoutRequestID")
    merchant_request_id = data.get("MerchantRequestID")

    if response_code == "0":
        return {
            "success": True,
            "message": response_desc,
            "checkout_request_id": checkout_request_id,
            "merchant_request_id": merchant_request_id,
            "response_code": response_code,
        }
    else:
        logger.warning("STK Push declined: %s", data)
        return {
            "success": False,
            "message": response_desc,
            "checkout_request_id": checkout_request_id,
            "merchant_request_id": merchant_request_id,
            "response_code": response_code,
        }


def query_stk_status(checkout_request_id: str) -> Dict[str, Any]:
    """
    Query the status of an STK push transaction.
    Useful for polling when callbacks are delayed.
    """
    token = _get_access_token()
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    password = _generate_password(timestamp)

    payload = {
        "BusinessShortCode": _SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "CheckoutRequestID": checkout_request_id,
    }

    url = f"{_BASE_URL}/mpesa/stkpushquery/v1/query"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as exc:
        logger.exception("STK query failed for checkout_request_id=%s", checkout_request_id)
        return {
            "error": str(exc),
            "ResultCode": "-1",
            "ResultDesc": "Query request failed",
        }


def process_callback(callback_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process the M-Pesa callback payload.

    Updates the matching Payment record based on CheckoutRequestID.
    Also updates linked Order/Appointment payment_status on success.

    Returns:
        dict: {success: bool, message: str, payment_id: int|None}
    """
    body = callback_data.get("Body", {})
    stk_callback = body.get("stkCallback", {})
    merchant_request_id = stk_callback.get("MerchantRequestID")
    checkout_request_id = stk_callback.get("CheckoutRequestID")
    result_code = stk_callback.get("ResultCode")
    result_desc = stk_callback.get("ResultDesc", "")
    callback_metadata = stk_callback.get("CallbackMetadata", {})
    items = callback_metadata.get("Item", [])

    logger.info(
        "M-Pesa callback received: checkout=%s result_code=%s",
        checkout_request_id,
        result_code,
    )

    if not checkout_request_id:
        logger.warning("Callback missing CheckoutRequestID")
        return {"success": False, "message": "Missing CheckoutRequestID", "payment_id": None}

    payment = Payment.query.filter_by(
        transaction_reference=checkout_request_id
    ).first()

    if not payment:
        logger.warning("No payment found for checkout_request_id=%s", checkout_request_id)
        return {"success": False, "message": "Payment not found", "payment_id": None}

    # Idempotency: already processed
    if payment.status in ("success", "failed", "cancelled"):
        logger.info("Payment %s already finalized as %s", payment.id, payment.status)
        return {
            "success": payment.status == "success",
            "message": f"Payment already {payment.status}",
            "payment_id": payment.id,
        }

    # Extract metadata
    mpesa_receipt = None
    phone = None
    amount_paid = None
    transaction_date = None

    for item in items:
        name = item.get("Name")
        value = item.get("Value")
        if name == "MpesaReceiptNumber":
            mpesa_receipt = value
        elif name == "PhoneNumber":
            phone = str(value) if value else None
        elif name == "Amount":
            amount_paid = value
        elif name == "TransactionDate":
            transaction_date = str(value) if value else None

    if result_code == 0:
        payment.status = "success"
        payment.mpesa_receipt_number = mpesa_receipt
        payment.phone_number = phone
        payment.paid_at = datetime.utcnow()

        # Update linked order
        if payment.order:
            payment.order.payment_status = "paid"

        # Update linked appointment (if you track payment_status there)
        if payment.appointment:
            # Appointments don't have payment_status field currently,
            # but we can leave this hook for future use.
            pass

        db.session.commit()
        logger.info("Payment %s marked success. Receipt=%s", payment.id, mpesa_receipt)
        return {
            "success": True,
            "message": result_desc or "Payment successful",
            "payment_id": payment.id,
        }
    else:
        payment.status = "failed"
        payment.failure_reason = result_desc
        db.session.commit()
        logger.info("Payment %s marked failed: %s", payment.id, result_desc)
        return {
            "success": False,
            "message": result_desc or "Payment failed",
            "payment_id": payment.id,
        }


def is_demo_mode() -> bool:
    return _DEMO_MODE
