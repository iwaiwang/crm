<template>
  <div class="guide-page">
    <div class="page-header">
      <h2>证书使用指南</h2>
    </div>

    <el-card class="section-card">
      <template #header><h3>概述</h3></template>
      <p>数字证书用于验证医院端软件的授权合法性。每份证书包含 RSA 2048 位密钥对和 X.509 v3 数字签名，由 CRM 系统统一签发管理。</p>
      <p>证书有效期通常为 12-36 个月。到期前 CRM 会提醒续期，超过 2 年未续期的证书，医院端软件将在使用中随机弹出授权提醒。</p>
    </el-card>

    <el-card class="section-card">
      <template #header><h3>证书生命周期</h3></template>
      <el-steps :active="5" align-center>
        <el-step title="申请" description="运维人员在CRM提交申请" />
        <el-step title="审核" description="两级审批后自动签发" />
        <el-step title="下载" description="下载ZIP包(证书+私钥)" />
        <el-step title="安装" description="安装到医院端软件目录" />
        <el-step title="续期" description="到期前续期，保持授权有效" />
      </el-steps>
    </el-card>

    <el-card class="section-card">
      <template #header><h3>下载与安装</h3></template>
      <el-steps direction="vertical">
        <el-step title="下载证书包" description="在证书管理页面，找到已签发的证书，点击「下载」按钮，获取 ZIP 文件。">
          <template #description>
            <p>在证书管理页面，找到状态为「已签发」的证书，点击「下载」。ZIP 包内包含两个文件：</p>
            <ul>
              <li><code>{医院名}_{软件产品名}_certificate.pem</code> — X.509 证书（公钥 + 签名）</li>
              <li><code>{医院名}_{软件产品名}_private_key.pem</code> — RSA 私钥（解密后使用）</li>
            </ul>
          </template>
        </el-step>
        <el-step title="放置文件">
          <template #description>
            <p>在医院端服务器的软件安装目录下创建 <code>license/</code> 文件夹，将两个 .pem 文件放入其中：</p>
            <pre class="code-block">软件安装目录/
├── license/
│   ├── certificate.pem      ← X.509 证书
│   └── private_key.pem      ← RSA 私钥
└── YourApp.exe</pre>
          </template>
        </el-step>
        <el-step title="软件集成" description="医院端软件启动时读取证书并验证，详见下方代码示例。" />
      </el-steps>
    </el-card>

    <el-card class="section-card">
      <template #header><h3>验证流程</h3></template>
      <p>医院端软件在启动时（以及运行期间定期）执行以下验证：</p>
      <el-steps direction="vertical" :space="80">
        <el-step title="1. 加载证书">
          <template #description>
            从 <code>license/certificate.pem</code> 读取 X.509 证书，解析有效期、颁发者等信息。
          </template>
        </el-step>
        <el-step title="2. 校验有效期">
          <template #description>
            检查当前日期是否在证书的 <code>not_valid_before</code> 和 <code>not_valid_after</code> 之间：
            <ul>
              <li>未到期 → 正常使用</li>
              <li>到期但未超过 2 年 → 弹出提醒通知运维续期</li>
              <li>到期超过 2 年 → 使用中随机弹出授权过期提醒</li>
            </ul>
          </template>
        </el-step>
        <el-step title="3. 校验签名">
          <template #description>
            使用证书中的公钥验证证书签名，确保证书未被篡改。
          </template>
        </el-step>
        <el-step title="4. 授权确认">
          <template #description>
            验证通过后正常启动；验证失败则拒绝启动并提示联系管理员。
          </template>
        </el-step>
      </el-steps>
    </el-card>

    <el-card class="section-card">
      <template #header><h3>代码示例</h3></template>

      <el-tabs v-model="activeLang" type="border-card">
        <!-- Python -->
        <el-tab-pane label="Python" name="python">
          <pre class="code-block">"""
证书验证模块 (Python)
适用于 PyQt5 / PySide6 桌面应用，或 Flask/FastAPI 服务端。
"""
import os
import datetime
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.exceptions import InvalidSignature
from pathlib import Path


