import { chromium } from 'playwright';

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext();
const page = await context.newPage();

const errors = [];
const networkFailures = [];
const wsMessages = [];

page.on('console', msg => {
  if (msg.type() === 'error') {
    errors.push(msg.text());
  }
});

page.on('requestfailed', request => {
  networkFailures.push(`${request.failure()?.errorText} - ${request.url()}`);
});

page.on('websocket', ws => {
  wsMessages.push({ event: 'opened', url: ws.url() });
  ws.on('framesent', frame => wsMessages.push({ event: 'sent', data: frame.payload }));
  ws.on('framereceived', frame => wsMessages.push({ event: 'received', data: frame.payload }));
  ws.on('closed', () => wsMessages.push({ event: 'closed' }));
});

async function runTest() {
  try {
    console.log('=== STEP 1: Homepage Load ===');
    await page.goto('http://localhost:3000', { timeout: 30000 });
    await page.waitForLoadState('networkidle');

    const title = await page.textContent('h1');
    console.log(`Title: ${title?.trim()}`);

    // Check for gradient logo
    const logo = await page.$('.bg-gradient-to-r');
    console.log(`Logo gradient found: ${!!logo}`);

    // Check feature grid
    const features = await page.$$('.grid-cols-1 > div');
    console.log(`Feature cards: ${features.length}`);

    console.log('\n=== STEP 2: Navigation to New Chat ===');
    await page.click('button:has-text("New Chat")');
    await page.waitForURL(/\/chat\/.+/, { timeout: 15000 });
    const sessionUrl = page.url();
    console.log(`Session URL: ${sessionUrl}`);

    const isNewSession = sessionUrl.includes('/chat/new');
    console.log(`Still /chat/new (not redirected): ${isNewSession}`);

    console.log('\n=== STEP 3: Wait for Session Creation ===');
    // Wait for actual session ID (not 'new')
    if (isNewSession) {
      await page.waitForFunction(() => !window.location.pathname.includes('/chat/new'), { timeout: 10000 });
      console.log(`Final URL: ${page.url()}`);
    }

    console.log('\n=== STEP 4: Chat Window State ===');
    // Wait for chat window to be ready
    await page.waitForSelector('text=Start a conversation', { timeout: 15000 });
    console.log('Empty state shown');

    // Check connection status
    const statusText = await page.textContent('text=/Connected|Connecting/');
    console.log(`Connection status: ${statusText?.trim()}`);

    console.log('\n=== STEP 5: Send Message ===');
    await page.fill('textarea', 'Hello AI, how are you?');
    await page.waitForTimeout(300);
    await page.keyboard.press('Enter');

    // Wait for user message to appear
    await page.waitForSelector('text=Hello AI, how are you?', { timeout: 10000 });
    console.log('User message appeared');

    console.log('\n=== STEP 6: Wait for AI Response ===');
    // Wait for streaming to start or response to appear
    await page.waitForTimeout(10000);

    // Check if there's any assistant response
    const assistantMessages = await page.$$('text=/I\'m|demo|Demo|Hello|Hi there/');
    console.log(`Potential AI responses: ${assistantMessages.length}`);

    console.log('\n=== STEP 7: Check for Errors ===');
    console.log('Console errors:');
    errors.forEach(e => console.log(`  - ${e.substring(0, 100)}`));

    console.log('\nNetwork failures:');
    networkFailures.slice(0, 5).forEach(e => console.log(`  - ${e.substring(0, 100)}`));

    console.log('\nWebSocket events:');
    wsMessages.slice(0, 10).forEach(e => console.log(`  - ${JSON.stringify(e).substring(0, 100)}`));

    console.log('\n=== STEP 8: Check UI Elements ===');
    const sidebar = await page.$('.w-72');
    console.log(`Sidebar present: ${!!sidebar}`);

    const messageArea = await page.$('text=Start a conversation');
    console.log(`Empty state present: ${!!messageArea}`);

    const inputBox = await page.$('textarea');
    console.log(`Input box present: ${!!inputBox}`);

    console.log('\n✅ Testing complete');

  } catch (error) {
    console.error('\n❌ Test failed:', error.message);

    console.log('\n=== Error Context ===');
    console.log('Console errors so far:');
    errors.forEach(e => console.log(`  - ${e.substring(0, 150)}`));

    console.log('\nNetwork failures:');
    networkFailures.forEach(e => console.log(`  - ${e.substring(0, 150)}`));

  } finally {
    await browser.close();
  }
}

runTest();