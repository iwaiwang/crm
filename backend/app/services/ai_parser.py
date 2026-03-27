"""
AI 文档解析服务

支持 OpenAI 兼容 API：
- 阿里云百炼 (DashScope)
- DeepSeek
- Moonshot (Kimi)
- ChatGPT
- 本地 Ollama
"""
import os
import json
import httpx
import base64
import uuid
from typing import Optional, Dict, Any
from datetime import datetime


# AI 服务配置
class AIServiceConfig:
    """AI 服务配置（内存缓存）"""
    # 启用的服务类型：openai_compatible | ollama
    SERVICE_TYPE: str = "openai_compatible"

    # OpenAI 兼容 API 配置
    API_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    API_KEY: str = ""
    MODEL: str = "qwen-vl-plus"  # 推荐使用视觉模型

    # Ollama 配置（备用）
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5-vl:7b"

    # 请求超时 (秒)
    TIMEOUT: int = 120

    # 是否启用
    ENABLED: bool = True


# 合同解析提示词
CONTRACT_SYSTEM_PROMPT = """你是一个专业的合同信息提取助手。请从提供的合同文档中提取关键信息，并以 JSON 格式返回。

需要提取的字段：
- contract_no: 合同编号
- contract_name: 合同名称/标题
- customer_name: 甲方/客户单位名称
- supplier_name: 乙方/供应商名称
- amount: 合同总金额（数字）
- sign_date: 签订日期 (YYYY-MM-DD)
- start_date: 合同开始日期 (YYYY-MM-DD)
- end_date: 合同结束日期 (YYYY-MM-DD)
- payment_terms: 付款方式/账期
- remarks: 其他重要条款备注

输出格式要求（必须是有效的 JSON）：
{
    "data": {
        "contract_no": "HT-2024-001",
        "contract_name": "软件开发合同",
        "customer_name": "某某科技公司",
        "amount": 100000,
        "sign_date": "2024-01-01",
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "payment_terms": "分期付款",
        "remarks": ""
    },
    "confidence": 0.92
}

如果某个字段无法确定，设为 null。
"""

# 发票解析提示词（图片用）
INVOICE_SYSTEM_PROMPT = """你是一个专业的发票信息提取助手。请从提供的发票图片中提取关键信息，并以 JSON 格式返回。

需要提取的字段：
- invoice_type: 发票类型（增值税专用发票/增值税普通发票/电子发票等）
- invoice_code: 发票代码（10-12 位）
- invoice_number: 发票号码（8 位）
- invoice_date: 开票日期 (YYYY-MM-DD)
- check_code: 校验码后 6 位
- amount: 金额（不含税，数字）
- tax_rate: 税率（如 1%, 3%, 5%, 6%, 9%, 11%, 13% 等，数字形式如 0.01, 0.03, 0.06, 0.13）
- tax_amount: 税额（数字）
- total_amount: 价税合计（数字）
- buyer_name: 购买方名称
- buyer_tax_id: 购买方纳税人识别号
- seller_name: 销售方名称
- seller_tax_id: 销售方纳税人识别号
- remarks: 备注

输出格式要求（必须是有效的 JSON）：
{
    "data": {
        "invoice_type": "增值税专用发票",
        "invoice_code": "1100123456",
        "invoice_number": "12345678",
        "invoice_date": "2024-01-15",
        "check_code": "123456",
        "amount": 10000,
        "tax_rate": 0.06,
        "tax_amount": 600,
        "total_amount": 10600,
        "buyer_name": "某某公司",
        "buyer_tax_id": "91110000XXXXXXXXXX",
        "seller_name": "某某销售公司",
        "seller_tax_id": "91110000XXXXXXXXXX"
    },
    "confidence": 0.95
}

如果某个字段无法确定，设为 null。
"""

