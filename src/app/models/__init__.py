"""Database models package - imports all models to register them with SQLAlchemy."""

# Import all model modules to register them with SQLAlchemy Base
# This ensures all tables are created and foreign key relationships are resolved

# Import all models (noqa: F401 to ignore unused import warnings)
from app.models import user  # noqa: F401
from app.models import admin  # noqa: F401
from app.models import chat  # noqa: F401
from app.models import document  # noqa: F401
from app.models import support_ticket  # noqa: F401
from app.models import external_api  # noqa: F401
from app.models import marja  # noqa: F401
from app.models import storage  # noqa: F401
from app.models import subscription  # noqa: F401
from app.models import environment  # noqa: F401
