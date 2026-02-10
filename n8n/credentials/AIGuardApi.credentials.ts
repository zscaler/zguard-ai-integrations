import {
	IAuthenticateGeneric,
	ICredentialTestRequest,
	ICredentialType,
	INodeProperties,
} from 'n8n-workflow';

export class AIGuardApi implements ICredentialType {
	name = 'aiGuardApi';
	displayName = 'Zscaler AI Guard API';
	documentationUrl = 'https://help.zscaler.com/ai-guard';
	properties: INodeProperties[] = [
		{
			displayName: 'API Key',
			name: 'apiKey',
			type: 'string',
			typeOptions: {
				password: true,
			},
			default: '',
			required: true,
			description: 'The API key for Zscaler AI Guard API',
		},
		{
			displayName: 'Cloud Environment',
			name: 'cloud',
			type: 'options',
			options: [
				{
					name: 'US1',
					value: 'us1',
				},
				{
					name: 'US2',
					value: 'us2',
				},
				{
					name: 'EU1',
					value: 'eu1',
				},
				{
					name: 'EU2',
					value: 'eu2',
				},
				{
					name: 'Custom',
					value: 'custom',
				},
			],
			default: 'us1',
			required: true,
			description: 'The cloud environment where your AI Guard instance is deployed',
		},
		{
			displayName: 'Custom Base URL',
			name: 'customBaseUrl',
			type: 'string',
			default: '',
			required: true,
			placeholder: 'https://api.custom.zseclipse.net',
			description: 'Custom base URL for AI Guard API (only used when Cloud is set to Custom)',
			displayOptions: {
				show: {
					cloud: ['custom'],
				},
			},
		},
		{
			displayName: 'Policy ID',
			name: 'policyId',
			type: 'string',
			default: '',
			placeholder: 'e.g. 760 or leave empty for auto-resolution',
			description: 'Optional: The AI Guard policy ID to use for scans. If omitted, uses the policy linked to your API key.',
		},
	];

	authenticate: IAuthenticateGeneric = {
		type: 'generic',
		properties: {
			headers: {
				'Authorization': '=Bearer {{$credentials.apiKey}}',
				'Content-Type': 'application/json',
			},
		},
	};

	test: ICredentialTestRequest = {
		request: {
			baseURL: '={{$credentials.cloud === "custom" ? $credentials.customBaseUrl : $credentials.cloud === "eu1" ? "https://api.eu1.zseclipse.net" : $credentials.cloud === "eu2" ? "https://api.eu2.zseclipse.net" : $credentials.cloud === "us2" ? "https://api.us2.zseclipse.net" : "https://api.us1.zseclipse.net"}}',
			url: '/v1/detection/execute-policy',
			method: 'POST',
			body: '={{ $credentials.policyId ? { "content": "Hello, this is a test to verify API credentials.", "direction": "IN", "policyId": parseInt($credentials.policyId) } : { "content": "Hello, this is a test to verify API credentials.", "direction": "IN" } }}',
		},
		rules: [
			{
				type: 'responseCode',
				properties: {
					message: 'Credential test successful',
					value: 200,
				},
			},
		],
	};
}