class LicenseValidator:
    """数字证书许可证验证器"""

    def __init__(self, license_dir: str = None):
        if license_dir is None:
            # 默认在应用程序同级目录下的 license/ 文件夹
            license_dir = Path(__file__).parent / "license"
        self.license_dir = Path(license_dir)
        self.cert_path = self.license_dir / "certificate.pem"
        self.key_path = self.license_dir / "private_key.pem"

    def validate(self) -> dict:
        """验证证书，返回 {valid, message, customer, product, expires}"""
        # 1. 检查文件是否存在
        if not self.cert_path.exists():
            return {"valid": False, "message": "未找到证书文件，请将 certificate.pem 放入 license/ 目录"}
        if not self.key_path.exists():
            return {"valid": False, "message": "未找到私钥文件，请将 private_key.pem 放入 license/ 目录"}

        # 2. 加载证书
        with open(self.cert_path, "rb") as f:
            cert = x509.load_pem_x509_certificate(f.read(), default_backend())

        # 3. 加载私钥
        with open(self.key_path, "rb") as f:
            private_key = serialization.load_pem_private_key(f.read(), password=None, backend=default_backend())

        # 4. 检查有效期
        now = datetime.datetime.utcnow()
        days_remaining = (cert.not_valid_after_utc - now).days

        if now < cert.not_valid_before_utc:
            return {"valid": False, "message": "证书尚未生效"}

        if now > cert.not_valid_after_utc:
            years_expired = abs(days_remaining) / 365.0
            if years_expired > 2:
                return {
                    "valid": False,
                    "message": f"证书已过期 {years_expired:.1f} 年，请联系管理员续期。",
                    "expired": True,
                    "expired_years": years_expired,
                }
            return {
                "valid": False,
                "message": f"证书已过期 {-days_remaining} 天，请尽快联系管理员续期。",
                "expired": True,
            }

        # 5. 验证公钥匹配（用私钥签名一段数据，用证书公钥验证）
        test_data = b"license_challenge_" + str(cert.serial_number).encode()
        try:
            signature = private_key.sign(test_data, padding.PKCS1v15(), hashes.SHA256())
            cert.public_key().verify(signature, test_data, padding.PKCS1v15(), hashes.SHA256())
        except InvalidSignature:
            return {"valid": False, "message": "证书与私钥不匹配，证书可能被篡改"}

        # 6. 提取证书信息
        def get_attr(oid):
            attrs = cert.subject.get_attributes_for_oid(oid)
            return attrs[0].value if attrs else ""

        return {
            "valid": True,
            "message": "证书验证通过",
            "customer": get_attr(NameOID.COMMON_NAME),
            "product": get_attr(NameOID.ORGANIZATIONAL_UNIT_NAME),
            "expires": cert.not_valid_after_utc.strftime("%Y-%m-%d"),
            "days_remaining": days_remaining,
        }


# ===== 使用示例 =====
if __name__ == "__main__":
    validator = LicenseValidator()
    result = validator.validate()
    if result["valid"]:
        print(f"✓ 授权有效 — 客户: {result['customer']}, 产品: {result['product']}")
        print(f"  有效期至: {result['expires']} (剩余 {result['days_remaining']} 天)")
    else:
        print(f"✗ 授权无效 — {result['message']}")
        if result.get("expired_years", 0) > 2:
            import random  # 超过2年随机弹窗
            if random.random() < 0.2:
                print("⚠ 您的软件授权已严重过期，请立即联系管理员！")</pre>
        </el-tab-pane>

        <!-- C# -->
        <el-tab-pane label="C# (.NET)" name="csharp">
          <pre class="code-block">/*
证书验证模块 (C#)
适用于 WinForms / WPF 桌面应用。
需要 NuGet 包: System.Security.Cryptography.Xml
*/
using System;
using System.IO;
using System.Security.Cryptography;
using System.Security.Cryptography.X509Certificates;
using System.Text;

public class LicenseValidator
{
    private readonly string _licenseDir;

