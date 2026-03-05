# TrustRadar Data Sources Research

**Generated:** 2026-03-04  
**Research Duration:** 5m 40s

---

## RSS Feeds (19+ Sources)

### US Government & Law Enforcement

1. **FTC Consumer Blog** - `https://www.ftc.gov/news-events/stay-connected/ftc-rss-feeds`
   - Focus: Consumer protection, fraud alerts, scams
   - Update frequency: Multiple times weekly

2. **FBI IC3 News** - `https://www.ic3.gov/PSA/RSS`
   - Focus: Internet crime, scam alerts, fraud schemes
   - Update frequency: Weekly

3. **FBI IC3 Industry Alerts** - `https://www.ic3.gov/CSA/RSS`
   - Focus: Industry-specific cybercrime alerts
   - Update frequency: Monthly

### Data Breach & Security

4. **Krebs on Security** - `https://krebsonsecurity.com/category/data-breaches/feed`
   - Focus: Major data breaches, cyber incidents
   - Update frequency: Multiple times weekly
   - Quality: High (Industry-leading security journalist)

5. **Databreaches.net** - `https://databreaches.net/feed`
   - Focus: Data breach notifications, analysis
   - Update frequency: Daily

6. **Have I Been Pwned** - `https://feeds.feedburner.com/HaveIBeenPwned/`
   - Focus: New data breach discoveries
   - Update frequency: Weekly

7. **UpGuard Breaches** - `https://upguard.com/breaches/rss.xml`
   - Focus: Third-party risk, breach detection
   - Update frequency: Multiple times weekly

### Fraud Detection & Prevention

8. **Fraud of the Day** - `https://fraudoftheday.com/feed`
   - Focus: Daily fraud cases, government prosecutions
   - Update frequency: Daily

9. **Action Fraud UK** - `https://actionfraud.police.uk/news/feed`
   - Focus: UK fraud alerts, cybercrime
   - Update frequency: Multiple times weekly

10. **Current Scams** - `https://currentscams.com/index.php/feed/`
    - Focus: Latest scam attempts, phishing alerts
    - Update frequency: Daily

11. **Fraud.org** - `https://fraud.org/feed/`
    - Focus: General fraud prevention
    - Update frequency: Weekly

---

## APIs (5+ Sources)

### Security & Breach APIs

1. **Have I Been Pwned API v3** - `https://haveibeenpwned.com/API/v3`
   - Documentation: https://haveibeenpwned.com/API/v3
   - Authentication: Required (HIBP API key)
   - Key endpoints:
     - `GET /breachedaccount/{account}` - Check if email in breach
     - `GET /breaches` - Get all breaches in system
     - `GET /pwnedpassword/{range}` - Check password (no auth required)
   - Quality: Excellent (trusted breach database)

2. **CISA KEV Catalog API** - `https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json`
   - Documentation: Available via CISA KEV catalog
   - Authentication: Not Required
   - Data format: JSON with CVE ID, vendor, product, vulnerability
   - Update frequency: Weekly
   - Note: CISA discontinued RSS feeds in May 2025

3. **Trustpilot API** - `https://developers.trustpilot.com/`
   - Documentation: https://developers.trustpilot.com/
   - Authentication: Required (OAuth 2.0)
   - Key endpoints:
     - Consumer API - Consumer information and reviews
     - Product Reviews API - Product ratings
     - Service Reviews API - Service ratings
     - Business Units API - Business information
   - Quality: High (official API)

### Product Recall APIs

4. **CPSC Recall API** - `https://www.cpsc.gov/Recalls/CPSC-Recalls-Application-Program-Interface-API-Information`
   - Documentation: Available at CPSC.gov
   - Authentication: Unknown
   - Data: Recall notifications
   - Note: Alternative GitHub repo `trietmnj/cpsc_recalls_api` provides Python interface

5. **WordPress API (SafetyData.org)** - `https://safetydata.org/wp-json/`
   - Documentation: WordPress REST API standard
   - Authentication: Not Required
   - Endpoints: `/wp/v2/posts` - All safety posts

---

## Web Scraping Targets (12+ Sites)

### Official Government Sites

1. **FTC Consumer Alerts** - `https://www.consumer.ftc.gov`
   - Target: Alerts blog, scam database, news releases
   - Update frequency: Multiple times weekly

2. **IC3.gov** - `https://www.ic3.gov`
   - Target: PSA (Public Service Announcements), CSA (Common Scam Alerts)
   - Update frequency: Weekly

3. **CPSC.gov Recalls** - `https://www.cpsc.gov/Recalls`
   - Target: Recall listings, search results
   - Update frequency: As recalls announced

4. **FDA Recalls** - `https://www.fda.gov/recalls`
   - Target: Food, drug, medical device recalls
   - Update frequency: Multiple times weekly

5. **NHTSA Recalls** - `https://www.nhtsa.gov/recalls`
   - Target: Vehicle, equipment recalls
   - Update frequency: Weekly

### Industry & Advocacy Sites

6. **BBB.org** - `https://www.bbb.org`
   - Target: Business profiles, scam alerts, news
   - Update frequency: Daily
   - Warning: BBB blocks automated scraping

7. **Online Threat Alerts (OTA)** - `https://www.onlinethreatalerts.com`
   - Target: Latest threats, scam database
   - Update frequency: Daily

8. **Fraud.org** - `https://fraud.org`
   - Target: Scam database, educational articles
   - Update frequency: Weekly

9. **IdentityTheft.gov** - `https://www.identitytheft.gov`
   - Target: Alert updates, recovery guides
   - Update frequency: Monthly

10. **Scamwatch.gov.au** - `https://www.scamwatch.gov.au`
    - Target: Current scams, scam types database
    - Update frequency: Weekly

---

## Recommended Configuration (Top 15 Sources)

```yaml
trust:
  - name: "FTC Consumer Blog"
    url: "https://www.ftc.gov/news-events/stay-connected/ftc-rss-feeds"
    type: "rss"
    priority: "high"
    focus: "consumer_protection"
  
  - name: "FBI IC3 News"
    url: "https://www.ic3.gov/PSA/RSS"
    type: "rss"
    priority: "high"
    focus: "cybercrime"
  
  - name: "Have I Been Pwned API"
    url: "https://haveibeenpwned.com/API/v3"
    type: "api"
    auth_required: true
    priority: "high"
    focus: "data_breaches"
  
  - name: "Krebs on Security"
    url: "https://krebsonsecurity.com/category/data-breaches/feed"
    type: "rss"
    priority: "high"
    focus: "security_news"
  
  - name: "CISA KEV Catalog"
    url: "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
    type: "api"
    auth_required: false
    priority: "medium"
    focus: "vulnerabilities"
```

**Total Sources**: 19+ RSS, 5+ APIs, 12+ Scraping Targets

**Important Notes**:
- CISA RSS feeds discontinued (May 2025) - use JSON feed
- Have I Been Pwned requires API key for account searches
- BBB.org blocks automated scraping - API partnership needed
