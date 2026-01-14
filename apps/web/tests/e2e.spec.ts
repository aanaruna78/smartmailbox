import { test, expect } from '@playwright/test';

test('has title and login prompt', async ({ page }) => {
    await page.goto('/login');

    // Expect a title "to contain" a substring.
    // The default title might be 'Smart Mailbox' or similar
    await expect(page).toHaveTitle(/Smart Mailbox/);

    // Check for the "Welcome Back" heading
    const heading = page.getByRole('heading', { name: /Welcome Back/i });
    await expect(heading).toBeVisible();

    // Check for some sign-in text
    await expect(page.getByText(/Sign in to access your smart mailbox dashboard/i)).toBeVisible();
});

test('redirects to login when unauthenticated', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveURL(/\/login/);
});
