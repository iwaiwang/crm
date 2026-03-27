"""
发票二维码识别服务

中国增值税发票的二维码包含完整的发票信息，通过 pyzbar 和 OpenCV 识别
支持 PDF 文件自动转换为图片后识别
"""
import re
import os
import tempfile
from typing import Optional, Dict, Any, List


def parse_invoice_qr(qr_data: str) -> Dict[str, Any]:
    """
    解析发票二维码数据

    中国增值税发票二维码常见格式：
    格式 1（逗号分隔）：01,31, ,26337000000147471236,4294.47,20260130, ,DB9A
    格式 2（空格分隔）：01 26337000000147471236 11 >4051.39 230225 147471236 8820260130

    字段说明（逗号分隔格式）：
    - 01: 版本号
    - 31: 发票类型代码 (30=普票，31=专票，51=电子普票，53=电子专票)
    - (空): 保留
    - 26337000000147471236: 发票号码 (20 位)
    - 4294.47: 含税金额
    - 20260130: 开票日期 (YYYYMMDD)
    - (空): 保留
    - DB9A: 校验码
    """
    result = {
        'invoice_number': None,  # 发票号码 (20 位)
        'invoice_code': None,    # 发票代码 (可选)
        'invoice_date': None,    # 开票日期
        'check_code': None,      # 校验码
        'amount': None,          # 不含税金额
        'tax_amount': None,      # 税额
        'total_amount': None,    # 含税总额
        'invoice_type': None,    # 发票类型 (special=专票，normal=普票)
    }

    # 清理数据
    qr_data = qr_data.strip()

    # 尝试逗号分隔格式（优先）
    if ',' in qr_data:
        parts = [p.strip() for p in qr_data.split(',')]
        print(f"[QR] 逗号分隔格式，共 {len(parts)} 部分：{parts}")

        # 解析发票类型代码（第 2 个字段，索引 1）
        if len(parts) > 1:
            type_code = parts[1]
            if type_code in ['30', '51']:  # 30=普票，51=电子普票
                result['invoice_type'] = 'normal'
                print(f"[QR] 发票类型：普票 (代码{type_code})")
            elif type_code in ['31', '53']:  # 31=专票，53=电子专票
                result['invoice_type'] = 'special'
                print(f"[QR] 发票类型：专票 (代码{type_code})")

        # 查找 20 位数字作为发票号码
        for part in parts:
            if part.isdigit() and len(part) == 20:
                result['invoice_number'] = part
                print(f"[QR] 找到发票号码：{part}")
                break

        # 查找日期（8 位数字，格式 YYYYMMDD）
        for part in parts:
            if part.isdigit() and len(part) == 8:
                try:
                    year = int(part[:4])
                    month = int(part[4:6])
                    day = int(part[6:8])
                    if 2000 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31:
                        result['invoice_date'] = f"{year}-{month:02d}-{day:02d}"
                        print(f"[QR] 找到日期：{result['invoice_date']}")
                        break
                except:
                    pass

        # 查找金额（带小数点的数字）
        # 注意：二维码中的金额是价税合计（total_amount），二维码本身不含税率信息
        # 税率需要通过 OCR 识别发票明细行获取，此处不反推 amount 和 tax_amount
        for part in parts:
            try:
                if '.' in part:
                    amount = float(part)
                    if amount > 0:
                        # 这是价税合计（含税金额）
                        result['total_amount'] = amount
                        # 不含税金额和税额需要结合税率计算，此处暂不计算
                        # 因为二维码本身不含税率信息，硬编码假设会导致错误
                        print(f"[QR] 找到价税合计：{amount}")
                        break
            except:
                pass

        # 查找校验码（字母数字混合，4-20 位）
        for part in reversed(parts):
            if part and not part.isdigit() and len(part) >= 4:
                result['check_code'] = part
                print(f"[QR] 找到校验码：{part}")
                break
            elif part and part.isdigit() and 4 <= len(part) <= 20:
                if part != result['invoice_number'] and part != result['invoice_date']:
                    result['check_code'] = part
                    print(f"[QR] 找到校验码：{part}")
                    break

        if result['invoice_number'] and result['invoice_date']:
            return result

    # 尝试空格分隔格式（备用）
    parts = qr_data.split()
    print(f"[QR] 空格分隔格式，共 {len(parts)} 部分")

    if len(parts) >= 5:
        # 解析发票类型代码（第 2 个字段）
        if len(parts) > 1:
            type_code = parts[1]
            if type_code in ['30', '51']:
                result['invoice_type'] = 'normal'
                print(f"[QR] 发票类型：普票 (代码{type_code})")
            elif type_code in ['31', '53']:
                result['invoice_type'] = 'special'
                print(f"[QR] 发票类型：专票 (代码{type_code})")

        # 查找金额（带>或 + 符号的部分）
        # 注意：>4051.39 表示不含税金额，但二维码本身不含税率信息
        # 硬编码假设 6% 税率会导致错误，此处只记录不含税金额和价税合计
        amount_index = -1
        for i, part in enumerate(parts):
            if part.startswith('>') or part.startswith('+'):
                amount_index = i
                try:
                    # 这是不含税金额
                    result['amount'] = float(part[1:])
                    # 价税合计需要结合税率计算，此处暂不计算
                    print(f"[QR] 找到不含税金额：{result['amount']}")
                except:
                    pass
                break

        if amount_index >= 0:
            # 日期在金额后第一位
            if amount_index + 1 < len(parts):
                date_part = parts[amount_index + 1]
                if date_part.isdigit() and len(date_part) in [6, 8]:
                    if len(date_part) == 8:
                        result['invoice_date'] = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}"
                    else:
                        year = int(date_part[:2])
                        full_year = 2000 + year if year < 50 else 1900 + year
                        result['invoice_date'] = f"{full_year}-{date_part[2:4]}-{date_part[4:6]}"

            # 查找 20 位数字作为发票号码
            for part in parts:
                if part.isdigit() and len(part) == 20:
                    result['invoice_number'] = part
                    break

            # 校验码
            for i in range(len(parts) - 1, -1, -1):
                part = parts[i]
                if part.isdigit() and 8 <= len(part) <= 20 and len(part) != 20:
                    result['check_code'] = part
                    break

        if result['invoice_number'] and result['invoice_date']:
            return result

    # 备用方案：正则表达式
    # 查找 20 位数字作为发票号码
    invoice_match = re.search(r'(?<!\d)(\d{20})(?!\d)', qr_data)
    if invoice_match:
        result['invoice_number'] = invoice_match.group(1)

    # 查找日期
    date_match = re.search(r'(?<!\d)(\d{8})(?!\d)', qr_data)
    if date_match:
        date_str = date_match.group(1)
        try:
            year = int(date_str[:4])
            month = int(date_str[4:6])
            day = int(date_str[6:8])
            if 2000 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31:
                result['invoice_date'] = f"{year}-{month:02d}-{day:02d}"
        except:
            pass

    # 查找金额
    amount_match = re.search(r'(?<!\d)(\d+\.\d{2})(?!\d)', qr_data)
    if amount_match:
        amount = float(amount_match.group(1))
        # 假设这是含税金额
        result['total_amount'] = amount
        result['amount'] = round(amount / 1.06, 2)
        result['tax_amount'] = round(amount - result['amount'], 2)

    return result


