import type { UIMessage } from 'ai';
import { get } from 'svelte/store';
import { _ } from 'svelte-i18n';
import { fetchWithNotify } from '$lib/fetchWithNotify';
import { isAssistantEntityLink } from './entityLink';

export type AssistantConversationSummary = {
	id: string;
	title: string;
	created_at: string;
	updated_at: string;
	message_count: number;
};

export type AssistantConversation = AssistantConversationSummary & {
	messages: UIMessage[];
};

const conversationsUrl = (query?: string) =>
	query ? `/api/agent/conversations?q=${encodeURIComponent(query)}` : '/api/agent/conversations';

export const listConversations = async (
	query?: string
): Promise<AssistantConversationSummary[]> => {
	const response = await fetchWithNotify(conversationsUrl(query));
	if (!response.ok) return [];
	return (await response.json()) as AssistantConversationSummary[];
};

export const createConversation = async (): Promise<AssistantConversation | null> => {
	const response = await fetchWithNotify('/api/agent/conversations', { method: 'POST' });
	if (!response.ok) return null;
	return (await response.json()) as AssistantConversation;
};

export const getConversation = async (id: string): Promise<AssistantConversation | null> => {
	const response = await fetchWithNotify(`/api/agent/conversations/${id}`, undefined, {
		404: get(_)('assistant.error-missing')
	});
	if (!response.ok) return null;
	return (await response.json()) as AssistantConversation;
};

export const renameConversation = async (id: string, title: string): Promise<boolean> => {
	const response = await fetchWithNotify(`/api/agent/conversations/${id}`, {
		method: 'PATCH',
		headers: { 'content-type': 'application/json' },
		body: JSON.stringify({ title })
	});
	return response.ok;
};

export const deleteConversation = async (id: string): Promise<boolean> => {
	const response = await fetchWithNotify(`/api/agent/conversations/${id}`, {
		method: 'DELETE'
	});
	return response.ok;
};

const textPart = (message: UIMessage) =>
	message.parts
		.filter((part) => part.type === 'text')
		.map((part) => part.text)
		.join('\n\n')
		.trim();

const metadataCreatedAt = (message: UIMessage) => {
	const metadata = message.metadata as { createdAt?: unknown } | undefined;
	return typeof metadata?.createdAt === 'string' ? metadata.createdAt : undefined;
};

/**
 * Render one conversation as Markdown, including the tool activity and entity
 * links that a plain text copy would lose.
 */
export const transcriptMarkdown = (title: string, messages: UIMessage[]): string => {
	const lines: string[] = [`# ${title}`, ''];
	for (const message of messages) {
		const createdAt = metadataCreatedAt(message);
		lines.push(
			`## ${message.role === 'user' ? 'Operator' : 'Thymis Assistant'}${createdAt ? ` (${createdAt})` : ''}`,
			''
		);
		for (const part of message.parts) {
			if (part.type === 'text' && part.text) {
				lines.push(part.text, '');
			} else if (part.type === 'file' && 'url' in part && typeof part.url === 'string') {
				lines.push(`![${part.filename ?? 'attachment'}](${part.url})`, '');
			} else if (part.type === 'reasoning' && part.text) {
				lines.push(...part.text.split('\n').map((line) => `> ${line}`), '');
			} else if (part.type === 'dynamic-tool' && part.toolName) {
				lines.push(`**Tool call: \`${part.toolName}\`**`, '');
				if ('input' in part && part.input !== undefined) {
					lines.push('```json', JSON.stringify(part.input, null, 2), '```', '');
				}
				if ('output' in part && part.output !== undefined && part.output !== null) {
					lines.push('```json', JSON.stringify(part.output, null, 2), '```', '');
				}
			} else if (part.type === 'data-entity-link' && isAssistantEntityLink(part.data)) {
				lines.push(`> ${part.data.entityType}: ${part.data.label} (${part.data.identifier})`, '');
			}
		}
	}
	return lines.join('\n');
};

export const downloadMarkdown = (title: string, markdown: string) => {
	const filename = `${title.replace(/[^\w.-]+/g, '-').replace(/^-|-$/g, '') || 'conversation'}.md`;
	const url = URL.createObjectURL(new Blob([markdown], { type: 'text/markdown' }));
	const anchor = document.createElement('a');
	anchor.href = url;
	anchor.download = filename;
	anchor.click();
	URL.revokeObjectURL(url);
};
