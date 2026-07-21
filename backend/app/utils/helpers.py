"""共享工具函数"""
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Optional


def clean_text(value: Optional[str]) -> Optional[str]:
    """清理文本，空字符串转为 None"""
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def to_decimal(value, default: str = "0") -> Decimal:
    """安全转换为 Decimal，自动去除货币符号和常见 OCR 噪声字符"""
    if value in (None, ""):
        return Decimal(default)
    cleaned = (
        str(value)
        .replace(",", "")
        .replace("¥", "")
        .replace("￥", "")
        .replace("楼", "")
        .replace("%", "")
        .strip()
    )
    try:
        return Decimal(cleaned)
    except (InvalidOperation, ValueError, TypeError):
        return Decimal(default)


def to_date(value) -> Optional[date]:
    """安全转换为日期，支持多种常见格式"""
    if not value:
        return None
    if isinstance(value, date):
        return value
    cleaned = str(value).strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"):
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue
    return None


def recommend_expense_category(seller_name: Optional[str], remark: Optional[str]) -> str:
    """根据供应商名称和备注推荐费用分类"""
    text = f"{seller_name or ''} {remark or ''}".lower()

    if any(kw in text for kw in ["餐", "饭", "酒店", "住宿", "机票", "车票", "火车", "打车", "滴滴", "出行", "差旅", "旅行"]):
        return "travel"
    if any(kw in text for kw in ["采购", "进货", "原料", "材料", "设备", "物资", "耗材", "货物", "器材"]):
        return "procurement"
    if any(kw in text for kw in ["办公", "文具", "纸张", "打印机", "电脑", "IT", "软件", "系统", "服务", "云", "服务器", "域名", "阿里云", "腾讯云", "订阅", "license", "saas", "平台", "技术服务", "打印"]):
        return "software" if any(kw in text for kw in ["软件", "系统", "云", "服务器", "域名", "订阅", "license", "saas", "平台", "技术服务"]) else "office"
    if any(kw in text for kw in ["房租", "租金", "物业", "租赁"]):
        return "rent"
    if any(kw in text for kw in ["水电", "电费", "水费", "燃气", "宽带", "网络"]):
        return "utilities"
    if any(kw in text for kw in ["工资", "薪资", "薪酬", "奖金", "提成"]):
        return "salary"
    if any(kw in text for kw in ["推广", "广告", "营销", "市场", "宣传", "投放", "百度", "抖音", "快手", "小红书"]):
        return "marketing"
    if any(kw in text for kw in ["维修", "维护", "修理", "保养", "配件"]):
        return "maintenance"
    if any(kw in text for kw in ["培训", "学习", "课程", "教育", "会议"]):
        return "training"
    if any(kw in text for kw in ["招待", "宴请", "礼品", "送礼", "接待"]):
        return "entertainment"
    if any(kw in text for kw in ["快递", "物流", "运输", "配送", "发货", "邮寄", "运费", "货运"]):
        return "logistics"

    return "other"


def normalize_party_name(value: Optional[str]) -> str:
    """标准化公司名称（去除公司后缀和括号，转小写）"""
    normalized = clean_text(value) or ""
    for token in ["（", "）", "(", ")", "有限责任公司", "有限公司", "股份有限公司", "公司", " ", "　"]:
        normalized = normalized.replace(token, "")
    return normalized.lower()


def normalize_tax_rate(value) -> Decimal:
    """标准化税率（>1 时除以 100）"""
    rate = to_decimal(value)
    if rate > 1:
        rate = (rate / Decimal("100")).quantize(Decimal("0.0001"))
    return rate


def build_invoice_remark(invoice_no: Optional[str], prefix: str) -> str:
    """构建发票备注"""
    return f"{prefix} - 发票号: {clean_text(invoice_no) or '未知'}"
