import {
	expect,
	type APIRequestContext,
	type Locator,
	type Page,
	type PageAssertionsToHaveScreenshotOptions
} from '../playwright/fixtures';

export const highlightLocator = async (screenshotTarget: Page | Locator, locator: Locator) => {
	const boundingBox = await locator.boundingBox();
	if (!boundingBox) {
		console.warn(`Bounding box not found for locator: ${locator}`);
		return;
	}
	// add element with marginally bigger size
	const margin = 8;
	const page = 'page' in screenshotTarget ? screenshotTarget.page() : screenshotTarget;
	page.evaluate(`
		const div = document.createElement('div');
		div.className = 'playwright-highlight';
		div.style.position = 'absolute';
		div.style.border = '2px solid red';
		div.style.top = '${boundingBox.y - margin}px';
		div.style.left = '${boundingBox.x - margin}px';
		div.style.width = '${boundingBox.width + 2 * margin}px';
		div.style.height = '${boundingBox.height + 2 * margin}px';
		div.style.zIndex = '999999';
		document.body.appendChild(div);
	`);
};

export const unhighlightAll = async (screenshotTarget: Page | Locator) => {
	// remove all elements with class 'playwright-highlight'
	const page = 'page' in screenshotTarget ? screenshotTarget.page() : screenshotTarget;
	await page.evaluate(`
		const elements = document.querySelectorAll('.playwright-highlight');
		for (const element of elements) {
			element.remove();
		}
	`);
};

export const expectToHaveScreenshotWithHighlight = async (
	screenshotTarget: Page | Locator,
	highlightedElement: Locator,
	options?: PageAssertionsToHaveScreenshotOptions
) => {
	await highlightLocator(screenshotTarget, highlightedElement);
	await expect(screenshotTarget).toHaveScreenshot(options);
	await unhighlightAll(screenshotTarget);
};

export const clearState = async (page: Page, request: APIRequestContext) => {
	await page.goto('http://localhost:8000/overview');
	const stateRequest = await request.get('/api/state');
	const state = await stateRequest.json();
	state['tags'] = [];
	state['devices'] = [];
	await request.patch('/api/state', { data: state });
};

export const deleteAllTasks = async (page: Page, request: APIRequestContext) => {
	const tasksRequest = await request.post('/api/tasks/delete_all');
	await tasksRequest.json();
	await page.reload();
};
