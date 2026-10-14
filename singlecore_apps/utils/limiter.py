import time
import functools
import logging

logger = logging.getLogger("api_limiter")

try:
    import frappe
except ImportError:
    frappe = None

def api_rate_limiter(max_req_per_sec=8, max_parallel=8):
    """
    Decorator Rate Limiter teruji untuk pemanggilan API eksternal (Accurate / SAP).
    1. Batas Frekuensi: Maksimal max_req_per_sec per detik.
    2. Batas Concurrency: Maksimal max_parallel worker paralel.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if frappe and hasattr(frappe, "cache"):
                redis_client = frappe.cache()
                active_workers_key = "singlecore_active_workers"
                active_workers = redis_client.incr(active_workers_key)
                
                if active_workers > max_parallel:
                    redis_client.decr(active_workers_key)
                    logger.warning("Rate limit concurrency hit. Retrying...")
                    time.sleep(1)
                    if hasattr(frappe, "RetryTaskError"):
                        raise frappe.RetryTaskError("Parallel worker limit hit.")
                
                try:
                    last_req_key = "singlecore_last_req_timestamp"
                    last_time = float(redis_client.get(last_req_key) or 0)
                    current_time = time.time()
                    elapsed = current_time - last_time
                    min_interval = 1.0 / max_req_per_sec
                    
                    if elapsed < min_interval:
                        time.sleep(min_interval - elapsed)
                    
                    redis_client.set(last_req_key, str(time.time()))
                    return func(*args, **kwargs)
                finally:
                    redis_client.decr(active_workers_key)
            else:
                # Fallback jika berjalan di luar Frappe framework
                min_interval = 1.0 / max_req_per_sec
                time.sleep(min_interval)
                return func(*args, **kwargs)
                
        return wrapper
    return decorator
