import { spawn } from 'child_process';
// const execFile =  util.promisify(execFileCallback);

const myExecFile = (file: string, args: string[]): Promise<{ stdout: string; stderr: string }> => {
	// call spawn
	return new Promise((resolve, reject) => {
		const child = spawn(file, args);
		let stdout = '';
		let stderr = '';
		child.stdout.on('data', (data) => {
			console.log(`stdout: ${data}`);
			stdout += data;
		});
		child.stderr.on('data', (data) => {
			console.log(`stderr: ${data}`);
			stderr += data;
		});
		child.on('error', (error) => {
			console.log(`error: ${error.message}`);
			reject(error);
		});
		child.on('close', (code) => {
			console.log(`child process exited with code ${code}`);
			resolve({ stdout, stderr });
		});
	});
};

export const getMyIp = async () => {
	// run `ip route get 1.2.3.4 | awk '{print $7}'` in bash
	const args = ['-c', "ip route get 1.2.3.4 | awk '{print $7}'"];
	const { stdout } = await myExecFile('bash', args);
	return stdout;
};
