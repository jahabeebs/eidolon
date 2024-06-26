export interface Company {
  name: string
  category?: string
  loading: boolean
  should_research: boolean
  researched_details?: CompanyDetails
  error?: string
}

export interface CompanyDetails {
  url: string
  process_id: string
  description: string
  stage: string
  market_size: string
  funding_information: string
  investors: string
  founders: string
  business_model: string
  logo_url: string
  relevance: number
  other_information?: string
  references?: Record<string, any>[]
  enriched_with_harmonic?: string
}

export interface Thesis {
  parent_process_id: string
  companyFinderPID: string
}
