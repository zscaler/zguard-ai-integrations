import {
	IExecuteFunctions,
	INodeExecutionData,
	INodeType,
	INodeTypeDescription,
	NodeOperationError,
	NodeApiError,
	IHttpRequestMethods,
	IDataObject,
	IHttpRequestOptions,
	ICredentialDataDecryptedObject,
	ApplicationError,
	NodeConnectionType,
	sleep,
	randomString,
} from 'n8n-workflow';

interface AIGuardCredentials {
	apiKey: string;
	cloud: string;
	customBaseUrl?: string;
	policyId?: string;
}

interface AIGuardRequest {
	content: string;
	direction: 'IN' | 'OUT';
	policyId?: number;
}

interface DetectorResponse {
	triggered: boolean;
	action?: string;
}

interface AIGuardResponse {
	action: 'ALLOW' | 'BLOCK' | 'DETECT';
	severity?: string;
	transactionId: string;
	detectorResponses?: Record<string, DetectorResponse>;
}

class AIGuardScanner {
	async executeScan(
		context: IExecuteFunctions,
		baseUrl: string,
		scanRequest: AIGuardRequest,
		timeout: number,
		maxRetries: number
	): Promise<AIGuardResponse> {
		const options: IHttpRequestOptions = {
			method: 'POST' as IHttpRequestMethods,
			url: `${baseUrl}/v1/detection/execute-policy`,
			body: scanRequest,
			json: true,
			timeout,
			returnFullResponse: true,
		};

		return await this.executeWithRetry(context, options, maxRetries);
	}

	private async executeWithRetry(
		context: IExecuteFunctions,
		options: IHttpRequestOptions,
		maxRetries: number
	): Promise<any> {
		let lastError: Error | undefined;

		for (let attempt = 0; attempt <= maxRetries; attempt++) {
			try {
				const response = await context.helpers.httpRequestWithAuthentication.call(context, 'aiGuardApi', options);
				return response.body || response;
			} catch (error) {
				lastError = error as Error;

				if (error instanceof NodeApiError) {
					// Don't retry on client errors (4xx)
					const code = (error as any).httpCode as number | string | undefined;
					const is4xx = typeof code === 'number' ? code >= 400 && code < 500 : /^4\d\d$/.test(String(code || ''));
					if (is4xx) {
						throw error;
					}
				}

				if (attempt < maxRetries) {
					// Exponential backoff
					const delay = Math.min(1000 * Math.pow(2, attempt), 30000);
					await sleep(delay);
				}
			}
		}

		throw lastError || new ApplicationError('Request failed after retries');
	}
}

export class AIGuard implements INodeType {
	private static getBaseURL(cloud: string, customBaseUrl?: string): string {
		if (cloud === 'custom') {
			if (!customBaseUrl || customBaseUrl.trim() === '') {
				throw new ApplicationError('Custom base URL is required when cloud is set to "custom"');
			}
			return customBaseUrl.replace(/\/$/, '');
		}
		if (cloud === 'us1') return 'https://api.us1.zseclipse.net';
		if (cloud === 'us2') return 'https://api.us2.zseclipse.net';
		if (cloud === 'eu1') return 'https://api.eu1.zseclipse.net';
		if (cloud === 'eu2') return 'https://api.eu2.zseclipse.net';
		throw new ApplicationError(`Unknown cloud "${cloud}". Expected "us1", "us2", "eu1", "eu2", or "custom".`);
	}

	private static extractTriggeredDetectors(detectorResponses?: Record<string, DetectorResponse>): string[] {
		const triggered: string[] = [];
		if (detectorResponses) {
			for (const [name, response] of Object.entries(detectorResponses)) {
				if (response.triggered) {
					triggered.push(name);
				}
			}
		}
		return triggered;
	}

	private static validateContentSize(content: string): void {
		const contentSize = Buffer.byteLength(content, 'utf8');
		const maxSize = 5 * 1024 * 1024; // 5MB limit

		if (contentSize > maxSize) {
			throw new ApplicationError(
				`Content size (${Math.round(contentSize / 1024 / 1024)}MB) exceeds maximum limit (5MB)`
			);
		}
	}

