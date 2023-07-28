from fastapi import APIRouter

from app.utils import send_email

router = APIRouter()


@router.post('/send_email')
async def send_email_route(to_email: str, subject: str, message: str):
    if send_email(to_email, subject, message):
        return {'message': 'Email sent successfully'}
    else:
        return {'message': 'Failed to send email'}