    public LicenseValidator(string licenseDir = null)
    {
        _licenseDir = licenseDir ?? Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "license");
    }

    public ValidationResult Validate()
    {
        string certPath = Path.Combine(_licenseDir, "certificate.pem");
        string keyPath = Path.Combine(_licenseDir, "private_key.pem");

        // 1. 检查文件是否存在
        if (!File.Exists(certPath))
            return new ValidationResult(false, "未找到证书文件");
        if (!File.Exists(keyPath))
            return new ValidationResult(false, "未找到私钥文件");

        // 2. 加载证书
        string certPem = File.ReadAllText(certPath);
        var cert = new X509Certificate2(
            Encoding.UTF8.GetBytes(certPem)
        );

        // 3. 加载私钥
        string keyPem = File.ReadAllText(keyPath);
        using var rsa = RSA.Create();
        rsa.ImportFromPem(keyPem);

        // 4. 检查有效期
        DateTime now = DateTime.UtcNow;
        double daysRemaining = (cert.NotAfter - now).TotalDays;

        if (now < cert.NotBefore)
            return new ValidationResult(false, "证书尚未生效");

        if (now > cert.NotAfter)
        {
            double yearsExpired = Math.Abs(daysRemaining) / 365.0;
            if (yearsExpired > 2)
                return new ValidationResult(false,
                    $"证书已过期 {yearsExpired:F1} 年，请立即联系管理员续期。")
                { Expired = true, ExpiredYears = yearsExpired };
            return new ValidationResult(false,
                $"证书已过期 {-daysRemaining:F0} 天，请尽快续期。")
            { Expired = true };
        }

        // 5. 验证公钥匹配
        byte[] testData = Encoding.UTF8.GetBytes(
            "license_challenge_" + cert.GetSerialNumberString()
        );
        byte[] signature = rsa.SignData(testData, HashAlgorithmName.SHA256,
            RSASignaturePadding.Pkcs1);

        bool keyMatch = cert.GetRSAPublicKey().VerifyData(
            testData, signature, HashAlgorithmName.SHA256,
            RSASignaturePadding.Pkcs1
        );
        if (!keyMatch)
            return new ValidationResult(false, "证书与私钥不匹配");

        // 6. 提取信息
        return new ValidationResult(true, "证书验证通过")
        {
            Customer = cert.GetNameInfo(X509NameType.SimpleName, false),
            Expires = cert.NotAfter.ToString("yyyy-MM-dd"),
            DaysRemaining = daysRemaining,
        };
    }
}

public class ValidationResult
{
    public bool Valid { get; set; }
    public string Message { get; set; }
    public string Customer { get; set; }
    public string Expires { get; set; }
    public double DaysRemaining { get; set; }
    public bool Expired { get; set; }
    public double ExpiredYears { get; set; }

    public ValidationResult(bool valid, string message)
    {
        Valid = valid;
        Message = message;
    }
}

// ===== 使用示例 =====
// 在 Program.cs 或 App.xaml.cs 的启动事件中：
//
// var validator = new LicenseValidator();
// var result = validator.Validate();
// if (!result.Valid)
// {
//     MessageBox.Show(result.Message, "授权验证失败",
//         MessageBoxButtons.OK, MessageBoxIcon.Warning);
//     if (result.ExpiredYears > 2 && new Random().NextDouble() < 0.2)
//     {
//         MessageBox.Show("您的软件授权已严重过期，请立即联系管理员！",
//             "授权提醒", MessageBoxButtons.OK, MessageBoxIcon.Error);
//     }
//     Environment.Exit(1);
// }</pre>
        </el-tab-pane>

        <!-- Java -->
        <el-tab-pane label="Java" name="java">
          <pre class="code-block">/*
证书验证模块 (Java)
适用于 Swing / JavaFX 桌面应用，或 Spring Boot 服务端。
需要 BouncyCastle 依赖 (build.gradle):
  implementation 'org.bouncycastle:bcpkix-jdk18on:1.78'
*/
import org.bouncycastle.asn1.x500.RDN;
import org.bouncycastle.asn1.x500.X500Name;
import org.bouncycastle.asn1.x500.style.BCStyle;
import org.bouncycastle.cert.X509CertificateHolder;
import org.bouncycastle.cert.jcajce.JcaX509CertificateConverter;
import org.bouncycastle.openssl.PEMKeyPair;
import org.bouncycastle.openssl.PEMParser;
import org.bouncycastle.openssl.jcajce.JcaPEMKeyConverter;

