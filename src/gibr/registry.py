"""Registry for issue tracker implementations."""

TRACKER_REGISTRY = {}


def register_tracker(key, display_name, supported=True):
    """Register a tracker class using this decorator."""

    def decorator(cls):
        cls.display_name = display_name
        TRACKER_REGISTRY[key] = {
            "class": cls,
            "display_name": display_name,
            "supported": supported,
        }
        return cls

    return decorator


def get_tracker_class(key: str):
    """Return the tracker class by key (e.g. 'github')."""
    tracker_info = TRACKER_REGISTRY.get(key)
    if not tracker_info:
        raise ValueError(f"Unsupported tracker type: {key}")
    return tracker_info["class"]
