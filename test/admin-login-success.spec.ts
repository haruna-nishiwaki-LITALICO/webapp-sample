// spec: test/basic-operations-test-plan.md
// seed: test/seed.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Admin Login Success', () => {
  test('Admin Login Success', async ({ page }) => {
    // 1. Navigate to http://127.0.0.1:5000/login を実行（ログインページへ遷移）
    await page.goto('http://127.0.0.1:5000/login');

    // 2. Enter "admin" into the ユーザーID input を実行（管理者IDを入力）
    const userIdInput = page.getByTestId('input-user-id');
    await userIdInput.fill('admin');

    // 3. Enter "admin_password" into the パスワード input を実行（管理者パスワードを入力）
    const passwordInput = page.getByTestId('input-password');
    await passwordInput.fill('admin_password');

    // 4. Click the ログイン button を実行（ログインボタンを押下）
    await page.getByTestId('submit-login').click();

    // 確認1. Confirm flash message "ログインしました。" is visible を実行（ログイン成功メッセージを確認）
    await expect(page.getByText('ログインしました。')).toBeVisible();

    // 確認2. Confirm header shows "ログイン中: admin (admin)" を実行（ヘッダー表示を確認）
    await expect(page.getByText('ログイン中: admin (admin)')).toBeVisible();

    // 確認3. Confirm the ログアウト button is visible を実行（ログアウトボタンを確認）
    await expect(page.getByRole('button', { name: 'ログアウト' })).toBeVisible();

    // 確認4. Confirm current URL contains "/products" を実行（URLに/productsが含まれることを確認）
    await expect(page).toHaveURL(/\/products$/);
  });
});
