// Declarative registry of pages for the structure-conformance suite.
// Each entry describes which shared-structure invariants a page must satisfy.
// Adding a new page = adding one entry here.

export type ListPageSpec = {
	family: 'list';
	name: string;
	/** URL to load the list page directly. */
	path: string;
	/**
	 * When set, the first link in the row containing `rowText` is a name link
	 * that must navigate to a URL matching `urlPattern` (detail/edit page).
	 */
	nameLink?: { rowText: string; urlPattern: RegExp };
};

export type DetailPageSpec = {
	family: 'detail';
	name: string;
	/** How to reach the detail page: open the seeded entity from this list page. */
	from: { listPath: string; rowText: string };
	/** Expected detail URL after opening the entity. */
	urlPattern: RegExp;
	/**
	 * Tab labels that must be present, in this order. Extra conditional tabs
	 * (e.g. VNC, Logs) are allowed and ignored — we only assert the core set.
	 */
	expectedTabs: string[];
	/** Primary action button label expected in the PageHead. */
	expectedAction: string;
};

// Seed data created once before the suite runs.
export const SEED = {
	configName: 'Conformance Config',
	configId: 'conformance-config',
	tagName: 'Conformance Tag',
	deviceHost: '127.0.0.50'
};

export const listPages: ListPageSpec[] = [
	{
		family: 'list',
		name: 'Configs',
		path: '/configuration/list',
		nameLink: { rowText: SEED.configName, urlPattern: /\/configuration\/configuration-details/ }
	},
	{
		family: 'list',
		name: 'Config-Tags',
		path: '/tags',
		nameLink: { rowText: SEED.tagName, urlPattern: /\/configuration\/edit/ }
	},
	{
		family: 'list',
		name: 'Devices',
		path: '/devices',
		nameLink: { rowText: SEED.configName, urlPattern: /\/devices\/.+\/details/ }
	},
	{ family: 'list', name: 'Secrets', path: '/secrets' },
	{ family: 'list', name: 'External Repositories', path: '/external-repositories' },
	{ family: 'list', name: 'Tasks', path: '/tasks' },
	{ family: 'list', name: 'Artifacts', path: '/artifacts' }
];

export const detailPages: DetailPageSpec[] = [
	{
		family: 'detail',
		name: 'Configuration detail',
		from: { listPath: '/configuration/list', rowText: SEED.configName },
		urlPattern: /\/configuration\/configuration-details/,
		expectedTabs: ['Details', 'Configure', 'Terminal'],
		expectedAction: 'Download Device Image'
	},
	{
		family: 'detail',
		name: 'Device detail',
		from: { listPath: '/devices', rowText: SEED.configName },
		urlPattern: /\/devices\/.+\/details/,
		expectedTabs: ['Details', 'Terminal', 'Logs'],
		expectedAction: 'Restart'
	}
];