def decode_qr_from_image(image_path: str) -> Optional[str]:
    """
    从图片中解码二维码

    Args:
        image_path: 图片文件路径

    Returns:
        二维码包含的文本数据，如果未找到则返回 None
    """
    try:
        import cv2
        from pyzbar import pyzbar
        from PIL import Image

        # 读取图片
        image = cv2.imread(image_path)
        if image is None:
            # 尝试用 PIL 读取
            pil_image = Image.open(image_path)
            import numpy as np
            image = np.array(pil_image)

        # 解码二维码
        barcodes = pyzbar.decode(image)

        for barcode in barcodes:
            if barcode.type in ['QRCODE']:
                qr_data = barcode.data.decode('utf-8')
                return qr_data

        return None
    except ImportError as e:
        print(f"[QR] 依赖库缺失：{e}")
        return None
    except Exception as e:
        print(f"[QR] 二维码识别失败：{e}")
        return None


def convert_pdf_to_image(pdf_path: str, dpi: int = 200) -> List[str]:
    """
    将 PDF 转换为 PNG 图片
    使用 pypdfium2 库（不需要 poppler）

    Args:
        pdf_path: PDF 文件路径
        dpi: 转换分辨率，默认 200

    Returns:
        生成的图片路径列表（每页一张图片）
    """
    try:
        import pypdfium2 as pdfium

        # 打开 PDF
        pdf = pdfium.PdfDocument(pdf_path)

        # 保存到临时文件
        temp_dir = tempfile.mkdtemp()
        image_paths = []

        for i in range(len(pdf)):
            # 渲染页面
            page = pdf[i]
            bitmap = page.render(scale=dpi/72)

            # 保存为 PNG
            image_path = os.path.join(temp_dir, f'page_{i+1}.png')
            bitmap.to_pil().save(image_path, 'PNG')
            image_paths.append(image_path)

        pdf.close()

        print(f"[QR] PDF 转换成功，共 {len(image_paths)} 页")
        return image_paths

    except ImportError as e:
        print(f"[QR] pypdfium2 库缺失：{e}")
        return []
    except Exception as e:
        print(f"[QR] PDF 转换失败：{e}")
        return []


