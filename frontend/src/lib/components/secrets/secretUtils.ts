import type { SecretProcessingType, SecretType } from '$lib/state';

export type SecretShort = {
	id: string;
	display_name: string;
	type: SecretType;
	value_str?: string;
	value_size: number;
	filename?: string;
	include_in_image: boolean;
	processing_type: SecretProcessingType;
	created_at: string;
	updated_at: string;
	delete_at?: string | null;
};

export type CreateSecretRequest = {
	display_name: string;
	type: SecretType;
	value_str?: string;
	value_b64?: string;
	filename?: string;
	include_in_image: boolean;
	processing_type: SecretProcessingType;
};

export type SecretEditState = {
	secretName: string;
	secretType: SecretType;
	singleLineValue: string | null;
	multiLineValue: string | undefined;
	fileValue: File | null;
	envVarList: [string, string][] | null;
	fileInfo: { name: string; size: number };
	includeInImage: boolean;
	processingType: SecretProcessingType;
};

export const stringToEnvVars = (str: string): [string, string][] => {
	if (!str || str.trim() === '') {
		return [['', '']]; // Default empty entry
	}

	return str
		.split('\n')
		.filter((line) => line.trim() !== '')
		.map((line) => {
			const separatorIndex = line.indexOf('=');
			if (separatorIndex === -1) {
				return [line.trim(), '']; // No value
			}
			const key = line.substring(0, separatorIndex).trim();
			const value = line.substring(separatorIndex + 1).trim();
			return [key, value];
		});
};

export const envVarsToString = (envVars: [string, string][]): string => {
	if (!envVars || envVars.length === 0) {
		return '';
	}

	return envVars
		.filter(([key]) => key.trim() !== '') // Only include entries with non-empty keys
		.map(([key, value]) => `${key}=${value}`)
		.join('\n');
};

export const arrayBufferToBase64 = (buffer: ArrayBuffer): string => {
	let binary = '';
	const bytes = new Uint8Array(buffer);
	const len = bytes.byteLength;
	for (let i = 0; i < len; i++) {
		binary += String.fromCharCode(bytes[i]);
	}
	return window.btoa(binary);
};

export const createSecretRequest = async (
	state: SecretEditState
): Promise<CreateSecretRequest | null> => {
	const {
		secretName,
		secretType,
		singleLineValue,
		multiLineValue,
		fileValue,
		envVarList,
		includeInImage,
		processingType
	} = state;

	let request: CreateSecretRequest | null = null;

	switch (secretType) {
		case 'single_line':
			request = {
				display_name: secretName,
				type: 'single_line',
				value_str: singleLineValue || '',
				include_in_image: includeInImage,
				processing_type: processingType
			};
			break;

		case 'multi_line':
			request = {
				display_name: secretName,
				type: 'multi_line',
				value_str: multiLineValue || '',
				include_in_image: includeInImage,
				processing_type: processingType
			};
			break;

		case 'env_list':
			request = {
				display_name: secretName,
				type: 'env_list',
				value_str: envVarsToString(envVarList || []),
				include_in_image: includeInImage,
				processing_type: processingType
			};
			break;

		case 'file':
			if (fileValue) {
				// New file uploaded, process it
				try {
					const arrayBuffer = await fileValue.arrayBuffer();
					const base64Data = arrayBufferToBase64(arrayBuffer);

					request = {
						display_name: secretName,
						type: 'file',
						filename: fileValue.name,
						value_b64: base64Data,
						include_in_image: includeInImage,
						processing_type: processingType
					};
				} catch (error) {
					console.error('Error processing file:', error);
					return null;
				}
			} else {
				// Editing existing file secret without changing the file
				request = {
					display_name: secretName,
					type: 'file',
					include_in_image: includeInImage,
					processing_type: processingType
				};
			}
			break;
	}

	return request;
};

export const downloadSecretFile = async (secretId: string, filename: string): Promise<boolean> => {
	try {
		const response = await fetch(`/api/secrets/${secretId}/download`);
		if (!response.ok) {
			throw new Error('Failed to download file');
		}

		const blob = await response.blob();
		const url = window.URL.createObjectURL(blob);

		const a = document.createElement('a');
		a.href = url;
		a.download = filename || `secret_${secretId}.bin`;
		document.body.appendChild(a);
		a.click();
		window.URL.revokeObjectURL(url);
		document.body.removeChild(a);
		return true;
	} catch (error) {
		console.error('Error downloading file:', error);
		return false;
	}
};

export const resetFileInputById = (inputId: string): void => {
	const fileInput = document.getElementById(inputId) as HTMLInputElement;
	if (fileInput) {
		fileInput.value = '';
	}
};

export const sendSecretRequest = async (
	secretId: string | null,
	secretData: CreateSecretRequest
): Promise<{ success: boolean; id?: string; display_name?: string; error?: string }> => {
	try {
		// Create or update secret
		const isCreating = !secretId;
		const endpoint = isCreating ? '/api/secrets' : `/api/secrets/${secretId}`;
		const method = isCreating ? 'POST' : 'PATCH';

		const response = await fetch(endpoint, {
			method,
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(secretData)
		});

		if (!response.ok) {
			return { success: false, error: `HTTP error ${response.status}` };
		}

		const result = await response.json();

		return {
			success: true,
			id: result.id,
			display_name: result.display_name
		};
	} catch (error) {
		console.error('Error sending secret request:', error);
		return {
			success: false,
			error: error instanceof Error ? error.message : 'Unknown error occurred'
		};
	}
};
