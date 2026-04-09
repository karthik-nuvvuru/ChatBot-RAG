import { chromium } from 'playwright';

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext();
const page = await context.newPage();

const errors = [];

page.on('console', msg => {
  if (msg.type() === 'error') {
    errors.push(msg.text());
  }
});

async function runTest() {
  try {
    console.log('=== STEP 1: Homepage ===');
    await page.goto('http://localhost:3000', { timeout: 30000 });
    await page.waitForLoadState('networkidle');
    console.log(`Title: ${await page.textContent('h1')}`);

    console.log('\n=== STEP 2: New Chat ===');
    await page.click('button:has-text("New Chat")');
    await page.waitForURL(/\/chat\/.+/, { timeout: 15000 });
    console.log(`URL: ${page.url().split('/').pop()}`);

    console.log('\n=== STEP 3: Chat Window ===');
    await page.waitForSelector('text=Start a conversation', { timeout: 15000 });
    console.log('Empty state shown');
    const status = await page.textContent('p:has-text("Connected"), p:has-text("Connecting")');
    console.log(`Status: ${status?.trim()}`);

    console.log('\n=== STEP 4: Send Message ===');
    await page.fill('textarea', 'Hello AI!');
    await page.waitForTimeout(300);
    await page.keyboard.press('Enter');

    console.log('\n=== STEP 5: Wait for Response ===');
    // Wait for user message
    await page.waitForSelector('text=Hello AI!', { timeout: 5000 });
    console.log('User message shown');

    // Wait for streaming to complete
    await page.waitForTimeout(8000);

    // Check for assistant response
    const messages = await page.$$eval('.bg-gray-800\\/50, [class*="assistant"]', els => els.map(e => e.textContent?.trim()).filter(t => t && t.length > 0));
    console.log(`Potential AI messages: ${messages.length}`);
    if (messages.length > 0) {
      console.log(`First message: ${messages[0]?.substring(0, 100)}`);
    }

    console.log('\n=== STEP 6: Error Summary ===');
    const criticalErrors = errors.filter(e =>
      !e.includes('favicon') &&
      !e.includes('404') &&
      !e.includes('WebSocket') &&
      !e.includes('ERR_ABORTED')
    );
    console.log(`Critical errors: ${criticalErrors.length}`);
    criticalErrors.forEach(e => console.log(`  - ${e.substring(0, 80)}`));

    console.log('\n✅ TEST COMPLETE');

  } catch (error) {
    console.error('\n❌ Test failed:', error.message);
  } finally {
    await browser.close();
  }
}

runTest();