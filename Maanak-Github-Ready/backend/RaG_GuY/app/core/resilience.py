import functools
import json
import inspect
from app.core.config import settings

def with_failover(func):
    """
    Resiliency Engine Decorator.
    Wraps an async generator function, catching API rate limits and cycling through backup keys from settings.
    Safely injects 'current_key' if accepted by the target function.
    """
    sig = inspect.signature(func)
    accepts_key = "current_key" in sig.parameters or any(
        p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()
    )

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        for api_key in settings.OPENROUTER_KEYS:
            try:
                print(f"\n[FAILOVER ENGINE] Attempting generation with key: {api_key}")
                
                kwargs_copy = kwargs.copy()
                if accepts_key:
                    kwargs_copy["current_key"] = api_key
                
                async for chunk in func(*args, **kwargs_copy):
                    yield chunk
                
                # Exit loop on success
                return
            except Exception as e:
                print(f"[FAILOVER ENGINE] Key '{api_key}' failed: {e}")

        # All keys failed fallback
        print("[FAILOVER ENGINE] ALL KEYS DEPLETED. Sending fallback.")
        fallback = {"type": "token", "content": "System overloaded, please try again."}
        yield f"data: {json.dumps(fallback)}\n\n"
        yield "data: [DONE]\n\n"

    return wrapper
