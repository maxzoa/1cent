def is_admin(user_id: int, allowed: frozenset[int]) -> bool:
    return user_id in allowed
