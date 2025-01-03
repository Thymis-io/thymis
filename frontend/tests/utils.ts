import { expect, type Locator, type Page } from '../playwright/fixtures';

export const highlightLocator = async (page: Page, locator: Locator) => {
	const boundingBox = await locator.boundingBox();
	if (!boundingBox) {
		return;
	}
	// add element with marginally bigger size
	const margin = 12;
	page.evaluate(`
		const div = document.createElement('div');
		div.className = 'playwright-highlight';
		div.style.position = 'absolute';
		div.style.border = '2px solid red';
		div.style.top = '${boundingBox.y - margin}px';
		div.style.left = '${boundingBox.x - margin}px';
		div.style.width = '${boundingBox.width + 2 * margin}px';
		div.style.height = '${boundingBox.height + 2 * margin}px';
		document.body.appendChild(div);
	`);
};

export const unhighlightAll = async (page: Page) => {
	// remove all elements with class 'playwright-highlight'
	page.evaluate(`
		const elements = document.querySelectorAll('.playwright-highlight');
		for (const element of elements) {
			element.remove();
		}
	`);
};

export const expectPageToHaveScreenshotWithHighlight = async (page: Page, locator: Locator) => {
	await highlightLocator(page, locator);
	await expect(page).toHaveScreenshot();
	await unhighlightAll(page);
};
