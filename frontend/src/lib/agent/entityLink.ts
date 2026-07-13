export type AssistantEntityType = 'configuration' | 'device' | 'tag' | 'task';

export type AssistantEntityLink = {
	entityType: AssistantEntityType;
	identifier: string;
	label?: string;
};

export const isAssistantEntityLink = (value: unknown): value is AssistantEntityLink => {
	if (!value || typeof value !== 'object') return false;
	const entity = value as Record<string, unknown>;
	return (
		(typeof entity.entityType === 'string' &&
			['configuration', 'device', 'tag', 'task'].includes(entity.entityType) &&
			typeof entity.identifier === 'string' &&
			entity.identifier.length > 0 &&
			(entity.label === undefined || typeof entity.label === 'string')) ||
		false
	);
};
