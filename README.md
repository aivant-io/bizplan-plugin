# BizPlan Plugins

AI-powered business plan and financial model generators for pre-launch founders. Works with **Claude Code** and **Claude Cowork**.

## Available Plugins

### bizplan-ecommerce

Generate professional ecommerce business plans and 6-year financial models.

**What it does:**
- Walks you through a structured founder questionnaire (product category, pricing, channels, team, funding)
- Resolves 49 financial drivers using curated industry benchmarks across 11 product categories and 5 regions
- Populates a pre-built Excel financial model with income statement, balance sheet, cash flow, and key metrics
- Writes a narrative business plan with market context and citations
- Optimizes equity/funding to ensure positive cash flow

**Commands:**
- `/bizplan` - Full pipeline: questionnaire + financial model + business plan
- `/financial-model` - Generate the Excel financial model only
- `/business-plan` - Write the narrative business plan only

**Categories supported:** Fashion/Apparel, Electronics/Gadgets, Health/Wellness, Beauty/Personal Care, Home/Kitchen, Food/Beverage, Pet Products, Sports/Outdoors, Baby/Kids, Jewelry/Accessories, Books/Stationery

**Regions supported:** US, UK, EU, Canada, Australia

## Installation

### Claude Code (CLI)

```bash
# Install from marketplace
claude plugin marketplace add <your-github-username>/bizplan-plugin
claude plugin install bizplan-ecommerce@bizplan-plugins

# Or install directly from GitHub
claude plugin install github:<your-github-username>/bizplan-plugin/bizplan-ecommerce
```

### Claude Cowork (Desktop)

1. Open Claude Desktop
2. Go to Customize > Plugins
3. Search for "bizplan-ecommerce"
4. Click Install

## Usage

```
/bizplan
```

Claude will walk you through the intake questionnaire and generate:
1. **Excel financial model** (.xlsx) - 6-year forecast with three financial statements
2. **Business plan** (.md) - Professional narrative with market analysis and citations

## Requirements

- **Claude Pro, Max, Team, or Enterprise** subscription
- **Python 3.11+** (for Excel generation)
- **openpyxl** and **xlcalculator** (auto-installed via requirements.txt)
- **Pandoc** (optional, for DOCX export)

## Roadmap

| Vertical | Status |
|----------|--------|
| Ecommerce | Available |
| SaaS | Planned |
| Marketplace | Planned |
| Services / Agency | Planned |
| D2C CPG | Planned |

## License

Apache 2.0 - see [LICENSE](LICENSE)
