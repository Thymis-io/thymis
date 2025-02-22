import {
	expect,
	type APIRequestContext,
	type Locator,
	type Page,
	type PageAssertionsToHaveScreenshotOptions
} from '../playwright/fixtures';

type MyHighlightOptions = {
	highlight: boolean;
	screenshotHighlightedElement: boolean;
	marginHighlight: number;
	marginScreenshot: number;
};

export const highlightLocator = async (
	screenshotTarget: Page | Locator,
	locator: Locator,
	options: Partial<MyHighlightOptions> = {}
) => {
	const defaultOptions = {
		highlight: true,
		screenshotHighlightedElement: false,
		marginHighlight: 8,
		marginScreenshot: 32
	};
	const myOptions: MyHighlightOptions = { ...defaultOptions, ...options };
	const boundingBox = await locator.boundingBox();
	if (!boundingBox) {
		console.warn(`Bounding box not found for locator: ${locator}`);
		return options.screenshotHighlightedElement ? locator : screenshotTarget;
	}
	if (options.marginScreenshot && !options.screenshotHighlightedElement) {
		console.warn('marginScreenshot is only used when screenshotHighlightedElement is true');
	}
	if (
		options.screenshotHighlightedElement &&
		options.marginHighlight &&
		options.marginScreenshot &&
		options.marginHighlight > options.marginScreenshot
	) {
		console.warn(
			'marginHighlight should be smaller than or equal to marginScreenshot, otherwise the screenshot will be cropped without the highlight'
		);
	}
	// add element with marginally bigger size
	const page = 'page' in screenshotTarget ? screenshotTarget.page() : screenshotTarget;
	if (options.highlight) {
		page.evaluate(`
		const highlightDiv = document.createElement('div');
		highlightDiv.className = 'playwright-highlight';
		highlightDiv.style.position = 'absolute';
		highlightDiv.style.border = '2px solid red';
		highlightDiv.style.top = '${boundingBox.y - myOptions.marginHighlight}px';
		highlightDiv.style.left = '${boundingBox.x - myOptions.marginHighlight}px';
		highlightDiv.style.width = '${boundingBox.width + 2 * myOptions.marginHighlight}px';
		highlightDiv.style.height = '${boundingBox.height + 2 * myOptions.marginHighlight}px';
		highlightDiv.style.zIndex = '999999';
		document.body.appendChild(highlightDiv);
	`);
	}
	if (options.screenshotHighlightedElement) {
		const myId = Math.random().toString(36).substring(7);
		// Make a new div with the same size as the bounding box, and take a screenshot of that
		await page.evaluate(
			`
		const screenshotDiv = document.createElement('div');
		screenshotDiv.id = '${myId}';
		screenshotDiv.className = 'playwright-highlight';
		screenshotDiv.style.position = 'absolute';
		screenshotDiv.style.top = '${boundingBox.y - myOptions.marginScreenshot}px';
		screenshotDiv.style.left = '${boundingBox.x - myOptions.marginScreenshot}px';
		screenshotDiv.style.width = '${boundingBox.width + 2 * myOptions.marginScreenshot}px';
		screenshotDiv.style.height = '${boundingBox.height + 2 * myOptions.marginScreenshot}px';
		screenshotDiv.style.zIndex = '999999';
		document.body.appendChild(screenshotDiv);
	`
		);

		return page.locator(`#${myId}`);
	}
	return options.screenshotHighlightedElement ? locator : screenshotTarget;
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
	options?: PageAssertionsToHaveScreenshotOptions,
	myOptions?: MyHighlightOptions
) => {
	const toScreenshot = await highlightLocator(screenshotTarget, highlightedElement, myOptions);
	await expect(toScreenshot).toHaveScreenshot(options);
	await unhighlightAll(screenshotTarget);
};

export const clearState = async (page: Page, request: APIRequestContext) => {
	await page.goto('http://localhost:8000/overview');
	const stateRequest = await page.request.get('/api/state');
	const state = await stateRequest.json();
	state['tags'] = [];
	state['devices'] = [];
	await page.request.patch('/api/state', { data: state });
};

export const deleteAllTasks = async (page: Page, request: APIRequestContext) => {
	const tasksRequest = await request.post('/api/tasks/delete_all');
	await tasksRequest.json();
	await page.reload();
};
