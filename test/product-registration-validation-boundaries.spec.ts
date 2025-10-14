// spec: test/basic-operations-test-plan.md
// seed: test/seed.spec.ts

import { expect, test } from '@playwright/test';

test.describe('Scenario 6: Product Registration Validation Boundaries', () => {
  test('Product Registration Validation Boundaries', async ({ page }) => {
    const userIdInput = page.getByTestId('input-user-id');
    const passwordInput = page.getByTestId('input-password');
    const loginButton = page.getByTestId('submit-login');
    const newProductLink = page.getByTestId('link-new-product');
    const flashItems = page.getByTestId('flash-messages').locator('li');
    const nameInput = page.getByTestId('input-name');
    const categorySelect = page.getByTestId('select-category');
    const priceInput = page.getByTestId('input-price');
    const stockInput = page.getByTestId('input-stock');
    const submitButton = page.getByTestId('submit-product');
    const nameError = page.getByTestId('error-name');
    const categoryError = page.getByTestId('error-category');
    const priceError = page.getByTestId('error-price');
    const stockError = page.getByTestId('error-stock');

    const overLengthName = 'A'.repeat(51);
    const validName = 'Valid Product';

    await page.addInitScript(() => {
      window.addEventListener('DOMContentLoaded', () => {
        const form = document.querySelector('[data-testid="product-form"]');
        if (form instanceof HTMLFormElement) {
          form.setAttribute('novalidate', '');
        }
      });
    });

    await page.goto('http://127.0.0.1:5000/login');
    await expect(page).toHaveURL('http://127.0.0.1:5000/login');
    await userIdInput.fill('admin');
    await passwordInput.fill('admin_password');
    await loginButton.click();
    await expect(page).toHaveURL('http://127.0.0.1:5000/products');
    await newProductLink.click();
    await expect(page).toHaveURL('http://127.0.0.1:5000/products/new');

    // Disable built-in constraint validation so the form submits and server-side errors surface.
    await page.getByTestId('product-form').evaluate((form: HTMLFormElement) => {
      form.setAttribute('novalidate', '');
    });

    // ステップ1: 「Attempt submission with all required fields blank.」の実施
    await submitButton.click();
    await expect(flashItems).toHaveText([
      'name: 商品名は必須です。',
      'category: カテゴリを選択してください。',
      'price: 必須入力です。',
      'stock: 必須入力です。',
    ]);
    await expect(nameError).toHaveText('商品名は必須です。');
    await expect(categoryError).toHaveText('カテゴリを選択してください。');
    await expect(priceError).toHaveText('必須入力です。');
    await expect(stockError).toHaveText('必須入力です。');

    // ステップ2: 「Enter 商品名 of 51 characters and submit.」の実施
    await nameInput.evaluate((element: HTMLInputElement) => {
      element.removeAttribute('maxlength');
      element.maxLength = 1000;
    });
    await nameInput.fill(overLengthName);
    await submitButton.click();
    await expect(flashItems).toHaveText([
      'name: 商品名は1文字以上50文字以下で入力してください。',
      'category: カテゴリを選択してください。',
      'price: 必須入力です。',
      'stock: 必須入力です。',
    ]);
    await expect(nameInput).toHaveValue(overLengthName);
    await expect(nameError).toHaveText('商品名は1文字以上50文字以下で入力してください。');
    await expect(categoryError).toHaveText('カテゴリを選択してください。');
    await expect(priceError).toHaveText('必須入力です。');
    await expect(stockError).toHaveText('必須入力です。');

    // ステップ3: 「Enter 価格 -1, then 1000001, submitting each time.」の実施
    await nameInput.fill(validName);
    await categorySelect.selectOption('その他');
    await stockInput.fill('10');
    await priceInput.fill('-1');
    await submitButton.click();
    await expect(flashItems).toHaveText(['price: 0以上1000000以下で入力してください。']);
    await expect(nameInput).toHaveValue(validName);
    await expect(categorySelect).toHaveValue('その他');
    await expect(stockInput).toHaveValue('10');
    await expect(priceInput).toHaveValue('-1');
    await expect(nameError).not.toBeVisible();
    await expect(categoryError).not.toBeVisible();
    await expect(stockError).not.toBeVisible();
    await expect(priceError).toHaveText('0以上1000000以下で入力してください。');

    await priceInput.fill('1000001');
    await submitButton.click();
    await expect(flashItems).toHaveText(['price: 0以上1000000以下で入力してください。']);
    await expect(priceInput).toHaveValue('1000001');
    await expect(priceError).toHaveText('0以上1000000以下で入力してください。');

    // ステップ4: 「Enter 在庫数 -1, then 1000, submitting each time.」の実施
    await priceInput.fill('1200');
    await stockInput.fill('-1');
    await submitButton.click();
    await expect(flashItems).toHaveText(['stock: 0以上999以下で入力してください。']);
    await expect(priceInput).toHaveValue('1200');
    await expect(stockInput).toHaveValue('-1');
    await expect(priceError).not.toBeVisible();
    await expect(stockError).toHaveText('0以上999以下で入力してください。');

    await stockInput.fill('1000');
    await submitButton.click();
    await expect(flashItems).toHaveText(['stock: 0以上999以下で入力してください。']);
    await expect(stockInput).toHaveValue('1000');
    await expect(stockError).toHaveText('0以上999以下で入力してください。');

    // ステップ5: 「Enter non-numeric characters in 価格 and 在庫数 and submit.」の実施
    await priceInput.evaluate((element: HTMLInputElement) => {
      element.setAttribute('type', 'text');
    });
    await stockInput.evaluate((element: HTMLInputElement) => {
      element.setAttribute('type', 'text');
    });
    await priceInput.fill('abc');
    await stockInput.fill('xyz');
    await submitButton.click();
    await expect(flashItems).toHaveText([
      'price: 数値を入力してください。',
      'stock: 数値を入力してください。',
    ]);
    await expect(nameInput).toHaveValue(validName);
    await expect(categorySelect).toHaveValue('その他');
    await expect(priceError).toHaveText('数値を入力してください。');
    await expect(stockError).toHaveText('数値を入力してください。');
  });
});
