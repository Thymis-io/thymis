import type { UIMessage } from 'ai';
import { fetchWithNotify } from '$lib/fetchWithNotify';

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

export const listConversations = async (): Promise<AssistantConversationSummary[]> => {
	const response = await fetchWithNotify('/api/agent/conversations');
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
		404: 'That assistant conversation no longer exists.'
	});
	if (!response.ok) return null;
	return (await response.json()) as AssistantConversation;
};

export const deleteConversation = async (id: string): Promise<boolean> => {
	const response = await fetchWithNotify(`/api/agent/conversations/${id}`, {
		method: 'DELETE'
	});
	return response.ok;
};
