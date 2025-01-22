import { devices, type PlaywrightTestConfig } from '@playwright/test';

// if env THYMIS_DEV_SHELL is set, use poetry run uvicorn reload stuff, else use nix run

let command = `nix run .#thymis-controller`;

if (process.env.THYMIS_DEV_SHELL) {
	console.log('Using poetry run uvicorn reload');
	command = `cd ../controller && poetry run uvicorn thymis_controller.main:app --reload`;
}

const runInShell = (cmd) => `sh -c '${cmd}'`;

const withErrorHandling = (cmd) => `set -e; ( ${cmd} )`;

const withTempPathVar = (cmd) => `TMPDIR=$(mktemp -d) && ( ${cmd} ) && rm -rf $TMPDIR`;

const withEnv = (env: Record<string, string>, cmd: string) =>
	`export ${Object.entries(env)
		.map(([key, value]) => `${key}=${value}`)
		.join(' && export ')} && ${cmd}`;

const withContentInFile = (content: string, file: string, cmd: string) =>
	`echo '${content}' > ${file} && ${cmd}`;

const commandFrame = (cmd) =>
	runInShell(
		withErrorHandling(
			withTempPathVar(
				withEnv(
					{
						THYMIS_PROJECT_PATH: '$TMPDIR',
						THYMIS_AUTH_BASIC_PASSWORD_FILE: '$TMPDIR/auth-basic-password',
						RUNNING_IN_PLAYWRIGHT: 'true'
					},
					withContentInFile('testadminpassword', '$THYMIS_AUTH_BASIC_PASSWORD_FILE', cmd)
				)
			)
		)
	);

const config: PlaywrightTestConfig = {
	workers: 1, // serial execution, but not with interdependent tests, but only one application instance
	retries: 3,
	webServer: {
		command: commandFrame(command),
		port: 8000
	},
	testDir: 'tests',
	testMatch: /(.+\.)?(test|spec)\.[jt]s/,
	use: {
		...devices['Desktop Chrome'],
		viewport: {
			width: 1920,
			height: 1080
		},
		launchOptions: {
			args: ['--disable-lcd-text']
		},
		video: 'retain-on-failure',
		trace: 'retain-on-failure'
	},
	reporter: [['list'], ['html']],
	expect: {
		toHaveScreenshot: {
			maxDiffPixels: 1,
			threshold: 0.01
		}
	}
};

export default config;
