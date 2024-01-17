import type { PageLoad } from './$types';
import type { State, Device } from '$lib/state';

export const load = (async ({ fetch }) => {
    const stateResponse = await fetch('http://localhost:8000/state', {
        method: 'GET',
        headers: {
            'content-type': 'application/json'
        }
    });

    const state = (await stateResponse.json()) as State;
    const devices = state.devices as Device[];

    return {
        state: state,
        devices: devices,
    };
}) satisfies PageLoad;
