import { invalidate } from '$app/navigation';

export type SettingTypes = {
    type: 'bool';
    value: boolean;
} | {
    type: 'string';
    value: string;
} | {
    type: 'path';
    value: string;
};

export type Setting = SettingTypes & {
    name: string;
    // value: unknown;
    default: string;
    description: string;
    example: string | null;
    // type: string;
};

export type Module = { name: string } & Record<string, Setting>;

export type SettingValue = { value: SettingTypes }
export type ModuleSettings = { type: string, settings: { [key: string]: SettingValue } };
export type Tag = { name: string, priority: number, modules: ModuleSettings[] };
export type Device = { hostname: string, displayName: string, modules: ModuleSettings[], tags: string[] };

export type State = {
    modules: Module[];
    devices: Device[];
    tags: Tag[];
};

export async function saveState(state: State) {
    await fetch('http://localhost:8000/state', {
        method: 'PATCH',
        headers: {
            'content-type': 'application/json'
        },
        body: JSON.stringify(state)
    });
    await invalidate('http://localhost:8000/state');
    await invalidate('http://localhost:8000/available_modules');
}