# 发票解析提示词（PDF 纯文本用）
INVOICE_TEXT_PROMPT = """你是一个专业的发票信息提取助手。请从提供的发票文本中提取关键信息，并以 JSON 格式返回。

输入内容是从 PDF 发票中提取的纯文本，可能包含格式混乱、字符识别错误等问题。请仔细识别以下字段：

需要提取的字段：
- invoice_type: 发票类型（如：增值税专用发票、增值税普通发票、电子普通发票等）
- invoice_code: 发票代码（10-12 位数字）
- invoice_number: 发票号码（8 位数字）
- invoice_date: 开票日期 (YYYY-MM-DD)
- check_code: 校验码后 6 位
- amount: 金额（不含税，数字）
- tax_rate: 税率（如 1%, 3%, 5%, 6%, 9%, 11%, 13% 等，数字形式如 0.01, 0.03, 0.05, 0.06, 0.09, 0.11, 0.13）
- tax_amount: 税额（数字）
- total_amount: 价税合计（数字）
- buyer_name: 购买方名称
- buyer_tax_id: 购买方纳税人识别号
- seller_name: 销售方名称
- seller_tax_id: 销售方纳税人识别号
- remarks: 备注

输出格式要求（必须是有效的 JSON）：
{
    "data": {
        "invoice_type": "增值税专用发票",
        "invoice_code": "1100123456",
        "invoice_number": "12345678",
        "invoice_date": "2024-01-15",
        "check_code": "123456",
        "amount": 10000,
        "tax_rate": 0.06,
        "tax_amount": 600,
        "total_amount": 10600,
        "buyer_name": "某某公司",
        "buyer_tax_id": "91110000XXXXXXXXXX",
        "seller_name": "某某销售公司",
        "seller_tax_id": "91110000XXXXXXXXXX"
    },
    "confidence": 0.95
}

注意：
1. 文本可能包含 OCR 识别错误或格式问题，请根据上下文推断正确内容
2. 如果某个字段无法确定，设为 null
3. 金额字段只返回数字，不要包含货币符号或逗号
4. 税率请返回小数形式（如 6% 返回 0.06）
"""


class OpenAICompatibleService:
    """OpenAI 兼容 API 服务"""

    def __init__(self, api_base_url: str = None, api_key: str = None, model: str = None, timeout: int = None):
        self.api_url = api_base_url or AIServiceConfig.API_BASE_URL
        self.api_key = api_key or AIServiceConfig.API_KEY
        self.model = model or AIServiceConfig.MODEL
        self.timeout = timeout or AIServiceConfig.TIMEOUT

    async def check_health(self) -> bool:
        """检查服务是否可用"""
        if not self.api_key:
            return False
        try:
            async with httpx.AsyncClient() as client:
                # 使用 chat/completions 测试连接（兼容性更好）
                response = await client.post(
                    f"{self.api_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": "Hello"}],
                        "max_tokens": 1
                    },
                    timeout=10
                )
                # 200 或 400（模型不存在）都说明 API 可达
                return response.status_code in [200, 400]
        except Exception:
            return False

    async def chat_with_vision(self, prompt: str, image_data: bytes) -> Dict[str, Any]:
        """
        使用视觉模型进行分析

        Args:
            prompt: 提示词
            image_data: 图片数据

        Returns:
            模型响应
        """
        # 将图片转换为 base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')

        # 检测图片类型
        # 简单判断，实际可以检测文件头
        mime_type = "image/png"  # 默认

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": prompt
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "请分析这张图片，提取关键信息并以 JSON 格式返回。"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 2000,
            "temperature": 0.1
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()

            return result

    async def chat(self, prompt: str, text: str, model: str = None) -> Dict[str, Any]:
        """
        纯文本对话

        Args:
            prompt: 系统提示词
            text: 用户输入
            model: 可选的模型名称，不传则使用默认模型

        Returns:
            模型响应
        """
        payload = {
            "model": model or self.model,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": text}
            ],
            "max_tokens": 2000,
            "temperature": 0.1
        }

        print(f"[DEBUG] API URL: {self.api_url}/chat/completions")
        print(f"[DEBUG] 使用模型：{model or self.model}")
        # 避免打印过长的 payload 导致编码问题
        print(f"[DEBUG] Payload 长度：{len(str(payload))} 字符")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.api_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload,
                    timeout=self.timeout
                )
                print(f"[DEBUG] 响应状态码：{response.status_code}")
                # 只打印响应的前 200 字符，避免编码问题
                response_text = response.text[:200] if response.text else 'empty'
                print(f"[DEBUG] 响应内容：{response_text.encode('utf-8', errors='replace').decode('utf-8')}")
                response.raise_for_status()
                result = response.json()

                return result
            except httpx.HTTPStatusError as e:
                print(f"[DEBUG] HTTP 错误：{e.response.status_code}")
                # 使用 errors='replace' 处理无法编码的字符
                error_text = e.response.text[:200] if e.response.text else 'empty'
                print(f"[DEBUG] HTTP 错误详情：{error_text.encode('utf-8', errors='replace').decode('utf-8')}")
                raise


