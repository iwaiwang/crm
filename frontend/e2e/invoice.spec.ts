/**
 * 发票管理模块自动化测试
 * 测试发票的 CRUD 操作及购买方/销售方信息保存
 */
import { test, expect } from '@playwright/test';

// 测试数据
const TEST_INVOICE = {
  invoice_no: `测试发票-${Date.now()}`,
  total_amount: 1000.00,
  tax_rate: 13,
  type: 'special',
  issue_date: '2026-03-25',
  status: 'issued',
  buyer_name: '测试购买方科技有限公司',
  buyer_tax_id: '91110000123456789X',
  seller_name: '测试销售方有限公司',
  seller_tax_id: '91310000987654321Y',
  remark: '自动化测试发票',
};

test.describe('发票管理', () => {
  // 登录并获取 token
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    // 等待登录页面加载
    await page.waitForSelector('input[type="text"]', { timeout: 10000 });

    // 使用测试账号登录
    await page.fill('input[type="text"]', 'admin');
    await page.fill('input[type="password"]', 'admin123');
    // 登录按钮使用 text 选择器
    await page.click('button:has-text("登 录")');

    // 等待登录成功并跳转到首页
    await page.waitForURL(/\/dashboard/, { timeout: 30000 });
  });

  test('should display invoice list page', async ({ page }) => {
    // 导航到发票管理页面
    await page.goto('/invoices');

    // 验证页面标题
    await expect(page.locator('h2')).toContainText('发票管理');

    // 验证新增发票按钮存在
    await expect(page.getByRole('button', { name: /新增发票/ })).toBeVisible();

    // 验证表格存在
    await expect(page.locator('.el-table')).toBeVisible();
  });

  test('should create invoice with buyer and seller info', async ({ page }) => {
    const uniqueInvoiceNo = `AUTO-${Date.now()}`;

    await page.goto('/invoices');

    // 点击新增发票按钮
    await page.click('button:has-text("新增发票")');

    // 等待对话框打开
    await page.waitForSelector('.el-dialog', { timeout: 5000 });
    await page.waitForTimeout(1500);

    // 填写基本信息
    await page.locator('.el-dialog .el-form-item:has-text("发票号码") input').fill(uniqueInvoiceNo);
    await page.locator('.el-dialog .el-form-item:has-text("含税金额") input').fill('1000');

    // 选择税率 - 点击 placeholder 打开下拉框
    await page.locator('.el-dialog .el-form-item:has-text("税率") .el-select__placeholder').click();
    await page.getByRole('option', { name: '13%' }).click();

    // 选择发票类型
    await page.locator('.el-dialog .el-radio:has-text("专票")').click();

    // 选择开票日期
    await page.locator('.el-dialog .el-form-item:has-text("开票日期") input').fill('2026-03-25');

    // 填写购买方信息
    await page.locator('.el-dialog .el-form-item:has-text("购买方") input').first().fill(TEST_INVOICE.buyer_name);
    await page.locator('.el-dialog .el-form-item:has-text("购买方税号") input').fill(TEST_INVOICE.buyer_tax_id);

    // 填写销售方信息
    await page.locator('.el-dialog .el-form-item:has-text("销售方") input').first().fill(TEST_INVOICE.seller_name);
    await page.locator('.el-dialog .el-form-item:has-text("销售方税号") input').fill(TEST_INVOICE.seller_tax_id);

    // 填写备注
    await page.locator('.el-dialog .el-form-item:has-text("备注") textarea').fill(TEST_INVOICE.remark);

    // 点击保存
    await page.locator('.el-dialog .el-button--primary, .el-dialog .el-button:has-text("保存")').click();

    // 等待保存成功提示
    await page.waitForSelector('.el-message--success', { timeout: 5000 });
    const successMsg = await page.locator('.el-message--success').textContent();
    expect(successMsg.includes('创建成功') || successMsg.includes('更新成功')).toBe(true);

    // 关闭对话框
    await page.waitForTimeout(2000);

    // 验证发票列表中显示新发票
    await expect(page.locator('.el-table')).toContainText(uniqueInvoiceNo);
  });

  test('should show buyer and seller info when editing invoice', async ({ page }) => {
    const uniqueInvoiceNo = `EDIT-${Date.now()}`;

    // 第一步：创建发票
    await page.goto('/invoices');
    await page.click('button:has-text("新增发票")');
    await page.waitForSelector('.el-dialog', { timeout: 5000 });
    await page.waitForTimeout(1500);

    // 填写发票信息（包含购买方和销售方）
    await page.locator('.el-dialog .el-form-item:has-text("发票号码") input').fill(uniqueInvoiceNo);
    await page.locator('.el-dialog .el-form-item:has-text("含税金额") input').fill('2000');
    await page.locator('.el-dialog .el-form-item:has-text("购买方") input').first().fill('购买方测试公司');
    await page.locator('.el-dialog .el-form-item:has-text("购买方税号") input').fill('111111111111111111');
    await page.locator('.el-dialog .el-form-item:has-text("销售方") input').first().fill('销售方测试公司');
    await page.locator('.el-dialog .el-form-item:has-text("销售方税号") input').fill('222222222222222222');
    await page.locator('.el-dialog .el-form-item:has-text("备注") textarea').fill('测试备注');

    // 选择税率
    await page.locator('.el-dialog .el-form-item:has-text("税率") .el-select__placeholder').click();
    await page.getByRole('option', { name: '6%' }).click();

    // 选择发票类型
    await page.locator('.el-dialog .el-radio:has-text("普票")').click();

    // 选择开票日期
    await page.locator('.el-dialog .el-form-item:has-text("开票日期") input').fill('2026-03-20');

    // 保存
    await page.locator('.el-dialog .el-button--primary, .el-dialog .el-button:has-text("保存")').click();
    await page.waitForSelector('.el-message--success', { timeout: 5000 });
    await page.waitForTimeout(2000);

    // 第二步：刷新页面后编辑
    await page.reload({ waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    // 点击编辑按钮
    await page.click('.el-table .el-button:has-text("编辑")');
    await page.waitForSelector('.el-dialog', { timeout: 5000 });
    await page.waitForTimeout(1500);

    // 第三步：验证购买方/销售方信息是否正确显示
    const buyerNameValue = await page.locator('.el-dialog .el-form-item:has-text("购买方") input').first().inputValue();
    const buyerTaxIdValue = await page.locator('.el-dialog .el-form-item:has-text("购买方税号") input').inputValue();
    const sellerNameValue = await page.locator('.el-dialog .el-form-item:has-text("销售方") input').first().inputValue();
    const sellerTaxIdValue = await page.locator('.el-dialog .el-form-item:has-text("销售方税号") input').inputValue();

    console.log('购买方名称:', buyerNameValue);
    console.log('购买方税号:', buyerTaxIdValue);
    console.log('销售方名称:', sellerNameValue);
    console.log('销售方税号:', sellerTaxIdValue);

    // 断言购买方信息
    expect(buyerNameValue).toBe('购买方测试公司');
    expect(buyerTaxIdValue).toBe('111111111111111111');

    // 断言销售方信息
    expect(sellerNameValue).toBe('销售方测试公司');
    expect(sellerTaxIdValue).toBe('222222222222222222');

    // 取消编辑
    await page.click('.el-dialog .el-button:has-text("取消")');
  });

  test('should update invoice and persist buyer/seller info', async ({ page }) => {
    const uniqueInvoiceNo = `UPDATE-${Date.now()}`;

    // 创建发票
    await page.goto('/invoices');
    await page.click('button:has-text("新增发票")');
    await page.waitForSelector('.el-dialog', { timeout: 5000 });
    await page.waitForTimeout(1500);

    await page.locator('.el-dialog .el-form-item:has-text("发票号码") input').fill(uniqueInvoiceNo);
    await page.locator('.el-dialog .el-form-item:has-text("含税金额") input').fill('3000');
    await page.locator('.el-dialog .el-form-item:has-text("购买方") input').first().fill('原始购买方');
    await page.locator('.el-dialog .el-form-item:has-text("购买方税号") input').fill('333333333333333333');
    await page.locator('.el-dialog .el-form-item:has-text("销售方") input').first().fill('原始销售方');
    await page.locator('.el-dialog .el-form-item:has-text("销售方税号") input').fill('444444444444444444');

    // 选择税率
    await page.locator('.el-dialog .el-form-item:has-text("税率") .el-select__placeholder').click();
    await page.getByRole('option', { name: '13%' }).click();

    // 选择类型
    await page.locator('.el-dialog .el-radio:has-text("专票")').click();

    // 选择开票日期
    await page.locator('.el-dialog .el-form-item:has-text("开票日期") input').fill('2026-03-22');

    // 保存
    await page.locator('.el-dialog .el-button--primary, .el-dialog .el-button:has-text("保存")').click();
    await page.waitForSelector('.el-message--success', { timeout: 5000 });
    await page.waitForTimeout(2000);

    // 刷新后编辑并修改信息
    await page.reload({ waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    await page.click('.el-table .el-button:has-text("编辑")');
    await page.waitForSelector('.el-dialog', { timeout: 5000 });
    await page.waitForTimeout(1500);

    // 修改购买方和销售方信息
    await page.locator('.el-dialog .el-form-item:has-text("购买方") input').first().fill('更新后的购买方');
    await page.locator('.el-dialog .el-form-item:has-text("销售方") input').first().fill('更新后的销售方');

    // 保存修改
    await page.locator('.el-dialog .el-button--primary, .el-dialog .el-button:has-text("保存")').click();
    await page.waitForSelector('.el-message--success', { timeout: 5000 });
    await page.waitForTimeout(2000);

    // 再次刷新并编辑验证
    await page.reload({ waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    await page.click('.el-table .el-button:has-text("编辑")');
    await page.waitForSelector('.el-dialog', { timeout: 5000 });
    await page.waitForTimeout(1500);

    // 验证更新后的值
    const updatedBuyerName = await page.locator('.el-dialog .el-form-item:has-text("购买方") input').first().inputValue();
    const updatedSellerName = await page.locator('.el-dialog .el-form-item:has-text("销售方") input').first().inputValue();

    expect(updatedBuyerName).toBe('更新后的购买方');
    expect(updatedSellerName).toBe('更新后的销售方');
  });

  test('should delete invoice', async ({ page }) => {
    const uniqueInvoiceNo = `DELETE-${Date.now()}`;

    // 创建临时发票用于删除测试
    await page.goto('/invoices');
    await page.click('button:has-text("新增发票")');
    await page.waitForSelector('.el-dialog', { timeout: 5000 });
    await page.waitForTimeout(1500);

    await page.locator('.el-dialog .el-form-item:has-text("发票号码") input').fill(uniqueInvoiceNo);
    await page.locator('.el-dialog .el-form-item:has-text("含税金额") input').fill('100');

    // 选择税率
    await page.locator('.el-dialog .el-form-item:has-text("税率") .el-select__placeholder').click();
    await page.getByRole('option', { name: '1%', exact: true }).click();

    // 选择类型
    await page.locator('.el-dialog .el-radio:has-text("普票")').click();

    // 选择开票日期
    await page.locator('.el-dialog .el-form-item:has-text("开票日期") input').fill('2026-03-25');

    // 保存
    await page.locator('.el-dialog .el-button--primary, .el-dialog .el-button:has-text("保存")').click();
    await page.waitForSelector('.el-message--success', { timeout: 5000 });
    await page.waitForTimeout(2000);

    // 删除刚创建的发票
    await page.click('.el-table .el-button:has-text("删除")');

    // 等待确认对话框并确认
    await page.waitForSelector('.el-message-box', { timeout: 5000 });
    await page.waitForTimeout(500);
    await page.locator('.el-message-box .el-button--primary, .el-message-box .el-button:has-text("确定")').click();

    // 等待删除成功提示 - 使用 last() 获取最新的消息
    await page.waitForSelector('.el-message--success', { timeout: 5000 });
    await page.waitForTimeout(1000);
    const deleteMsg = await page.locator('.el-message--success').last().textContent();
    expect(deleteMsg.includes('删除成功')).toBe(true);
  });
});
