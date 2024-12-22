import { devices, type PlaywrightTestConfig } from '@playwright/test';

// if env THYMIS_DEV_SHELL is set, use poetry run uvicorn reload stuff, else use nix run

let command = `nix run .#thymis-controller`;

if (process.env.THYMIS_DEV_SHELL) {
	console.log('Using poetry run uvicorn reload');
	command = `cd ../controller && poetry run uvicorn thymis_controller.main:app --reload`;
}

const commandFrame = (cmd) =>
	`sh -c 'set -e; TMPFILE=$(mktemp) && echo "testadminpassword" > $TMPFILE && export THYMIS_AUTH_BASIC_PASSWORD_FILE=$TMPFILE && ${cmd}; rm -f $TMPFILE'`;

const config: PlaywrightTestConfig = {
	webServer: {
		command: commandFrame(command),
		port: 8000
	},
	testDir: 'tests',
	testMatch: /(.+\.)?(test|spec)\.[jt]s/,
	...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH
		? {
				use: {
					launchOptions: {
						executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH as string
					},
					...devices['Desktop Chrome']
				}
			}
		: {})
};

export default config;