	description: INodeTypeDescription = {
		displayName: 'Zscaler AI Guard',
		name: 'aiGuard',
		icon: 'file:aiguard.svg',
		group: ['transform'],
		version: 1,
		subtitle: '={{$parameter["operation"]}}',
		description: 'Scan AI prompts and responses for security threats using Zscaler AI Guard',
		defaults: {
			name: 'AI Guard',
		},
		inputs: ['main'],
		outputs: ['main'],
		credentials: [
			{
				name: 'aiGuardApi',
				required: true,
			},
		],
		properties: [
			{
				displayName: 'Operation',
				name: 'operation',
				type: 'options',
				noDataExpression: true,
				options: [
					{
						name: 'Prompt Scan',
						value: 'promptScan',
						description: 'Scan user input/prompts for security threats',
						action: 'Scan a prompt for security threats',
					},
					{
						name: 'Response Scan',
						value: 'responseScan',
						description: 'Scan AI-generated responses for policy violations',
						action: 'Scan a response for policy violations',
					},
					{
						name: 'Dual Scan',
						value: 'dualScan',
						description: 'Scan both prompt and response in sequence',
						action: 'Perform dual scanning of prompt and response',
					},
				],
				default: 'promptScan',
			},
			{
				displayName: 'Content',
				name: 'content',
				type: 'string',
				requiresDataPath: 'single',
				typeOptions: {
					rows: 4,
				},
				default: '',
				required: true,
				description: 'The content to scan for security threats',
				displayOptions: {
					show: {
						operation: ['promptScan', 'responseScan'],
					},
				},
			},
			{
				displayName: 'Prompt Content',
				name: 'promptContent',
				type: 'string',
				requiresDataPath: 'single',
				typeOptions: {
					rows: 3,
				},
				default: '',
				required: true,
				description: 'The prompt content to scan',
				displayOptions: {
					show: {
						operation: ['dualScan'],
					},
				},
			},
			{
				displayName: 'Response Content',
				name: 'responseContent',
				type: 'string',
				requiresDataPath: 'single',
				typeOptions: {
					rows: 3,
				},
				default: '',
				required: true,
				description: 'The response content to scan',
				displayOptions: {
					show: {
						operation: ['dualScan'],
					},
				},
			},
			{
				displayName: 'Additional Options',
				name: 'additionalOptions',
				type: 'collection',
				placeholder: 'Add Option',
				default: {},
				options: [
					{
						displayName: 'AI Model',
						name: 'aiModel',
						type: 'string',
						default: 'n8n-integration',
						description: 'AI model identifier for metadata',
					},
					{
						displayName: 'Application Name',
						name: 'applicationName',
						type: 'string',
						default: 'n8n-workflow',
						description: 'Application name for audit trails',
					},
					{
						displayName: 'Environment',
						name: 'environment',
						type: 'string',
						default: '',
						placeholder: 'e.g., production, staging, development',
						description: 'Environment identifier for attribution and tracking (optional)',
					},
					{
						displayName: 'Max Retries',
						name: 'maxRetries',
						type: 'number',
						default: 3,
						description: 'Maximum number of retry attempts for failed requests',
					},
					{
						displayName: 'Policy ID Override',
						name: 'policyIdOverride',
						type: 'string',
						default: '',
						description: 'Override the default policy ID. Leave empty to use credential policy or auto-resolution.',
					},
					{
						displayName: 'Timeout (Ms)',
						name: 'timeout',
						type: 'number',
						default: 30000,
						description: 'Request timeout in milliseconds',
					},
					{
						displayName: 'Transaction ID',
						name: 'transactionId',
						type: 'string',
						default: '',
						description: 'Custom transaction ID for tracking. If empty, one will be generated.',
					},
					{
						displayName: 'User ID',
						name: 'userId',
						type: 'string',
						default: 'n8n-user',
						description: 'User identifier for audit trails',
					},
				],
			},
		],
	};

