import environ
from django.core.management.utils import get_random_secret_key

env = environ.Env(
    DEBUG=(bool, False),
    SECRET_KEY=(str, get_random_secret_key()),
    ALLOWED_HOSTS=(list, ["localhost"]),
    CSRF_TRUSTED_ORIGINS=(list, ["http://localhost"]),
    # Database
    DATABASE_URL=(str, "sqlite:///db.sqlite3"),
    # Redis
    REDIS_URL=(str, "redis://localhost:6379/0"),
    # Custom app variables
    COMPANY_NAME=(str, "GastroFlow"),
    BOSS_USERNAME=(str, "Boss"),
    BOSS_PASSWORD=(str, "GFboss123"),
    WORKERS_USERNAME=(str, "Workers"),
    WORKERS_PASSWORD=(str, "GFworkers123"),
    # Email variables
    HOST_EMAIL=(str, ""),
    HOST_PASSWORD=(str, ""),
)
