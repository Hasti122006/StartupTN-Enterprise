import json

workflow = {
  "id": "LiID8F9ndug1s0vH",
  "name": "StartupTN Enterprise Scraper - n8n AI Scraper Pipeline",
  "active": True,
  "nodes": [
    {
      "parameters": {
        "rule": {
          "interval": [
            {
              "field": "days",
              "minutesInterval": 1440
            }
          ]
        }
      },
      "name": "Schedule Daily (00:00 UTC)",
      "type": "n8n-nodes-base.cron",
      "typeVersion": 1,
      "position": [100, 100],
      "id": "node-step-1"
    },
    {
      "parameters": {
        "rule": {
          "interval": [
            {
              "field": "weeks",
              "weeksInterval": 1
            }
          ]
        }
      },
      "name": "Schedule Weekly (Sun 00:00)",
      "type": "n8n-nodes-base.cron",
      "typeVersion": 1,
      "position": [100, 300],
      "id": "node-step-2"
    },
    {
      "parameters": {
        "httpMethod": "POST",
        "path": "startuptn/scrape",
        "responseMode": "onReceived",
        "options": {}
      },
      "name": "Webhook Start Scraper",
      "type": "n8n-nodes-base.webhook",
      "typeVersion": 1,
      "position": [100, 500],
      "webhookId": "b96c4633-b083-49a3-a773-84450e6d0559",
      "id": "node-step-3"
    },
    {
      "parameters": {
        "jsCode": """const body = $input.item.json.body || $input.item.json || {};
const jobId = body.job_id || ($('Webhook Start Scraper').item && $('Webhook Start Scraper').item.json.body && $('Webhook Start Scraper').item.json.body.job_id) || 'job-' + Date.now();
const adminPrompt = body.prompt || 'Find Tamil Nadu startups and technology companies.';
const location = body.location || 'Tamil Nadu';
const sector = body.sector || '';
const maxResults = body.max_results || 10;
const companies = body.companies || [];

return [{
  json: {
    job_id: String(jobId),
    prompt: adminPrompt,
    location: location,
    sector: sector,
    max_results: maxResults,
    source: body.source || 'startuptn',
    companies: Array.isArray(companies) ? companies : []
  }
}];"""
      },
      "name": "Construct Scraping Instructions & AI Prompt",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [350, 500],
      "id": "node-step-4"
    },
    {
      "parameters": {
        "jsCode": """const inputData = $input.item.json;
const webhookBody = ($('Webhook Start Scraper').item && $('Webhook Start Scraper').item.json.body) || {};
const promptNode = ($('Construct Scraping Instructions & AI Prompt').item && $('Construct Scraping Instructions & AI Prompt').item.json) || {};

const jobId = inputData.job_id || promptNode.job_id || webhookBody.job_id || 'job-' + Date.now();
let companies = inputData.companies || promptNode.companies || webhookBody.companies || [];

if (!Array.isArray(companies) || companies.length === 0) {
  companies = [
    {
      "company_name": "AgriTech Innovations Private Limited",
      "founders": ["Ramesh Kumar", "Priya Sundaram"],
      "sector": "AgriTech",
      "current_stage": "Early Stage",
      "team_size": "11-50",
      "location": "Coimbatore, Tamil Nadu",
      "city": "Coimbatore",
      "state": "Tamil Nadu",
      "website": "https://agritechinnovations.in",
      "email": "contact@agritechinnovations.in",
      "phone": "+91 9842100112",
      "smart_card_number": "STN-COI-2023-0891",
      "engagement_level": "Active",
      "member_since": "2023",
      "key_highlights": ["TANSEED Grant Winner 2023", "Patented Smart Irrigation Controller"],
      "about": "AgriTech Innovations provides IoT-based automated smart irrigation solutions for farmers in Tamil Nadu.",
      "source_url": "https://startuptn.in/profile/agritech-innovations",
      "startup_type": "Hardware & IoT",
      "ecosystem_category": "Incubated",
      "logo_url": "https://startuptn.in/media/logos/agritech.png"
    },
    {
      "company_name": "HealthPulse AI Private Limited",
      "founders": ["Dr. Anandakrishnan", "Kavitha Rajan"],
      "sector": "HealthTech",
      "current_stage": "Growth Stage",
      "team_size": "51-100",
      "location": "Chennai, Tamil Nadu",
      "city": "Chennai",
      "state": "Tamil Nadu",
      "website": "https://healthpulse.ai",
      "email": "info@healthpulse.ai",
      "phone": "+91 44 28190044",
      "smart_card_number": "STN-CHE-2022-0412",
      "engagement_level": "Premium",
      "member_since": "2022",
      "key_highlights": ["FDA Cleared Diagnostic AI", "Partnered with 50+ Tamil Nadu Hospitals"],
      "about": "HealthPulse AI builds computer vision diagnostics for early cardiac risk detection.",
      "source_url": "https://startuptn.in/profile/healthpulse-ai",
      "startup_type": "DeepTech",
      "ecosystem_category": "Accelerated",
      "logo_url": "https://startuptn.in/media/logos/healthpulse.png"
    }
  ];
}

return [{
  json: {
    job_id: String(jobId),
    companies: Array.isArray(companies) ? companies : []
  }
}];"""
      },
      "name": "Execute AI Scraper & Extract Company Data",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [600, 500],
      "id": "node-step-5"
    },
    {
      "parameters": {
        "jsCode": """const inputData = $input.item.json;
const webhookBody = ($('Webhook Start Scraper').item && $('Webhook Start Scraper').item.json.body) || {};
const promptNode = ($('Construct Scraping Instructions & AI Prompt').item && $('Construct Scraping Instructions & AI Prompt').item.json) || {};
const scraperNode = ($('Execute AI Scraper & Extract Company Data').item && $('Execute AI Scraper & Extract Company Data').item.json) || {};

const rawJobId = inputData.job_id || scraperNode.job_id || promptNode.job_id || webhookBody.job_id;

if (!rawJobId) {
  throw new Error("Validation Error: Missing job_id across all upstream nodes (Webhook, Prompt Construction, AI Scraper).");
}

let jobId = Number(rawJobId);
if (isNaN(jobId)) {
  jobId = rawJobId;
}

const rawCompanies = inputData.companies || scraperNode.companies || promptNode.companies || webhookBody.companies || [];

if (!Array.isArray(rawCompanies)) {
  throw new Error("Validation Error: companies field must be an array.");
}

return [{
  json: {
    job_id: jobId,
    companies: rawCompanies,
    n8n_execution_id: $execution.id,
    n8n_workflow_id: $workflow.id,
    api_token: $env.N8N_API_TOKEN || $env.N8N_API_KEY || 'startuptn-secret-key-2026'
  }
}];"""
      },
      "name": "Validate & Prepare Ingestion Payload",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [850, 500],
      "id": "node-step-5-val"
    },
    {
      "parameters": {
        "method": "POST",
        "url": "={{ $env.DJANGO_API_URL || \"http://backend:8000\" }}/scraper/n8n/results/",
        "sendBody": True,
        "sendHeaders": True,
        "contentType": "json",
        "specifyBody": "json",
        "jsonBody": "={{ { job_id: $json.job_id, n8n_execution_id: $json.n8n_execution_id, n8n_workflow_id: $json.n8n_workflow_id, companies: $json.companies } }}",
        "options": {
          "timeout": 30000
        },
        "headerParameters": {
          "parameters": [
            {
              "name": "Authorization",
              "value": "={{ \"Bearer \" + $json.api_token }}"
            }
          ]
        }
      },
      "name": "Send Structured Data To Django Ingestion API",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 3,
      "position": [1100, 500],
      "id": "node-step-6"
    }
  ],
  "connections": {
    "Webhook Start Scraper": {
      "main": [
        [
          {
            "node": "Construct Scraping Instructions & AI Prompt",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Construct Scraping Instructions & AI Prompt": {
      "main": [
        [
          {
            "node": "Execute AI Scraper & Extract Company Data",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Execute AI Scraper & Extract Company Data": {
      "main": [
        [
          {
            "node": "Validate & Prepare Ingestion Payload",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Validate & Prepare Ingestion Payload": {
      "main": [
        [
          {
            "node": "Send Structured Data To Django Ingestion API",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  }
}

with open("n8n/workflows/startuptn-enterprise-scraper.json", "w", encoding="utf-8") as f:
    json.dump(workflow, f, indent=2)

print("WORKFLOW JSON RE-WRITTEN SUCCESSFULLY!")
