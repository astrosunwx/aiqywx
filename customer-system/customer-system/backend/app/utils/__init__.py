"""工具函数"""

def format_phone(phone: str) -> str:
    """格式化手机号"""
    phone = phone.strip().replace(" ", "").replace("-", "")
    if len(phone) == 11 and phone.startswith("1"):
        return phone
    return None

def mask_phone(phone: str) -> str:
    """手机号脱敏显示"""
    if len(phone) == 11:
        return f"{phone[:3]}****{phone[-4:]}"
    return phone
