const { chromium } = require("playwright");

const SONAR_URL = process.env.SONAR_URL || "http://localhost:9000";
const ADMIN_USER = process.env.SONAR_ADMIN_USER || "admin";
const ADMIN_PWD = process.env.SONAR_ADMIN_OLD_PWD || "admin";
const ADMIN_PASS = process.env.SONAR_ADMIN_PASS || "P@ssw0rd$123";



(async () => {
  try {
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();

    await page.goto(SONAR_URL);
    await page.fill('input[name="login"]', ADMIN_USER);
    await page.fill('input[name="password"]', ADMIN_PWD);
    await page.click('button[type="submit"]');

    try {
      await page.waitForURL(`${SONAR_URL}/account/reset_password`, {
        waitUntil: "networkidle",
        timeout: 30000,
      });
      console.log("No Reset Password page detected.");
    } catch (e) {
      if (page.url().startsWith(`${SONAR_URL}/`)) {
        await page.fill('input[name="login"]', ADMIN_USER);
        await page.fill('input[name="password"]', ADMIN_PASS);
        await page.click('button[type="submit"]');
        await page.waitForURL("**", { waitUntil: "networkidle" });
        console.log("Logged in using new password.");
      }
    }

    if (page.url().includes("/account/reset_password")) {
      console.log("Password change page detected");
      await page.waitForSelector('input[name="old_password"]', {
        timeout: 30000,
      });
      await page.fill('input[name="old_password"]', ADMIN_PWD);
      await page.fill('input[id="create-password"]', ADMIN_PASS);
      await page.fill('input[id="confirm-password"]', ADMIN_PASS);
      await page.click('button[type="submit"]');
      await page.waitForURL("**", { waitUntil: "networkidle" });

      console.log("Password changed and logged in with new password.");
    }

    await browser.close();
  } catch (e) {
    console.error(e);
    console.log("SonarQube is not ready yet. Exiting.");
    process.exit(1);
  }
})();
