from sqlalchemy import create_engine
from thymis_controller.config import global_settings

engine = create_engine(global_settings.DATABASE_URL)
