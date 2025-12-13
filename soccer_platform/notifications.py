from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from sqlalchemy.future import select
from .config import settings
from .models import User, SystemSetting

async def send_game_processed_notification(db, game_id):
    try:
        # 1. Fetch System Settings for Mail
        settings_res = await db.execute(select(SystemSetting).where(SystemSetting.key.in_([
            "MAIL_USERNAME", "MAIL_PASSWORD", "MAIL_FROM", "MAIL_PORT", "MAIL_SERVER"
        ])))
        db_settings = {s.key: s.value for s in settings_res.scalars().all()}
        
        # Use DB settings or Fallback to Env
        username = db_settings.get("MAIL_USERNAME", settings.MAIL_USERNAME)
        password = db_settings.get("MAIL_PASSWORD", settings.MAIL_PASSWORD)
        mail_from = db_settings.get("MAIL_FROM", settings.MAIL_FROM)
        port = int(db_settings.get("MAIL_PORT", settings.MAIL_PORT))
        server = db_settings.get("MAIL_SERVER", settings.MAIL_SERVER)
        
        if not server or not username:
            print("Mail not configured via DB or Env. Skipping.")
            return

        conf = ConnectionConfig(
            MAIL_USERNAME = username,
            MAIL_PASSWORD = password,
            MAIL_FROM = mail_from,
            MAIL_PORT = port,
            MAIL_SERVER = server,
            MAIL_FROM_NAME = settings.MAIL_FROM_NAME,
            MAIL_STARTTLS = True,
            MAIL_SSL_TLS = False,
            USE_CREDENTIALS = True,
            VALIDATE_CERTS = True 
        )
        
        # 2. Get recipients (Admins & Coaches)
        query = select(User).where(User.role.in_(["admin", "coach"]))
        result = await db.execute(query)
        users = result.scalars().all()
        
        # Filter valid emails
        recipients = [u.username for u in users if "@" in u.username]
        
        if recipients:
            message = MessageSchema(
                subject=f"Game Processed: {game_id}",
                recipients=recipients,
                body=f"The game {game_id} has been processed and is ready for viewing.",
                subtype=MessageType.html
            )
            
            fm = FastMail(conf)
            await fm.send_message(message)
            print(f"Sent notifications to {recipients}")
            
    except Exception as e:
        print(f"Failed to send email: {e}")
