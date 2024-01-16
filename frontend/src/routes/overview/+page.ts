import type { PageLoad } from './$types';

type SettingValue = { value: any }
type ModuleSettings = { type: string, settings: { [key: string]: SettingValue } };
type Device = { hostname: string, displayName: string, modules: ModuleSettings[], tags: string[] };

export const load = (async ({ fetch }) => {
    const stateResponse = await fetch('http://localhost:8000/state', {
        method: 'GET',
        headers: {
            'content-type': 'application/json'
        }
    });
    const devices = (await stateResponse.json())["devices"] as Device[];
    return {
        devices: devices,
    };
}) satisfies PageLoad;