import java.io.*;
import java.nio.file.*;
import java.security.*;
import java.security.cert.X509Certificate;
import java.time.*;
import java.time.temporal.ChronoUnit;
import java.util.*;

public class LicenseValidator {

    private final Path licenseDir;

    public LicenseValidator() {
        this.licenseDir = Paths.get(System.getProperty("user.dir"), "license");
    }

    public LicenseValidator(Path licenseDir) {
        this.licenseDir = licenseDir;
    }

    public ValidationResult validate() {
        Path certPath = licenseDir.resolve("certificate.pem");
        Path keyPath = licenseDir.resolve("private_key.pem");

        // 1. 检查文件
        if (!Files.exists(certPath))
            return new ValidationResult(false, "未找到证书文件");
        if (!Files.exists(keyPath))
            return new ValidationResult(false, "未找到私钥文件");

        try {
            // 2. 加载证书
            X509Certificate cert;
            try (PEMParser parser = new PEMParser(new FileReader(certPath.toFile()))) {
                X509CertificateHolder holder = (X509CertificateHolder) parser.readObject();
                cert = new JcaX509CertificateConverter()
                    .setProvider("BC").getCertificate(holder);
            }

            // 3. 加载私钥
            PrivateKey privateKey;
            try (PEMParser parser = new PEMParser(new FileReader(keyPath.toFile()))) {
                PEMKeyPair keyPair = (PEMKeyPair) parser.readObject();
                privateKey = new JcaPEMKeyConverter().setProvider("BC")
                    .getKeyPair(keyPair).getPrivate();
            }

            // 4. 检查有效期
            Instant now = Instant.now();
            LocalDate expiryDate = cert.getNotAfter().toInstant()
                .atZone(ZoneId.of("UTC")).toLocalDate();
            LocalDate today = LocalDate.now(ZoneId.of("UTC"));
            long daysRemaining = ChronoUnit.DAYS.between(today, expiryDate);

            if (cert.getNotBefore().toInstant().isAfter(now))
                return new ValidationResult(false, "证书尚未生效");

            if (cert.getNotAfter().toInstant().isBefore(now)) {
                double yearsExpired = Math.abs(daysRemaining) / 365.0;
                if (yearsExpired > 2)
                    return new ValidationResult(false,
                        String.format("证书已过期 %.1f 年，请立即联系管理员续期。", yearsExpired));
                return new ValidationResult(false,
                    String.format("证书已过期 %d 天，请尽快续期。", -daysRemaining));
            }

            // 5. 验证公钥匹配
            byte[] testData = ("license_challenge_" + cert.getSerialNumber()).getBytes();
            Signature sig = Signature.getInstance("SHA256withRSA");
            sig.initSign(privateKey);
            sig.update(testData);
            byte[] signature = sig.sign();

            sig.initVerify(cert.getPublicKey());
            sig.update(testData);
            if (!sig.verify(signature))
                return new ValidationResult(false, "证书与私钥不匹配");

            // 6. 提取信息
            X500Name subject = new X500Name(cert.getSubjectX500Principal().getName());
            String customer = getCN(subject);
            return new ValidationResult(true, "证书验证通过", customer, expiryDate, daysRemaining);

        } catch (Exception e) {
            return new ValidationResult(false, "证书验证异常: " + e.getMessage());
        }
    }

    private String getCN(X500Name name) {
        RDN[] rdns = name.getRDNs(BCStyle.CN);
        return rdns.length > 0 ? rdns[0].getFirst().getValue().toString() : "";
    }

