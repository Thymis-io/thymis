import baseConfig from './playwright.config';

// Temporary config used only to capture fresh docs screenshots against an
// already-running dev-mode controller (avoids the RUNNING_IN_PLAYWRIGHT-forced
// production build path). Not part of the committed test suite.
export default {
	...baseConfig,
	webServer: {
		...(baseConfig.webServer as object),
		reuseExistingServer: true
	}
};
