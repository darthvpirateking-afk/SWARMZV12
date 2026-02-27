import queue
from nexusmon.hologram.hologram_ingestor import HologramIngestor
from nexusmon.hologram.hologram_reconciler import HologramReconciler, HologramPublisher
from nexusmon.hologram.hologram_api import create_hologram_api


def bootstrap_hologram(feed_stream, event_bus, main_fastapi_app=None, auth_check=None):
    """Wire together the full hologram state engine.

    Args:
        feed_stream:       FeedStream instance (wrapping an EventBus).
        event_bus:         Underlying EventBus (kept for future extensions).
        main_fastapi_app:  If provided, mount the hologram sub-app at /hologram.
        auth_check:        Optional callable(request) -> bool for /patch auth.

    Returns:
        (reconciler, publisher, ingestor)         — when main_fastapi_app is given.
        (reconciler, publisher, ingestor, holo_app) — when main_fastapi_app is None.
    """
    update_q = queue.Queue()
    publisher = HologramPublisher()
    reconciler = HologramReconciler(
        update_queue=update_q,
        publisher=publisher,
        batch_ms=200,
        snapshot_interval=5,
    )
    reconciler.start()
    ingestor = HologramIngestor(feed_stream=feed_stream, update_queue=update_q, batch_ms=100)
    hologram_app = create_hologram_api(
        reconciler=reconciler,
        publisher=publisher,
        auth_check=auth_check,
    )
    if main_fastapi_app is not None:
        main_fastapi_app.mount("/hologram", hologram_app)
        return reconciler, publisher, ingestor
    return reconciler, publisher, ingestor, hologram_app
