import hashlib


def get_device_id(request):
    """
    Extract device info from request headers.
    """
    return request.headers.get('User-Agent')


def generate_device_hash(request):
    """
    Generate SHA-256 hash from device fingerprint.
    """
    device_info = get_device_id(request)

    if not device_info:
        return None

    return hashlib.sha256(device_info.encode()).hexdigest()
