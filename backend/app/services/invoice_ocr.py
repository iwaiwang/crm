"""
发票 OCR 识别服务
使用 RapidOCR 识别发票购买方和销售方信息
"""
import re
import os
from typing import Dict, Any, Optional, List

try:
    from rapidocr_onnxruntime import RapidOCR
    HAS_RAPIDOCR = True
except ImportError:
    HAS_RAPIDOCR = False
    print("[WARNING] rapidocr_onnxruntime 未安装，OCR 功能不可用")


class InvoiceOCR:
    """发票 OCR 识别服务"""

    def __init__(self):
        if HAS_RAPIDOCR:
            self.ocr = RapidOCR()
        else:
            self.ocr = None

    def is_available(self) -> bool:
        """检查 OCR 服务是否可用"""
        return HAS_RAPIDOCR and self.ocr is not None

    def extract_text_with_position(self, image_path: str) -> List:
        """提取文本及其位置信息"""
        if not self.ocr:
            return []
        result, _ = self.ocr(image_path)
        return result  # [([[x1,y1], [x2,y2], [x3,y3], [x4,y4]], '文本', 置信度), ...]

    def extract_invoice_fields(self, image_path: str) -> Dict[str, Any]:
        """
        提取发票字段信息

        Args:
            image_path: 发票图片路径

        Returns:
            提取的字段信息字典
        """
        result = {
            'success': False,
            'error': None,
            'data': {
                'buyer_name': None,
                'buyer_tax_id': None,
                'buyer_bank': None,
                'seller_name': None,
                'seller_tax_id': None,
                'seller_bank': None,
                'tax_rate': None,  # 税率
            }
        }

        if not self.is_available():
            result['error'] = 'OCR 服务不可用'
            return result

        if not os.path.exists(image_path):
            result['error'] = '图片文件不存在'
            return result

        try:
            # OCR 识别
            ocr_result = self.extract_text_with_position(image_path)
            if not ocr_result:
                result['error'] = '未识别到任何文本'
                return result

            # 获取图片尺寸用于位置判断
            import cv2
            image = cv2.imread(image_path)
            h, w = image.shape[:2]

            # 转换为便于处理的格式
            all_texts = [(text, box, conf) for box, text, conf in ocr_result]

            # 判断发票类型：查找是否包含"专用"字样
            invoice_type = None
            for text, box, conf in all_texts:
                if '增值税专用发票' in text:
                    invoice_type = 'special'
                    break
                elif '增值税普通发票' in text or '电子普通发票' in text:
                    invoice_type = 'normal'
                    break

            # 如果没找到明确标识，根据版式判断（左右分布通常是专票）
            if invoice_type is None:
                # 收集所有包含公司关键词的文本
                company_texts = []
                for text, box, conf in all_texts:
                    clean_text = text.strip()
                    if any(kw in clean_text for kw in ['公司', '厂', '店', '部', '中心']) and len(clean_text) >= 5:
                        center_x = (box[0][0] + box[2][0]) / 2
                        center_y = (box[0][1] + box[2][1]) / 2
                        company_texts.append({'text': clean_text, 'x': center_x, 'y': center_y})

                if len(company_texts) >= 2:
                    x_coords = [c['x'] for c in company_texts]
                    x_range = max(x_coords) - min(x_coords)
                    if x_range > w * 0.2:  # 左右分布
                        invoice_type = 'special'
                    else:  # 上下分布
                        invoice_type = 'normal'
                else:
                    invoice_type = 'normal'  # 默认普票

            result['data']['invoice_type'] = invoice_type
            print(f"[OCR] 发票类型：{invoice_type}")

            # 提取公司名称和税号
            # 收集所有包含公司关键词的文本
            company_texts = []
            for text, box, conf in all_texts:
                clean_text = text.strip()
                if any(kw in clean_text for kw in ['公司', '厂', '店', '部', '中心']) and len(clean_text) >= 5:
                    center_x = (box[0][0] + box[2][0]) / 2
                    center_y = (box[0][1] + box[2][1]) / 2
                    name = clean_text.replace('名称：', '').replace('名称:', '').replace('称：', '').strip()
                    company_texts.append({'text': name, 'x': center_x, 'y': center_y, 'box': box})

            # 判断发票格式：左右分布 or 上下分布
            if len(company_texts) >= 2:
                # 计算 X 坐标的范围
                x_coords = [c['x'] for c in company_texts]
                x_range = max(x_coords) - min(x_coords)

                if x_range > w * 0.2:  # X 坐标差异大，左右分布（专票）
                    for c in company_texts:
                        if c['x'] < w / 2:
                            if result['data']['buyer_name'] is None:
                                result['data']['buyer_name'] = c['text']
                        else:
                            if result['data']['seller_name'] is None:
                                result['data']['seller_name'] = c['text']
                else:  # 上下分布（普票）
                    # 按 Y 坐标排序，上方是购买方，下方是销售方
                    company_texts.sort(key=lambda c: c['y'])
                    if result['data']['buyer_name'] is None:
                        result['data']['buyer_name'] = company_texts[0]['text']
                    if len(company_texts) >= 2 and result['data']['seller_name'] is None:
                        result['data']['seller_name'] = company_texts[1]['text']

            # 提取税号（统一社会信用代码）
            tax_ids = []
            for text, box, conf in all_texts:
                if '纳税人' in text or '识别号' in text:
                    match = re.search(r'[A-Za-z0-9]{15,20}', text)
                    if match:
                        tax_id = match.group()
                        center_x = (box[0][0] + box[2][0]) / 2
                        center_y = (box[0][1] + box[2][1]) / 2
                        tax_ids.append({'text': tax_id, 'x': center_x, 'y': center_y})

            # 根据税号位置分配给购买方/销售方
            # 左右分布时按 X 坐标匹配，上下分布时按 Y 坐标匹配
            use_x_matching = x_range > w * 0.2  # 与公司名称相同的分布逻辑

            if result['data']['buyer_name']:
                # 找离购买方名称最近的税号
                buyer_pos = None
                for c in company_texts:
                    if c['text'] == result['data']['buyer_name']:
                        buyer_pos = c['x'] if use_x_matching else c['y']
                        break

                if buyer_pos:
                    min_dist = float('inf')
                    best_tax = None
                    for t in tax_ids:
                        t_pos = t['x'] if use_x_matching else t['y']
                        dist = abs(t_pos - buyer_pos)
                        if dist < min_dist:
                            min_dist = dist
                            best_tax = t['text']
                    if best_tax:
                        result['data']['buyer_tax_id'] = best_tax

            if result['data']['seller_name']:
                # 找离销售方名称最近的税号
                seller_pos = None
                for c in company_texts:
                    if c['text'] == result['data']['seller_name']:
                        seller_pos = c['x'] if use_x_matching else c['y']
                        break

                if seller_pos:
                    min_dist = float('inf')
                    best_tax = None
                    for t in tax_ids:
                        t_pos = t['x'] if use_x_matching else t['y']
                        dist = abs(t_pos - seller_pos)
                        if dist < min_dist:
                            min_dist = dist
                            best_tax = t['text']
                    if best_tax:
                        result['data']['seller_tax_id'] = best_tax

            # 提取银行账号（在发票下半部分，纯数字 10-20 位）
            for text, box, conf in all_texts:
                clean = text.replace('-', '').replace(' ', '')
                if 10 <= len(clean) <= 20 and clean.isdigit():
                    center_x = (box[0][0] + box[2][0]) / 2
                    center_y = (box[0][1] + box[2][1]) / 2

                    # 必须在下半部分，且不是发票号码等
                    if center_y > h * 0.3:
                        # 排除已知的非银行账号
                        if '发票号码' in text or '开票日期' in text:
                            continue
                        if result['data']['buyer_tax_id'] and result['data']['buyer_tax_id'] in text:
                            continue
                        if result['data']['seller_tax_id'] and result['data']['seller_tax_id'] in text:
                            continue

                        if center_x < w / 2:
                            if result['data']['buyer_bank'] is None:
                                result['data']['buyer_bank'] = text.strip()
                        else:
                            if result['data']['seller_bank'] is None:
                                result['data']['seller_bank'] = text.strip()

            # 提取税率（关键词：税率、税额、征收率等）
            # 常见税率：1%, 3%, 5%, 6%, 9%, 11%, 13%
            tax_rate_patterns = [
                r'税率 [：:\s]*(\d+(?:\.\d+)?\s*%?)',
                r'征收率 [：:\s]*(\d+(?:\.\d+)?\s*%?)',
                r'税额.*?(\d+(?:\.\d+)?\s*%?)',
                r'(\d+(?:\.\d+)?)\s*%\s*税率',
            ]

            for text, box, conf in all_texts:
                for pattern in tax_rate_patterns:
                    match = re.search(pattern, text)
                    if match:
                        tax_rate_str = match.group(1).replace('%', '').strip()
                        try:
                            tax_rate = float(tax_rate_str)
                            # 如果是小数形式（如 0.06），转换为百分比数字（6）
                            if tax_rate < 1:
                                tax_rate = tax_rate * 100
                            result['data']['tax_rate'] = tax_rate
                            print(f"[OCR] 识别到税率：{tax_rate}%")
                            break
                        except ValueError:
                            pass
                if result['data']['tax_rate']:
                    break

            # 如果没有找到税率，尝试直接识别独立的百分比值（如 13%、6% 等）
            # 这是备用方案，用于识别发票表格中的税率列
            if result['data']['tax_rate'] is None:
                for text, box, conf in all_texts:
                    # 匹配独立的百分比值，如 13%、6%、3% 等
                    match = re.match(r'^(\d+(?:\.\d+)?)\s*%$', text.strip())
                    if match:
                        tax_rate_str = match.group(1)
                        try:
                            tax_rate = float(tax_rate_str)
                            # 常见税率范围检查（1-20% 之间）
                            if 1 <= tax_rate <= 20:
                                result['data']['tax_rate'] = tax_rate
                                print(f"[OCR] 识别到独立税率：{tax_rate}%")
                                break
                        except ValueError:
                            pass

            # 检查是否提取到至少一个字段
            data = result['data']
            if (data['buyer_name'] or data['buyer_tax_id'] or
                data['seller_name'] or data['seller_tax_id']):
                result['success'] = True
            else:
                result['error'] = '未找到购买方或销售方信息'

            return result

        except Exception as e:
            result['error'] = f'识别失败：{str(e)}'
            return result


# 便捷函数
def recognize_invoice_fields(image_path: str) -> Dict[str, Any]:
    """
    识别发票字段（便捷函数）

    Args:
        image_path: 发票图片路径

    Returns:
        识别结果字典
    """
    ocr = InvoiceOCR()
    return ocr.extract_invoice_fields(image_path)
