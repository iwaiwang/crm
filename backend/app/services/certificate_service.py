"""数字证书服务 — RSA 密钥生成、X.509 签名、加解密"""
import os
import datetime
import uuid
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend


_ENCRYPTION_KEY = None

_KEY_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "data",
    "cert_encryption.key",
)


def _get_encryption_key() -> bytes:
    """获取或生成 AES 加密密钥。优先从环境变量读取，否则从本地文件读取，否则生成并持久化。"""
    global _ENCRYPTION_KEY
    if _ENCRYPTION_KEY is not None:
        return _ENCRYPTION_KEY
    env_key = os.environ.get("CERT_ENCRYPTION_KEY")
    if env_key:
        _ENCRYPTION_KEY = env_key.encode("utf-8")[:32].ljust(32, b"\x00")
        return _ENCRYPTION_KEY
    if os.path.exists(_KEY_FILE):
        with open(_KEY_FILE, "rb") as f:
            _ENCRYPTION_KEY = f.read()
        return _ENCRYPTION_KEY
    _ENCRYPTION_KEY = os.urandom(32)
    os.makedirs(os.path.dirname(_KEY_FILE), exist_ok=True)
    with open(_KEY_FILE, "wb") as f:
        f.write(_ENCRYPTION_KEY)
    return _ENCRYPTION_KEY


def set_encryption_key(key_hex: str) -> None:
    """从数据库 settings 加载持久化的加密密钥"""
    global _ENCRYPTION_KEY
    _ENCRYPTION_KEY = bytes.fromhex(key_hex)


def generate_certificate(customer_name: str, product_name: str, start_date: datetime.date, end_date: datetime.date) -> dict:
    """生成 RSA 2048 位密钥对和 X.509 v3 证书。返回 {cert_pem, key_pem, encrypted_key_pem, serial}。"""
    # 生成 RSA 密钥对
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend(),
    )
    public_key = private_key.public_key()
    serial = str(uuid.uuid4().int)[:32]

    # 构建证书主题
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "CN"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Pyxis CRM"),
        x509.NameAttribute(NameOID.COMMON_NAME, customer_name),
        x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, product_name),
    ])

    # 构建 X.509 v3 证书
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(public_key)
        .serial_number(int(serial, 16) % (2**63))
        .not_valid_before(datetime.datetime.combine(start_date, datetime.time(0, 0, 0)))
        .not_valid_after(datetime.datetime.combine(end_date, datetime.time(23, 59, 59)))
        .add_extension(
            x509.BasicConstraints(ca=False, path_length=None),
            critical=True,
        )
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False,
                content_commitment=False,
            ),
            critical=True,
        )
        .sign(private_key, hashes.SHA256(), default_backend())
    )

    cert_pem = cert.public_bytes(serialization.Encoding.PEM).decode("utf-8")
    key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    encrypted_key_pem = _encrypt_private_key(key_pem)

    return {
        "cert_pem": cert_pem,
        "key_pem": key_pem,
        "encrypted_key_pem": encrypted_key_pem,
        "serial": f"SN-{serial[:16]}",
    }


def decrypt_private_key(encrypted_pem: str) -> str:
    """解密加密存储的私钥"""
    data = bytes.fromhex(encrypted_pem)
    iv = data[:16]
    ciphertext = data[16:]
    key = _get_encryption_key()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded = decryptor.update(ciphertext) + decryptor.finalize()
    # Remove PKCS7 padding
    pad_len = padded[-1]
    return padded[:-pad_len].decode("utf-8")


def _encrypt_private_key(key_pem: str) -> str:
    """AES-256-CBC 加密私钥"""
    key = _get_encryption_key()
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    plaintext = key_pem.encode("utf-8")
    # PKCS7 padding
    pad_len = 16 - (len(plaintext) % 16)
    padded = plaintext + bytes([pad_len]) * pad_len
    ciphertext = encryptor.update(padded) + encryptor.finalize()
    return (iv + ciphertext).hex()