def cleanup_temp_images(image_paths: List[str]):
    """清理临时图片文件"""
    try:
        import shutil
        if image_paths:
            temp_dir = os.path.dirname(image_paths[0])
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                print(f"[QR] 已清理临时文件")
    except Exception as e:
        print(f"[QR] 清理临时文件失败：{e}")


def recognize_invoice_from_qr(file_path: str, file_ext: str = None) -> Dict[str, Any]:
    """
    从发票图片中识别二维码并解析发票信息
    支持 PDF 文件自动转换为图片后识别

    Args:
        file_path: 发票文件路径
        file_ext: 文件扩展名（可选，如果不传则从路径推断）

    Returns:
        解析后的发票信息
    """
    # 确定文件类型
    if not file_ext:
        file_ext = os.path.splitext(file_path)[1].lower().lstrip('.')

    image_paths = []
    temp_created = False

    try:
        # 如果是 PDF，先转换为图片
        if file_ext == 'pdf':
            print(f"[QR] 检测到 PDF 文件，开始转换...")
            image_paths = convert_pdf_to_image(file_path)
            if not image_paths:
                return {
                    'success': False,
                    'error': 'PDF 转换失败',
                    'data': None,
                    'confidence': 0
                }
            temp_created = True
            # 使用第一页进行识别
            file_path = image_paths[0]
            print(f"[QR] 使用第 1 页进行二维码识别")

        # 从图片中解码二维码
        qr_data = decode_qr_from_image(file_path)

        if not qr_data:
            return {
                'success': False,
                'error': '未找到发票二维码',
                'data': None,
                'confidence': 0
            }

        print(f"[QR] 二维码原始数据：{qr_data}")

        # 解析二维码数据
        parsed_data = parse_invoice_qr(qr_data)

        print(f"[QR] === 解析后的数据 ===")
        for key, value in parsed_data.items():
            print(f"[QR]   {key}: {value}")
        print(f"[QR] ====================")

        # 检查是否成功解析关键字段
        if not parsed_data.get('invoice_number') and not parsed_data.get('invoice_date'):
            return {
                'success': False,
                'error': '无法从二维码中解析发票信息',
                'data': None,
                'confidence': 0
            }

        # 计算税率
        import logging
        logging.info(f"[QR DEBUG] 开始计算税率，parsed_data={parsed_data}")
        tax_rate = None
        if parsed_data.get('amount') and parsed_data.get('tax_amount'):
            try:
                amount = float(parsed_data['amount'])
                tax_amount = float(parsed_data['tax_amount'])
                if amount > 0:
                    tax_rate = round(tax_amount / amount, 4)  # 保留 4 位小数，如 0.06
                    logging.info(f"[QR DEBUG] 计算税率成功：tax_rate={tax_rate}")
            except Exception as e:
                logging.info(f"[QR DEBUG] 计算税率失败：{e}")
                pass
        else:
            logging.info(f"[QR DEBUG] 缺少 amount 或 tax_amount 字段")

        logging.info(f"[QR DEBUG] 返回数据：tax_rate={tax_rate}")
        return {
            'success': True,
            'data': {
                'invoice_number': parsed_data.get('invoice_number'),
                'invoice_code': parsed_data.get('invoice_code'),
                'invoice_date': parsed_data.get('invoice_date'),
                'check_code': parsed_data.get('check_code'),
                'amount': parsed_data.get('amount'),
                'tax_amount': parsed_data.get('tax_amount'),
                'total_amount': parsed_data.get('total_amount'),
                'tax_rate': tax_rate,  # 税率（小数形式，如 0.06 表示 6%）
                'invoice_type': parsed_data.get('invoice_type'),
            },
            'confidence': 0.95,
            'qr_raw_data': qr_data
        }

    except Exception as e:
        print(f"[QR] 识别异常：{str(e)}")
        return {
            'success': False,
            'error': f'识别失败：{str(e)}',
            'data': None,
            'confidence': 0
        }

    finally:
        # 清理临时文件
        if temp_created and image_paths:
            cleanup_temp_images(image_paths)
