import { fetchWithNotify } from './fetchWithNotify';

export type DeploymentInfo = {
	id: string;
	ssh_public_key: string;
	deployed_config_commit: string | null;
	deployed_config_id: string | null;
	reachable_deployed_host: string | null;
};

export const getDeploymentInfoByConfigId = async (
	fetch: typeof window.fetch,
	deployedConfigId: string
) => {
	const response = await fetchWithNotify(
		`/api/deployment_infos_by_config_id/${deployedConfigId}`,
		undefined,
		{ 404: `Deployment info not found for config id ${deployedConfigId}` },
		fetch
	);
	if (response.ok) {
		const deploymentInfos = await response.json();
		if (deploymentInfos.length == 1) {
			return deploymentInfos[0] as DeploymentInfo;
		} else if (deploymentInfos.length > 1) {
			console.error(
				`Multiple deployment infos found for config id ${deployedConfigId}, using the first one`
			);
			return deploymentInfos[0] as DeploymentInfo;
		}
	}
};

export const getDeploymentInfosByConfigId = async (
	fetch: typeof window.fetch,
	deployedConfigId: string
) => {
	const response = await fetchWithNotify(
		`/api/deployment_infos_by_config_id/${deployedConfigId}`,
		undefined,
		{ 404: `Deployment info not found for config id ${deployedConfigId}` },
		fetch
	);
	if (response.ok) {
		return (await response.json()) as DeploymentInfo[];
	}
	return [];
};

export const getConnectedDeploymendInfosByConfigId = async (
	fetch: typeof window.fetch,
	deployedConfigId: string
) => {
	const response = await fetchWithNotify(
		`/api/connected_deployment_infos_by_config_id/${deployedConfigId}`,
		undefined,
		{ 404: `Deployment info not found for config id ${deployedConfigId}` },
		fetch
	);
	if (response.ok) {
		return (await response.json()) as DeploymentInfo[];
	}
	return [];
};

export const getAllDeploymentInfos = async (fetch: typeof window.fetch) => {
	const response = await fetchWithNotify('/api/deployment_info', undefined, {}, fetch);
	if (response.ok) {
		return (await response.json()) as DeploymentInfo[];
	}
	return [];
};

export const getAllDeploymentInfosAsMapFromConfigId = async (fetch: typeof window.fetch) => {
	const deploymentInfos = await getAllDeploymentInfos(fetch);
	const deploymentInfosMap = new Map<string, DeploymentInfo[]>();
	for (const deploymentInfo of deploymentInfos) {
		const configId = deploymentInfo.deployed_config_id;
		if (!configId) {
			continue;
		}
		if (deploymentInfosMap.has(configId)) {
			deploymentInfosMap.get(configId)?.push(deploymentInfo);
		} else {
			deploymentInfosMap.set(configId, [deploymentInfo]);
		}
	}
	return deploymentInfosMap;
};