    // ==== 结果类 ====
    public static class ValidationResult {
        public final boolean valid;
        public final String message;
        public final String customer;
        public final LocalDate expires;
        public final long daysRemaining;

        public ValidationResult(boolean valid, String message) {
            this(valid, message, "", null, 0);
        }

        public ValidationResult(boolean valid, String message, String customer,
                               LocalDate expires, long daysRemaining) {
            this.valid = valid;
            this.message = message;
            this.customer = customer;
            this.expires = expires;
            this.daysRemaining = daysRemaining;
        }
    }

    // ===== 使用示例 =====
    public static void main(String[] args) {
        LicenseValidator validator = new LicenseValidator();
        ValidationResult result = validator.validate();
        if (result.valid) {
            System.out.printf("✓ 授权有效 — 客户: %s, 到期: %s (剩余 %d 天)%n",
                result.customer, result.expires, result.daysRemaining);
        } else {
            System.out.println("✗ 授权无效 — " + result.message);
        }
    }
}</pre>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-card class="section-card">
      <template #header><h3>定期校验策略</h3></template>
      <el-table :data="strategyData" border stripe>
        <el-table-column prop="timing" label="校验时机" width="180" />
        <el-table-column prop="action" label="行为" />
        <el-table-column prop="expired" label="过期后行为" />
      </el-table>
    </el-card>

    <el-card class="section-card">
      <template #header><h3>常见问题</h3></template>
      <el-collapse>
        <el-collapse-item title="Q: 下载的私钥为什么是加密的？" name="1">
          <p>私钥在服务器端使用 AES-256-CBC 加密存储。下载 ZIP 包中的 private_key.pem 已经过解密，可以直接使用。数据库中存储的是加密版本。</p>
        </el-collapse-item>
        <el-collapse-item title="Q: 证书到期后医院端软件会怎样？" name="2">
          <p>到期后软件仍可启动，但会在启动时弹窗提示续期。超过 2 年未续期，运行时还会随机弹出提醒（约 20% 概率），强烈建议在到期前完成续期。</p>
        </el-collapse-item>
        <el-collapse-item title="Q: 更换服务器后需要重新签发证书吗？" name="3">
          <p>不需要。只需将 <code>license/</code> 文件夹复制到新服务器即可，证书与硬件无关。</p>
        </el-collapse-item>
        <el-collapse-item title="Q: 证书可以同时用于多个医院吗？" name="4">
          <p>不可以。每份证书针对特定医院和软件产品签发，证书中包含医院名称（CN 字段）。多医院需分别申请。</p>
        </el-collapse-item>
        <el-collapse-item title="Q: 私钥泄露了怎么办？" name="5">
          <p>立即在 CRM 中吊销该证书，重新申请新的证书。吊销后旧证书的私钥将无法通过验证（如果医院端软件实现了 CRL/OCSP 在线校验）。</p>
        </el-collapse-item>
      </el-collapse>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const activeLang = ref('python')

const strategyData = [
  { timing: '软件启动时', action: '强制校验证书有效性和有效期', expired: '弹窗提示续期' },
  { timing: '软件运行中（每24小时）', action: '静默校验有效期', expired: '弹窗提示续期' },
  { timing: '过期超过2年', action: '运行时随机弹窗（~20%概率）', expired: '干扰性提醒' },
  { timing: '证书文件被删除/篡改', action: '校验失败，拒绝启动', expired: '-' },
]
</script>

<style scoped>
.guide-page {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.section-card {
  margin-bottom: 20px;
}

.section-card h3 {
  margin: 0;
}

.section-card p {
  line-height: 1.8;
  margin: 8px 0;
}

.section-card ul {
  padding-left: 20px;
}

.section-card li {
  line-height: 1.8;
}

.code-block {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 16px 20px;
  border-radius: 6px;
  overflow-x: auto;
  font-size: 13px;
  line-height: 1.6;
  max-height: 500px;
  white-space: pre;
  tab-size: 4;
}

code {
  background: #f0f0f0;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 13px;
}
</style>
