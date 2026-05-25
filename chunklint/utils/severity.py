SEVERITY_ORDER = {"low": 1, "medium": 2, "high": 3}


def normalize_severity(value: str) -> str:
    severity = value.lower().strip()
    if severity not in SEVERITY_ORDER:
        raise ValueError(f"Unsupported severity: {value}")
    return severity


def at_or_above(severity: str, threshold: str) -> bool:
    return SEVERITY_ORDER[normalize_severity(severity)] >= SEVERITY_ORDER[
        normalize_severity(threshold)
    ]


def max_severity(left: str, right: str) -> str:
    left_value = normalize_severity(left)
    right_value = normalize_severity(right)
    if SEVERITY_ORDER[left_value] >= SEVERITY_ORDER[right_value]:
        return left_value
    return right_value