	async execute(this: IExecuteFunctions): Promise<INodeExecutionData[][]> {
		const items = this.getInputData();
		const returnData: INodeExecutionData[] = [];
		const credentials = (await this.getCredentials('aiGuardApi')) as AIGuardCredentials;

		const baseUrl = AIGuard.getBaseURL(credentials.cloud, credentials.customBaseUrl);

		for (let i = 0; i < items.length; i++) {
			try {
				const operation = this.getNodeParameter('operation', i) as string;
				const additionalOptions = this.getNodeParameter('additionalOptions', i, {}) as IDataObject;

				const workflow = this.getWorkflow();
				const context = {
					workflowName: workflow?.name || '',
					workflowId: workflow?.id || '',
					executionId: this.getExecutionId() || '',
					executionMode: this.getMode() || '',
				};

				const transactionId = (additionalOptions.transactionId as string) || `n8n-${randomString(16)}-${Date.now()}`;
				const aiModel = (additionalOptions.aiModel as string) || 'n8n-integration';
				const applicationName = (additionalOptions.applicationName as string) || 'n8n-workflow';
				const userId = (additionalOptions.userId as string) || 'n8n-user';
				const environment = (additionalOptions.environment as string) || '';
				const timeout = (additionalOptions.timeout as number) || 30000;
				const rawMaxRetries = (additionalOptions.maxRetries as number) || 3;
				const maxRetries = Math.min(rawMaxRetries, 6);
				const policyIdOverride = (additionalOptions.policyIdOverride as string) || '';
				const policyIdToUse = policyIdOverride || credentials.policyId;

				const scanner = new AIGuardScanner();
				let scanResult: AIGuardResponse;

				// Execute based on operation
				switch (operation) {
					case 'promptScan': {
						const content = this.getNodeParameter('content', i) as string;
						AIGuard.validateContentSize(content);

						const request: AIGuardRequest = {
							content,
							direction: 'IN',
						};
						if (policyIdToUse) {
							request.policyId = parseInt(policyIdToUse);
						}

						scanResult = await scanner.executeScan(this, baseUrl, request, timeout, maxRetries);
						break;
					}
					case 'responseScan': {
						const content = this.getNodeParameter('content', i) as string;
						AIGuard.validateContentSize(content);

						const request: AIGuardRequest = {
							content,
							direction: 'OUT',
						};
						if (policyIdToUse) {
							request.policyId = parseInt(policyIdToUse);
						}

						scanResult = await scanner.executeScan(this, baseUrl, request, timeout, maxRetries);
						break;
					}
					case 'dualScan': {
						const promptContent = this.getNodeParameter('promptContent', i) as string;
						const responseContent = this.getNodeParameter('responseContent', i) as string;
						
						AIGuard.validateContentSize(promptContent);
						AIGuard.validateContentSize(responseContent);

						// Scan prompt first
						const promptRequest: AIGuardRequest = {
							content: promptContent,
							direction: 'IN',
						};
						if (policyIdToUse) {
							promptRequest.policyId = parseInt(policyIdToUse);
						}

						const promptResult = await scanner.executeScan(this, baseUrl, promptRequest, timeout, maxRetries);

						// If prompt is blocked, don't scan response
						if (promptResult.action === 'BLOCK') {
							scanResult = promptResult;
							break;
						}

						// Scan response
						const responseRequest: AIGuardRequest = {
							content: responseContent,
							direction: 'OUT',
						};
						if (policyIdToUse) {
							responseRequest.policyId = parseInt(policyIdToUse);
						}

						const responseResult = await scanner.executeScan(this, baseUrl, responseRequest, timeout, maxRetries);

						// Combine results
						scanResult = {
							...responseResult,
							promptScan: promptResult,
						} as any;
						break;
					}
					default:
						throw new NodeOperationError(this.getNode(), `Unknown operation: ${operation}`);
				}

				// Extract triggered detectors
				const triggeredDetectors = AIGuard.extractTriggeredDetectors(scanResult.detectorResponses);

				// Prepare output data
				const outputData: IDataObject = {
					operation,
					...scanResult,
					severity: scanResult.severity || 'NONE',
					detectors: triggeredDetectors,
					blocked: scanResult.action === 'BLOCK',
					...(context.workflowId && { workflowId: context.workflowId }),
					...(context.workflowName && { workflowName: context.workflowName }),
					...(context.executionId && { executionId: context.executionId }),
					...(context.executionMode && { executionMode: context.executionMode }),
					...(environment && { environment }),
					timestamp: new Date().toISOString(),
				};

				returnData.push({
					json: outputData,
					pairedItem: { item: i },
				});

			} catch (error) {
				if (this.continueOnFail()) {
					returnData.push({
						json: {
							error: error instanceof Error ? error.message : 'Unknown error',
							action: 'ALLOW', // Fail open
							blocked: false,
							timestamp: new Date().toISOString(),
						},
						pairedItem: { item: i },
					});
				} else {
					throw error;
				}
			}
		}

		return [returnData];
	}
}