class OllamaService:
    """Ollama 本地服务（备用）"""

    def __init__(self, base_url: str = None, model: str = None, timeout: int = None):
        self.base_url = base_url or AIServiceConfig.OLLAMA_BASE_URL
        self.model = model or AIServiceConfig.OLLAMA_MODEL
        self.timeout = timeout or AIServiceConfig.TIMEOUT

    async def check_health(self) -> bool:
        """检查服务是否可用"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/tags", timeout=10)
                return response.status_code == 200
        except Exception:
            return False

    async def generate(self, prompt: str) -> Dict[str, Any]:
        """生成响应"""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "top_p": 0.9,
            }
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()


class AIService:
    """AI 解析服务（支持 OpenAI 兼容 API）"""

    def __init__(self):
        self._load_config_from_memory()
        self.openai_service = None
        self.ollama_service = None
        self._init_services()

    def _load_config_from_memory(self):
        """从内存配置加载"""
        self.service_type = AIServiceConfig.SERVICE_TYPE
        self.api_base_url = AIServiceConfig.API_BASE_URL
        self.api_key = AIServiceConfig.API_KEY
        self.model = AIServiceConfig.MODEL
        self.ollama_base_url = AIServiceConfig.OLLAMA_BASE_URL
        self.ollama_model = AIServiceConfig.OLLAMA_MODEL
        self.timeout = AIServiceConfig.TIMEOUT
        self.enabled = AIServiceConfig.ENABLED

    def _init_services(self):
        """初始化子服务"""
        if self.service_type == "openai_compatible":
            self.openai_service = OpenAICompatibleService(
                api_base_url=self.api_base_url,
                api_key=self.api_key,
                model=self.model,
                timeout=self.timeout
            )
        else:
            self.ollama_service = OllamaService(
                base_url=self.ollama_base_url,
                model=self.ollama_model,
                timeout=self.timeout
            )

    def load_config_from_db(self, config_dict: Dict[str, Any]):
        """从数据库配置加载"""
        self.service_type = config_dict.get("service_type", "openai_compatible")
        self.api_base_url = config_dict.get("api_base_url", AIServiceConfig.API_BASE_URL)
        self.api_key = config_dict.get("api_key", AIServiceConfig.API_KEY)
        self.model = config_dict.get("model", AIServiceConfig.MODEL)
        self.ollama_base_url = config_dict.get("ollama_base_url", AIServiceConfig.OLLAMA_BASE_URL)
        self.ollama_model = config_dict.get("ollama_model", AIServiceConfig.OLLAMA_MODEL)
        self.timeout = config_dict.get("timeout", AIServiceConfig.TIMEOUT)
        self.enabled = config_dict.get("enabled", AIServiceConfig.ENABLED)
        self._init_services()

    def save_config_to_db(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """保存配置到数据库（需要外部调用）"""
        # 这个方法由 API 调用，更新内存配置
        AIServiceConfig.SERVICE_TYPE = config_dict.get("service_type", "openai_compatible")
        AIServiceConfig.API_BASE_URL = config_dict.get("api_base_url", AIServiceConfig.API_BASE_URL)
        AIServiceConfig.API_KEY = config_dict.get("api_key", AIServiceConfig.API_KEY)
        AIServiceConfig.MODEL = config_dict.get("model", AIServiceConfig.MODEL)
        AIServiceConfig.OLLAMA_BASE_URL = config_dict.get("ollama_base_url", AIServiceConfig.OLLAMA_BASE_URL)
        AIServiceConfig.OLLAMA_MODEL = config_dict.get("ollama_model", AIServiceConfig.OLLAMA_MODEL)
        AIServiceConfig.TIMEOUT = config_dict.get("timeout", AIServiceConfig.TIMEOUT)
        AIServiceConfig.ENABLED = config_dict.get("enabled", True)
        self._load_config_from_memory()
        self._init_services()
        return self.get_config()

    async def check_health(self) -> bool:
        """检查 AI 服务是否可用"""
        if not self.enabled:
            return False
        if self.service_type == "openai_compatible":
            if not self.openai_service:
                self._init_services()
            return await self.openai_service.check_health()
        else:
            if not self.ollama_service:
                self._init_services()
            return await self.ollama_service.check_health()

    async def refresh_health_check(self) -> bool:
        """强制重新检查 AI 服务健康状态（忽略缓存）"""
        if not self.enabled:
            return False

        if self.service_type == "openai_compatible":
            # 直接测试 API 连接，不使用缓存
            if not self.api_key:
                return False
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.api_base_url}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": self.model,
                            "messages": [{"role": "user", "content": "Hello"}],
                            "max_tokens": 1
                        },
                        timeout=10
                    )
                    return response.status_code in [200, 400]
            except Exception:
                return False
        else:
            if not self.ollama_service:
                self._init_services()
            return await self.ollama_service.check_health()

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """
        从模型响应中解析 JSON

        Args:
            content: 模型返回的文本内容

        Returns:
            解析后的 JSON 数据
        """
        try:
            # 尝试直接解析
            return json.loads(content)
        except json.JSONDecodeError:
            # 尝试提取 JSON 部分
            try:
                # 查找 JSON 开始和结束
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = content[json_start:json_end]
                    return json.loads(json_str)
                else:
                    return {"error": "无法解析 JSON 输出", "raw": content}
            except Exception:
                return {"error": "JSON 解析失败", "raw": content}

    async def extract_text_from_pdf(self, file_path: str) -> str:
        """从 PDF 提取文本（使用 PyMuPDF/fitz）"""
        try:
            import fitz  # PyMuPDF
            text = ""
            doc = fitz.open(file_path)
            for page in doc:
                page_text = page.get_text()
                if page_text:
                    text += page_text + "\n"
            doc.close()
            return text
        except ImportError:
            raise Exception("未安装 pymupdf 库，请运行 pip install pymupdf")
        except Exception as e:
            raise Exception(f"PDF 文本提取失败：{str(e)}")

    async def parse_contract(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """
        解析合同

        Args:
            file_path: 文件路径
            file_type: 文件类型 (pdf/doc/docx/jpg/png)

        Returns:
            解析结果
        """
        if self.service_type == "openai_compatible":
            # 使用 OpenAI 兼容 API
            with open(file_path, "rb") as f:
                file_data = f.read()

            # 如果是 PDF，先提取文本
            if file_type == "pdf":
                text = await self.extract_text_from_pdf(file_path)
                if not text:
                    return {"error": "无法从 PDF 中提取文本", "confidence": 0}

                # 使用文本模式分析
                result = await self.openai_service.chat(CONTRACT_SYSTEM_PROMPT, text)
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                return self._parse_json_response(content)
            else:
                # 图片使用视觉模型
                result = await self.openai_service.chat_with_vision(CONTRACT_SYSTEM_PROMPT, file_data)
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                return self._parse_json_response(content)
        else:
            # Ollama 备用方案
            text = await self.extract_text_from_pdf(file_path)
            if not text:
                return {"error": "无法从文件中提取文本", "confidence": 0}
            return {
                "data": {"contract_name": text[:100] if text else ""},
                "confidence": 0.5
            }

    async def parse_invoice(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """
        解析发票

        Args:
            file_path: 文件路径
            file_type: 文件类型 (pdf/jpg/png)

        Returns:
            解析结果
        """
        if self.service_type == "openai_compatible":
            # PDF 文件：先提取文本，再通过大模型提取内容
            if file_type == "pdf":
                text = await self.extract_text_from_pdf(file_path)
                if not text:
                    return {"error": "无法从 PDF 中提取文本", "confidence": 0}

                print(f"[DEBUG] PDF 提取的文本长度：{len(text)}")
                # 避免打印包含特殊字符的文本导致编码错误
                print(f"[DEBUG] PDF 提取的文本前 100 字符：{text[:100].encode('utf-8', errors='replace').decode('utf-8')}")

                # 使用文本模式分析（PDF 专用提示词）
                print("[DEBUG] 正在调用阿里云百炼 API 进行发票解析...")
                print(f"[DEBUG] 使用模型：{self.model}")
                try:
                    # 使用配置的模型
                    result = await self.openai_service.chat(INVOICE_TEXT_PROMPT, text)
                    # 避免打印包含特殊字符的响应导致编码错误
                    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    print(f"[DEBUG] AI 响应内容长度：{len(content)}")

                    parsed = self._parse_json_response(content)
                    print(f"[DEBUG] 解析后的 JSON: {parsed}")

                    return parsed
                except Exception as e:
                    print(f"[DEBUG] AI 调用失败，错误类型：{type(e).__name__}")
                    # 避免打印包含特殊字符的错误信息导致编码错误
                    error_msg = str(e).encode('utf-8', errors='replace').decode('utf-8')
                    print(f"[DEBUG] AI 调用失败，错误信息：{error_msg}")
                    raise
            else:
                # 图片文件（jpg/png）：直接使用视觉模型分析
                with open(file_path, "rb") as f:
                    file_data = f.read()
                print(f"[DEBUG] 图片文件大小：{len(file_data)} bytes")

                try:
                    result = await self.openai_service.chat_with_vision(INVOICE_SYSTEM_PROMPT, file_data)
                    print(f"[DEBUG] AI 原始响应：{result}")

                    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    print(f"[DEBUG] AI 响应内容：{content}")

                    parsed = self._parse_json_response(content)
                    print(f"[DEBUG] 解析后的 JSON: {parsed}")

                    return parsed
                except Exception as e:
                    print(f"[DEBUG] AI 调用失败，错误类型：{type(e).__name__}")
                    print(f"[DEBUG] AI 调用失败，错误信息：{str(e)}")
                    raise
        else:
            # Ollama 备用方案
            return {
                "data": {},
                "confidence": 0.5
            }

    def get_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        return {
            "service_type": self.service_type,
            "api_base_url": self.api_base_url,
            "api_key": self.api_key,
            "model": self.model,
            "ollama_base_url": self.ollama_base_url,
            "ollama_model": self.ollama_model,
            "timeout": self.timeout,
            "enabled": self.enabled,
        }


# 全局 AI 服务实例
ai_service = AIService()
