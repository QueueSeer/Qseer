import httpx
import logging

from app.core.config import settings

logger = logging.getLogger('uvicorn.error')

Trigger_URL = settings.TRIGGER_URL
Trigger_SECRET = settings.TRIGGER_SECRET
protocal = "http://"

headers = {
    "accept": "application/json",
    "Authorization": "Bearer " + Trigger_SECRET,
    "Content-Type": "application/json",
}


async def send_generic_email():
    pass


async def send_verify_email(email, verify_url):
    myobj = {
        'url': verify_url,
        'email': email
    }
    path = "/api/email/send_verify_email"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                protocal + Trigger_URL + path,
                json=myobj,
                headers=headers,
                timeout=30
            )
            success = response.is_success
        except httpx.TimeoutException:
            success = False
    if not success:
        logger.warning(f"Failed to send email to {email}")
        logger.warning(f"Url: {verify_url}")
    return success


async def send_verify_seer_email(email, verify_url):
    myobj = {
        'url': verify_url,
        'email': email
    }
    path = "/api/email/send_verify_seer_email"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                protocal + Trigger_URL + path,
                json=myobj,
                headers=headers,
                timeout=30
            )
            success = response.is_success
        except httpx.TimeoutException:
            success = False
    if not success:
        logger.warning(f"Failed to send email to {email}")
        logger.warning(f"Url: {verify_url}")
    return success


async def send_change_password(email, verify_url):
    myobj = {
        'url': verify_url,
        'email': email
    }
    path = "/api/email/send_change_password_email"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                protocal + Trigger_URL + path,
                json=myobj,
                headers=headers,
                timeout=30
            )
            success = response.is_success
        except httpx.TimeoutException:
            success = False
    if not success:
        logger.warning(f"Failed to send email to {email}")
        logger.warning(f"Url: {verify_url}")
    return success
