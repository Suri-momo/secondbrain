import { test, expect } from '@playwright/test';

test('has title', async ({ page }) => {
  await page.goto('/');

  // Expect a title to contain "Next.js"
  await expect(page).toHaveTitle(/Next.js/);
});

test('navigate to root', async ({ page }) => {
  await page.goto('/');

  // Expect the page to have a heading
  const heading = page.locator('h1, h2, h3').first();
  await expect(heading).toBeVisible();
});
