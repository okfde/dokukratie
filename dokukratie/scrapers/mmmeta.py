from datetime import datetime, timedelta

from memorious import settings
from mmmeta import mmmeta
from servicelayer import env

from .util import ensure_date
from .util import get_env_or_context as _geoc


def get_start_date(context):
    if not settings.INCREMENTAL:
        return
    if env.get("MMMETA"):
        m = mmmeta()
        m.update()
        try:
            query = m.files.all(order_by="-published_at")
            file = next(query)
            while (
                file.get("published_at") is None
                or ensure_date(file.get("published_at")) > datetime.now().date()
            ):
                file = next(query)
            # go a bit backwards
            delta = _geoc(context, "START_DATE_DELTA", 7)  # 1 week
            delta = int(delta)
            start_date = ensure_date(file["published_at"])
            start_date = start_date - timedelta(days=delta)
            if start_date:
                context.log.info(f"Using START_DATE `{start_date}` from mmmeta state")
            return start_date
        except StopIteration:
            return
