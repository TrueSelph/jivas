export type Agent = {
	id: string;
	name: string;
	thumbnail?: string;
};

export type Action = {
	id: string;
	version: string;
	label: string;
	description: string;
	enabled: boolean;
	_package: {
		name?: string;
		author?: string;
		architype?: string;
		version?: string;
		meta?: {
			title?: string;
			description?: string;
			group?: string;
			type?: string;
		};
		config?: {
			singleton?: boolean;
			order?: {
				weight?: number;
				before?: string;
			};
			path?: string;
			app?: boolean;
			module_root?: string;
			module?: string;
			namespace?: string;
			package_name?: string;
		};
		dependencies?: {
			jivas?: string;
			actions?: Record<string, string>;
			pip?: Record<string, string>;
		};
	};
	anchors?: any[];
	functions?: any[];
	weight?: number;
	prompt?: string;
	timezone?: string;
	history?: boolean;
	history_size?: number;
	max_statement_length?: number;
	model_action?: string;
	model_name?: string;
	model_temperature?: number;
	model_max_tokens?: number;
	channel_format_directives?: Record<string, string>;
	user_model?: boolean;
	exceptions?: any[];
	permissions?: {
		default?: {
			any?: {
				deny?: string[];
				allow?: string[];
			};
		};
		whatsapp?: {
			any?: {
				deny?: string[];
				allow?: string[];
			};
		};
	};
	session_groups?: Record<string, any>;
	api_url?: string;
	instance_id?: string;
	token?: string;
	phone_number?: string;
	base_url?: string;
	webhook_url?: string;
	webhook_properties?: Record<string, any>;
	chunk_length?: number;
	use_pushname?: boolean;
	ignore_newsletters?: boolean;
	request_timeout?: number;
	outbox_base_rate_per_minute?: number;
	outbox_send_interval?: number;
	outbox_min_send_interval?: number;
	outbox_max_send_interval?: number;
	outbox_min_batch_size?: number;
	outbox_max_batch_size?: number;
	outbox?: Record<string, any>;
	api_key?: string;
	secret_key?: string;
	session?: string;
	ignore_forwards?: boolean;
	sync_pushname?: boolean;
	sync_avatar?: boolean;
	poll_manager_action?: string;
	model?: string;
	voice?: string;
	smart_format?: boolean;
	policy_url?: string;
	content?: string;
	config?: Record<string, any>;
	provider?: string;
	api_version?: string;
	azure_endpoint?: string;
	collection_name?: string;
	embedding_model_endpoint?: string;
	embedding_model_api_key?: string;
	embedding_model_api_version?: string;
	embedding_model_name?: string;
	embedding_model_provider?: string;
	export_page_size?: number;
	host?: string;
	port?: string;
	protocol?: string;
	connection_timeout?: number;
	vector_dims?: number;
	vector_store_action?: string;
	doc_manifest?: Record<string, any>;
	key_or_url?: string;
	worksheet_title?: string;
	info_type?: string;
	project_id?: string;
	private_key_id?: string;
	private_key?: string;
	client_email?: string;
	client_id?: string;
	auth_uri?: string;
	token_uri?: string;
	auth_provider_x509_cert_url?: string;
	client_x509_cert_url?: string;
	universe_domain?: string;
};

export type Package = {
	id: string;
	downloads: number;
	title: string;
	name: string;
	key: string;
	type: string;
	version: string;
	publishedAt: string;
	package: string;
	keywords: string[];
	description: string;
	organization: {
		name: string;
	};
};

export interface ApiResponse<T> {
	status: number;
	reports: T[];
}
