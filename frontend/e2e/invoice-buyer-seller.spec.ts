/**
 * 购买方/销售方信息保存测试
 * 专项测试：验证发票保存后，编辑时购买方/销售方信息是否正确显示
 *
 * 运行方式：
 *   npx playwright test e2e/invoice-buyer-seller.spec.ts --debug
 */
import { test, expect } from '@playwright/test';

test.describe('发票购买方/销售方信息保存 Bug 修复验证', () => {
  test('Bug 修复验证：保存后编辑应显示购买方和销售方信息', async ({ page }) => {
    const timestamp = Date.now();
    const invoiceNo = `BUGFIX-${timestamp}`;

    console.log(`\n=== 开始测试：发票 ${invoiceNo} ===`);
    console.log('步骤 1: 登录系统');

    // 登录
    await page.goto('/');
    await page.waitForSelector('input[type="text"]', { timeout: 10000 });
    await page.fill('input[type="text"]', 'admin');
    await page.fill('input[type="password"]', 'admin123');
    await page.click('button:has-text("登 录")');
    await page.waitForURL(/\/dashboard/, { timeout: 30000 });
    console.log('✓ 登录成功');

    // 导航到发票页面
    console.log('\n步骤 2: 导航到发票管理页面');
    await page.goto('/invoices');
    await expect(page.locator('h2')).toContainText('发票管理');
    console.log('✓ 发票管理页面已加载');

    // 创建发票
    console.log('\n步骤 3: 创建新发票（包含购买方/销售方信息）');
    await page.click('button:has-text("新增发票")');
    await page.waitForSelector('.el-dialog', { timeout: 5000 });
    // 等待对话框完全打开
    await page.waitForTimeout(1500);

    // 填写基本信息 - 使用 label 定位
    await page.getByLabel('发票号码').fill(invoiceNo);
    await page.getByLabel('含税金额').fill('1000');

    // 选择税率 - 点击 placeholder 打开下拉框
    await page.locator('.el-dialog .el-form-item:has-text("税率") .el-select__placeholder').click();
    await page.getByRole('option', { name: '13%' }).click();

    // 选择类型 - 点击 label
    await page.locator('.el-dialog .el-radio:has-text("专票")').click();

    // 选择日期
    await page.getByLabel('开票日期').fill('2026-03-25');

    // 填写购买方信息（这是 Bug 的关键字段）
    const buyerName = '测试购买方科技有限公司';
    const buyerTaxId = '91110000123456789X';
    await page.locator('.el-dialog .el-form-item:has-text("购买方") input').first().fill(buyerName);
    await page.locator('.el-dialog .el-form-item:has-text("购买方税号") input').fill(buyerTaxId);
    console.log(`  - 购买方：${buyerName}`);
    console.log(`  - 购买方税号：${buyerTaxId}`);

    // 填写销售方信息（这是 Bug 的关键字段）
    const sellerName = '测试销售方有限公司';
    const sellerTaxId = '91310000987654321Y';
    await page.locator('.el-dialog .el-form-item:has-text("销售方") input').first().fill(sellerName);
    await page.locator('.el-dialog .el-form-item:has-text("销售方税号") input').fill(sellerTaxId);
    console.log(`  - 销售方：${sellerName}`);
    console.log(`  - 销售方税号：${sellerTaxId}`);

    // 保存 - 使用更通用的选择器
    console.log('\n步骤 4: 保存发票');
    await page.locator('.el-dialog .el-button--primary, .el-dialog .el-button:has-text("保存")').click();

    // 等待保存成功
    await page.waitForSelector('.el-message--success', { timeout: 10000 });
    const successMessage = await page.locator('.el-message--success').textContent();
    console.log(`✓ 保存成功：${successMessage}`);

    // 等待对话框关闭
    await page.waitForTimeout(2000);
    // 如果对话框还在，尝试点击确认按钮关闭
    if (await page.locator('.el-dialog').isVisible()) {
      await page.waitForTimeout(3000);
    }

    // 刷新页面
    console.log('\n步骤 5: 刷新页面后编辑发票');
    await page.reload({ waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    console.log('✓ 页面已刷新');

    // 点击编辑
    console.log('\n步骤 6: 点击编辑按钮');
    const editButtons = await page.locator('.el-table .el-button:has-text("编辑")').all();

    // 找到刚创建的发票的编辑按钮
    let targetEditBtn = null;
    for (const btn of editButtons) {
      const row = btn.locator('..');
      const rowText = await row.innerText();
      if (rowText.includes(invoiceNo)) {
        targetEditBtn = btn;
        break;
      }
    }

    if (!targetEditBtn) {
      // 如果没有找到，点击第一个编辑按钮
      targetEditBtn = await page.locator('.el-table .el-button:has-text("编辑")').first();
    }

    await targetEditBtn.click();
    await page.waitForSelector('.el-dialog', { timeout: 5000 });
    console.log('✓ 编辑对话框已打开');

    // 验证购买方信息
    console.log('\n步骤 7: 验证购买方/销售方信息是否正确显示');

    const actualBuyerName = await page.locator('.el-dialog .el-form-item:has-text("购买方") input').first().inputValue();
    const actualBuyerTaxId = await page.locator('.el-dialog .el-form-item:has-text("购买方税号") input').inputValue();
    const actualSellerName = await page.locator('.el-dialog .el-form-item:has-text("销售方") input').first().inputValue();
    const actualSellerTaxId = await page.locator('.el-dialog .el-form-item:has-text("销售方税号") input').inputValue();

    console.log(`  购买方名称：期望="${buyerName}", 实际="${actualBuyerName}"`);
    console.log(`  购买方税号：期望="${buyerTaxId}", 实际="${actualBuyerTaxId}"`);
    console.log(`  销售方名称：期望="${sellerName}", 实际="${actualSellerName}"`);
    console.log(`  销售方税号：期望="${sellerTaxId}", 实际="${actualSellerTaxId}"`);

    // 断言
    expect(actualBuyerName).toBe(buyerName);
    expect(actualBuyerTaxId).toBe(buyerTaxId);
    expect(actualSellerName).toBe(sellerName);
    expect(actualSellerTaxId).toBe(sellerTaxId);

    console.log('\n✓ 所有字段验证通过！Bug 已修复！');

    // 取消编辑 - 使用更通用的选择器
    await page.locator('.el-dialog .el-button:has-text("取消")').click();
    await page.waitForTimeout(2000);

    console.log(`\n=== 测试完成：发票 ${invoiceNo} ===`);
  });
});
