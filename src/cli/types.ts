/**
 * Plugin manifest type definitions
 */
export interface PluginManifest {
  name: string;
  version: string;
  description: string;
  author: string;
  category: 'data' | 'filesystem' | 'communication' | 'ai' | 'integration';
  capabilities: string[];
  entry: string;
  tags: string[];
  marketplace: {
    title: string;
    icon: string;
    price: 'free' | 'paid';
  };
}

/**
 * Skill manifest type definitions
 */
export interface SkillAction {
  id: string;
  type: string;
  config: Record<string, unknown>;
}

export interface SkillManifest {
  name: string;
  version: string;
  description: string;
  agent: string;
  triggers: string[];
  actions: SkillAction[];
  tags: string[];
}

/**
 * Marketplace entry combining plugin info with registry metadata
 */
export interface MarketplaceEntry {
  name: string;
  version: string;
  title: string;
  description: string;
  category: string;
  icon: string;
  price: string;
  tags: string[];
  capabilities: string[];
}

/**
 * Marketplace index
 */
export interface Marketplace {
  generated_at: string;
  total: number;
  plugins: MarketplaceEntry[];
}
