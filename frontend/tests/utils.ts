import {
	expect,
	type APIRequestContext,
	type Locator,
	type Page,
	type PageAssertionsToHaveScreenshotOptions,
	type TestInfo
} from '../playwright/fixtures';

export const colorSchemes = ['light', 'dark'] as const;

type MyHighlightOptions = {
	highlight?: boolean;
	screenshotHighlightedElement?: boolean;
	marginHighlight?: number;
	marginScreenshot?: number;
};

export const highlightLocator = async (
	screenshotTarget: Page | Locator,
	locator: Locator | Locator[],
	options: Partial<MyHighlightOptions> = {}
) => {
	const defaultOptions = {
		highlight: true,
		screenshotHighlightedElement: false,
		marginHighlight: 8,
		marginScreenshot: 32
	};
	const myOptions: MyHighlightOptions = { ...defaultOptions, ...options };

	let locators: Locator[] = [];
	if (Array.isArray(locator)) {
		locators = locator;
	} else {
		locators = [locator];
	}

	for (const locator of locators) {
		const boundingBox = await locator.boundingBox();
		if (!boundingBox) {
			console.warn(`Bounding box not found for locator: ${locator}`);
			return myOptions.screenshotHighlightedElement ? locator : screenshotTarget;
		}
		if (myOptions.marginScreenshot && !myOptions.screenshotHighlightedElement) {
			console.warn('marginScreenshot is only used when screenshotHighlightedElement is true');
		}
		if (
			myOptions.screenshotHighlightedElement &&
			myOptions.marginHighlight &&
			myOptions.marginScreenshot &&
			myOptions.marginHighlight > myOptions.marginScreenshot
		) {
			console.warn(
				'marginHighlight should be smaller than or equal to marginScreenshot, otherwise the screenshot will be cropped without the highlight'
			);
		}
		// add element with marginally bigger size
		const page = 'page' in screenshotTarget ? screenshotTarget.page() : screenshotTarget;
		if (myOptions.highlight) {
			page.evaluate(`
				const highlightDiv = document.createElement('div');
				highlightDiv.className = 'playwright-highlight';
				highlightDiv.style.position = 'absolute';
				highlightDiv.style.border = '2px solid red';
				highlightDiv.style.top = '${boundingBox.y - myOptions.marginHighlight!}px';
				highlightDiv.style.left = '${boundingBox.x - myOptions.marginHighlight!}px';
				highlightDiv.style.width = '${boundingBox.width + 2 * myOptions.marginHighlight!}px';
				highlightDiv.style.height = '${boundingBox.height + 2 * myOptions.marginHighlight!}px';
				highlightDiv.style.zIndex = '999999';
				document.body.appendChild(highlightDiv);
			`);
		}
		if (myOptions.screenshotHighlightedElement) {
			const myId = Math.random().toString(36).substring(7);
			// Make a new div with the same size as the bounding box, and take a screenshot of that
			await page.evaluate(`
				const screenshotDiv = document.createElement('div');
				screenshotDiv.id = '${myId}';
				screenshotDiv.className = 'playwright-highlight';
				screenshotDiv.style.position = 'absolute';
				screenshotDiv.style.top = '${boundingBox.y - myOptions.marginScreenshot!}px';
				screenshotDiv.style.left = '${boundingBox.x - myOptions.marginScreenshot!}px';
				screenshotDiv.style.width = '${boundingBox.width + 2 * myOptions.marginScreenshot!}px';
				screenshotDiv.style.height = '${boundingBox.height + 2 * myOptions.marginScreenshot!}px';
				screenshotDiv.style.zIndex = '999999';
				document.body.appendChild(screenshotDiv);
			`);

			return page.locator(`#${myId}`);
		}
	}

	if (myOptions.screenshotHighlightedElement) {
		return Array.isArray(locator) ? locator[0] : locator;
	} else {
		return screenshotTarget;
	}
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

export const expectScreenshot = async (
	screenshotTarget: Page | Locator,
	testInfo: TestInfo,
	counter: { count: number },
	options?: PageAssertionsToHaveScreenshotOptions
) => {
	counter.count++;
	const page = 'page' in screenshotTarget ? screenshotTarget.page() : screenshotTarget;

	// if options or options.mask is undefined, set it to an array with the default mask
	if (!options || options.mask === undefined) {
		options = { ...options, mask: [page.locator('.playwright-snapshot-unstable')] };
	}

	for (const colorScheme of colorSchemes) {
		await page.evaluate((scheme) => {
			document.documentElement.classList.toggle('dark', scheme === 'dark');
		}, colorScheme);

		await expect(page).toHaveScreenshot(
			`Color-scheme-${colorScheme}-${testInfo.title}-${counter.count}.png`,
			options
		);
	}
};

export const expectScreenshotWithHighlight = async (
	screenshotTarget: Page | Locator,
	highlightedElement: Locator | Locator[],
	testInfo: TestInfo,
	counter: { count: number },
	options?: PageAssertionsToHaveScreenshotOptions,
	highlightOptions?: MyHighlightOptions
) => {
	const toScreenshot = await highlightLocator(
		screenshotTarget,
		highlightedElement,
		highlightOptions
	);
	await expectScreenshot(toScreenshot, testInfo, counter, options);
	await unhighlightAll(screenshotTarget);
};

export const clearState = async (page: Page, request: APIRequestContext) => {
	await page.reload();
	await page.goto('/overview');
	const stateRequest = await page.request.get('/api/state');
	const state = await stateRequest.json();
	state['tags'] = [];
	state['devices'] = [];
	await page.request.patch('/api/state', { data: state });
	await page.evaluate(() => {
		if (window.toast) {
			window.toast.pop(0);
		}
	});
	await page.reload();
};

export const deleteAllTasks = async (page: Page, request: APIRequestContext) => {
	await page.goto('about:blank');
	const tasksRequest = await request.post(`/api/tasks/delete_all`);
	await tasksRequest.json();
	await page.goto('/overview');
};

export const createConfiguration = async (
	page: Page,
	name: string,
	deviceType: string,
	tags: string[]
) => {
	await page.locator('nav:visible').locator('a', { hasText: 'Configs' }).click();

	const addConfigurationButton = page
		.locator('button')
		.filter({ hasText: 'Create New Configuration' });
	await addConfigurationButton.click();

	const displayNameInput = page.locator('#display-name').first();
	await displayNameInput.fill(name);

	const deviceTypeSelect = page.locator('#device-type').first();
	await deviceTypeSelect.selectOption({ label: deviceType });

	if (tags.length > 0) {
		const tagsMultiSelect = page.locator('input[autocomplete]');
		await tagsMultiSelect.click();

		// for each tag, input and enter
		for (const tag of tags) {
			await page.getByRole('option', { name: tag }).click();
		}
	}

	await page.getByRole('heading', { name: 'Create a new device' }).click();

	const saveButton = page.locator('button').filter({ hasText: 'Create device configuration' });
	await saveButton.click();
};

export const createTag = async (page: Page, name: string) => {
	await page.locator('nav:visible').locator('a', { hasText: 'Config-Tags' }).click();

	const addTagButton = page.locator('button').filter({ hasText: 'Create Tag' });
	await addTagButton.click();

	const tagNameInput = page.locator('#display-name').first();
	await tagNameInput.fill(name);

	const saveButton = page.locator('button').filter({ hasText: 'Add tag' });
	await saveButton.click();
};

export const waitForTerminalText = async (page: Page, text: string) => {
	return await page.waitForFunction((text: string) => {
		// window.terminals[].buffer.active.getLine(0 up to .length-1).translateToString()
		window.terminals = window.terminals || [];
		let all_buffers = '';
		for (const terminal of window.terminals) {
			for (let i = 0; i < terminal.buffer.active.length; i++) {
				all_buffers += terminal.buffer.active.getLine(i).translateToString();
			}
		}
		return all_buffers.includes(text);
	}, text);
};

export const enterTextInTerminal = async (page: Page, text: string) => {
	const terminalElement = await page.$('.xterm-helper-textarea');
	await terminalElement?.focus();
	await page.keyboard.type(text);
	await page.keyboard.press('Enter');
};
