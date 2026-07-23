# Strategic SearXNG Configuration: Quality Over Quantity

**Philosophy:** Optimize for coverage, resilience, and performance—not engine count.

**Status:** Planning optimal multi-tier engine configuration

---

## Principles

1. **Independent Indexes First** - Brave, Mojeek reduce reliance on single sources
2. **Diversity Over Duplication** - Skip redundant Google/Bing clones
3. **Regional/Language Specific** - Baidu for Chinese, Yandex for Russian, etc.
4. **Specialized Excellence** - GitHub for code, OpenAlex for papers, etc.
5. **Practical Resilience** - Remove consistently slow engines
6. **Sustainable Maintenance** - Fewer, well-maintained engines > many broken ones

---

## Tier 1: Essential Independent Indexes

### Brave Search ⭐⭐⭐⭐⭐

**Why:** 
- Independent web index (not Google/Bing dependent)
- Strong free tier (unlimited API access with key)
- Excellent coverage and relevance
- Fast, reliable

**Configuration:**
```yaml
- name: brave
  disabled: false
  timeout: 8
  engine: brave
  # Requires free API key from https://api.search.brave.com/
```

**Coverage:** General web search (reduces Google/Bing dependency)

---

### Mojeek ⭐⭐⭐⭐⭐

**Why:**
- Independent crawler with own index
- Different ranking philosophy than Google
- Finds obscure/niche content Google misses
- Privacy-focused

**Configuration:**
```yaml
- name: mojeek
  disabled: false
  timeout: 10
  engine: mojeek
```

**Coverage:** Niche content, independent perspective

---

### Marginalia Search ⭐⭐⭐⭐☆

**Why:**
- Specialized for finding small/indie websites
- Excellent for niche content, blogs, technical sites
- Independent index

**Configuration:**
```yaml
- name: marginalia
  disabled: false
  timeout: 12  # Slower, but worthwhile
  engine: bing  # Uses Bing as fallback until Marginalia adds API
```

**Note:** Need to wait for official Marginalia SearXNG integration

**Coverage:** Small websites, indie content, niche topics

---

## Tier 2: Regional/Language Engines

### Chinese Content (Priority)

#### Baidu ⭐⭐⭐⭐☆
```yaml
- name: baidu
  disabled: false
  timeout: 10
  language: zh
  # Important: Requires Chinese user-agent
```

#### Sogou ⭐⭐⭐⭐☆
```yaml
- name: sogou
  disabled: false
  timeout: 10
  language: zh
```

**Why both?** Different ranking algorithms, complementary results

---

### Russian / Eastern Europe

#### Yandex ⭐⭐⭐⭐☆
```yaml
- name: yandex
  disabled: false
  timeout: 8
  language: ru
  # Strong for Russian content, Eastern Europe
```

**Coverage:** Russian, Ukrainian, Belarusian content

---

### Asian Regional

#### Naver (Korean) ⭐⭐⭐⭐☆
```yaml
- name: naver
  disabled: false
  timeout: 10
  language: ko
```

#### Daum (Korean)
```yaml
- name: daum
  disabled: false
  timeout: 10
  language: ko
```

#### Yahoo! Japan
```yaml
- name: yahoo_jp
  disabled: false
  timeout: 10
  language: ja
```

#### Goo (Japanese)
```yaml
- name: goo
  disabled: false
  timeout: 10
  language: ja
```

---

## Tier 3: Privacy/Alternative Engines

### Startpage ⭐⭐⭐⭐☆
```yaml
- name: startpage
  disabled: false
  timeout: 8
  # Privacy-focused, excellent results
```

### Qwant ⭐⭐⭐⭐☆
```yaml
- name: qwant
  disabled: false
  timeout: 8
  # European, privacy-focused
```

### Swisscows ⭐⭐⭐☆☆
```yaml
- name: swisscows
  disabled: false
  timeout: 10
  # Swiss privacy-focused
```

### MetaGer ⭐⭐⭐☆☆
```yaml
- name: metager
  disabled: false
  timeout: 10
  # German privacy engine
```

### Ecosia ⭐⭐⭐☆☆
```yaml
- name: ecosia
  disabled: false
  timeout: 10
  # Privacy + environmental focus
```

---

## Tier 4: Specialized Search

### Developer/Technical

#### GitHub ⭐⭐⭐⭐⭐
```yaml
- name: github
  disabled: false
  timeout: 8
  categories: source code
```

#### Stack Overflow ⭐⭐⭐⭐⭐
```yaml
- name: stackoverflow
  disabled: false
  timeout: 8
  categories: qa
```

#### SourceHut (Alternative git host)
```yaml
- name: sourcehut
  disabled: false
  timeout: 10
  # Open-source alternative to GitHub
```

#### Codeberg (Alternative git host)
```yaml
- name: codeberg
  disabled: false
  timeout: 10
  # Privacy-focused Git hosting
```

#### Package Registries

```yaml
- name: npm
  disabled: false
  timeout: 8
  categories: packages
  # Node.js packages

- name: pypi
  disabled: false
  timeout: 8
  categories: packages
  # Python packages

- name: crates
  disabled: false
  timeout: 8
  categories: packages
  # Rust packages

- name: docker
  disabled: false
  timeout: 10
  categories: packages
  # Docker images
```

---

### Academic/Research

#### Semantic Scholar ⭐⭐⭐⭐⭐
```yaml
- name: semantic_scholar
  disabled: false
  timeout: 10
  categories: academic
  # AI-powered academic search
```

#### OpenAlex ⭐⭐⭐⭐☆
```yaml
- name: openalex
  disabled: false
  timeout: 10
  categories: academic
  # Free open metadata on research
```

#### arXiv ⭐⭐⭐⭐☆
```yaml
- name: arxiv
  disabled: false
  timeout: 10
  categories: academic
  # Preprints and papers
```

#### Crossref ⭐⭐⭐⭐☆
```yaml
- name: crossref
  disabled: false
  timeout: 10
  categories: academic
  # DOI metadata
```

---

### Company/Business Discovery

#### OpenCorporates ⭐⭐⭐⭐⭐
```yaml
- name: opencorporates
  disabled: false
  timeout: 10
  categories: business
  # Global company information
  # IMPORTANT: May require rate limiting
```

#### Wikidata ⭐⭐⭐⭐☆
```yaml
- name: wikidata
  disabled: false
  timeout: 8
  categories: reference
  # Structured company data
```

#### Crunchbase ⭐⭐⭐⭐☆
```yaml
- name: crunchbase
  disabled: false
  timeout: 15
  categories: business
  # Note: Requires monitoring for access restrictions
```

#### Common Crawl ⭐⭐⭐⭐☆
```yaml
- name: commoncrawl
  disabled: false
  timeout: 20  # Can be slow
  categories: index
  # Historical web snapshots
```

#### Internet Archive / Wayback Machine ⭐⭐⭐⭐⭐
```yaml
- name: wayback_machine
  disabled: false
  timeout: 15
  categories: archive
  engine: bing  # Falls back to archive.org API
  # Search archived versions of websites
  # Useful for: Dead links, historical research, version tracking
  
# Alternative: Direct Wayback Machine API
- name: archive_org
  disabled: false
  timeout: 20
  categories: archive
  # Direct Internet Archive search
  # Better for finding specific snapshots
```

**Why Include Wayback Machine:**
- ✅ Recover content from deleted/changed websites
- ✅ Historical research and version tracking
- ✅ Find working versions of dead links
- ✅ Track domain history
- ✅ Access old documentation and resources
- ✅ Verify claim changes over time
- ✅ 30+ billion web pages archived since 1996

**API Details:**
- Endpoint: `https://archive.org/advancedsearch.php`
- Search syntax: `url:example.com` for all snapshots of domain
- Rate limit: Generous (no aggressive blocking)
- No authentication required
- Cache policy: Historical data, changes rarely

**Example Queries:**
```
web.archive.org snapshots of google.com in 2010
old version of wikipedia homepage 2005
internet archive search results for deleted page
wayback machine historical snapshots domain tracking
```

---

### Images & Media

#### Wikimedia Commons ⭐⭐⭐⭐⭐
```yaml
- name: wikimedia_commons
  disabled: false
  timeout: 8
  categories: images
  # Free licensed media
```

#### Flickr ⭐⭐⭐⭐☆
```yaml
- name: flickr
  disabled: false
  timeout: 10
  categories: images
  # Creative Commons licensed images
```

---

## Tier 5: Standard (With Caution)

### Google ⭐⭐⭐⭐⭐ (But with rate limiting)
```yaml
- name: google
  disabled: false
  timeout: 10
  rate_limit: 0.5  # Conservative rate limit
```

**Caution:** Subject to blocking/rate limits. Use with monitoring.

### Bing ⭐⭐⭐⭐☆ (Fallback)
```yaml
- name: bing
  disabled: false
  timeout: 8
```

**Caution:** Different results than Google, good as secondary source.

### DuckDuckGo ⭐⭐⭐☆☆ (Privacy wrapper)
```yaml
- name: duckduckgo
  disabled: false
  timeout: 8
```

**Note:** DDG is mostly Google results with privacy wrapper. Lower priority than alternatives.

---

## Engines to SKIP

**Don't enable just for the sake of it:**

- ❌ **Yahoo** - Uses Bing backend anyway
- ❌ **Ask.com** - Minimal independent index
- ❌ **AOL Search** - Uses Bing
- ❌ **Multiple Bing clones** - Redundant
- ❌ **Free public proxies** - Unreliable
- ❌ **Regional Google clones** - Same results, different packaging
- ❌ **Deprecated engines** - Often broken, slow

---

## Recommended Production Configuration

**Total Engines: ~35-40 (not 100+)**

### By Category Count

```
Independent indexes: 3 (Brave, Mojeek, Marginalia)
Regional/Language: 8 (Baidu, Sogou, Yandex, Naver, Daum, Yahoo JP, Goo, etc.)
Privacy engines: 5 (Startpage, Qwant, Swisscows, MetaGer, Ecosia)
Developer: 8 (GitHub, SO, SourceHut, Codeberg, npm, PyPI, crates, Docker)
Academic: 4 (Semantic Scholar, OpenAlex, arXiv, Crossref)
Company: 4 (OpenCorporates, Wikidata, Common Crawl, Internet Archive)
Media: 2 (Wikimedia, Flickr)
Standard (monitored): 2-3 (Google, Bing, maybe DDG)
───────────────────────
Total: 35-40 engines
```

### Rationale

- **35-40** provides excellent coverage without maintenance burden
- **Independent indexes** reduce single-point-of-failure risks
- **Regional engines** handle non-English content naturally
- **Specialized search** covers distinct use cases
- **Monitored standard** engines for when all else fails

---

## Performance Optimization Strategy

### HTTP/2 & HTTP/3
```yaml
# Enable in SearXNG config
use_http2: true
use_http3: true
```

### Brotli Compression
```yaml
# Enable response compression
compression: brotli
```

### Asynchronous Workers
```yaml
# Increase worker count for parallel requests
async_workers: 16  # Depends on available CPU
```

### Per-Engine Timeout Tuning

```yaml
# Fast engines (responsive, reliable)
fast_engines:
  - github
  - npm
  - pypi
  timeout: 5

# Medium engines (typically responsive)
medium_engines:
  - google
  - bing
  - brave
  timeout: 8

# Slow engines (need patience)
slow_engines:
  - common_crawl
  - internet_archive
  - marginalia
  timeout: 15-20
```

### Connection Pooling
```yaml
# Reuse connections to reduce overhead
connection_pool_size: 100
connection_pool_timeout: 30
```

### Response Caching
```yaml
# Cache results for repeated queries
cache:
  default_ttl: 300
  
result_cache:
  expiration_time: 86400
```

### Health Checks
```yaml
# Automatically disable failing engines
health_check:
  interval: 3600  # Check every hour
  max_failures: 3
  auto_disable: true
```

---

## Comprehensive Proxy Strategy

### Tier 1: Recommended (Production)
- ✅ **Cloudflare WARP** - Low latency, easy deployment, reliable
- ✅ **SOCKS5 rotating proxies** - Better engine resistance than HTTP
- ✅ **Residential rotating proxies** - Highest success rate
- ✅ **ISP/static residential proxies** - Consistent, reliable
- ✅ **Mobile (4G/5G) rotating proxies** - Hardest to block
- ✅ **Datacenter proxies (premium)** - Speed + reliability balance

### Tier 2: Geo-Unblocking
- ✅ **Country-specific exit nodes** - CN, RU, KR, JP, DE, US
- ✅ **Multi-region proxy pools** - Global coverage
- ✅ **GeoDNS-aware proxies** - Location-aware routing
- ✅ **ASN-targeted proxies** - Different ISP networks

### Tier 3: Privacy & Anti-Rate-Limit
- ✅ **Tor SOCKS5** - IP-rate-limited engines
- ✅ **Tor bridges** (obfs4, Snowflake) - Tor unblocking
- ✅ **Shadowsocks** - Lightweight encryption
- ✅ **V2Ray / Xray** - Configurable protocols
- ✅ **WireGuard tunnels** - Modern VPN
- ✅ **OpenVPN gateways** - Mature, reliable

### Tier 4: Cloud-Based
- ✅ **Cloudflare Tunnel** - Secure SearXNG exposure
- ✅ **Tailscale Exit Nodes** - Mesh VPN
- ✅ **Headscale + Tailscale mesh** - Self-hosted mesh
- ✅ **Self-hosted VPS proxy fleet** - Complete control
- ✅ **Kubernetes egress gateways** - Enterprise scale

### Tier 5: Enterprise Providers
- ✅ **Bright Data** - Premium residential
- ✅ **Oxylabs** - High-performance
- ✅ **NetNut** - Sticky sessions
- ✅ **SOAX** - Global coverage
- ✅ **Smartproxy** - Cost-effective
- ✅ **Webshare** - Budget option
- ✅ **IPRoyal** - Rotating options
- ✅ **Rayobyte** - Datacenter + residential
- ✅ **PacketStream** - Peer-to-peer
- ✅ **ProxyRack** - Flexible plans

### Tier 6: Advanced Features
- ✅ **Proxy chaining** - Multi-layer proxies
- ✅ **Automatic proxy health checks** - Continuous monitoring
- ✅ **Per-engine proxy assignment** - Optimal routing
- ✅ **Automatic proxy rotation** - Dynamic switching
- ✅ **Latency-aware proxy selection** - Smart routing
- ✅ **Failure-based failover** - Redundancy
- ✅ **Sticky sessions** - Connection persistence
- ✅ **Weighted load balancing** - Capacity management

### ❌ DO NOT Use:
- ❌ **Free public proxies** - Slow, unreliable, blocked
- ❌ **Simple HTTP proxies** - Easily detected
- ❌ **Single fixed proxy** - Obvious fingerprint

---

## Engine-Specific Proxy Routing (Recommended)

**Key insight:** Different engines need different strategies

```yaml
# Geo-targeted routing by region
baidu:
  proxies:
    - china_residential_proxy_1
    - china_residential_proxy_2
  failover: tor_socks5
  sticky: true  # Maintain IP for session

sogou:
  proxies: baidu_proxies  # Same pool
  
yandex:
  proxies:
    - russia_residential_proxy
    - eastern_europe_proxy
  failover: tor_socks5
  
naver:
  proxies:
    - korea_residential_proxy
  failover: asia_warp
  
yahoo_japan:
  proxies:
    - japan_residential_proxy
  failover: asia_warp
  
# Rate-limited high-value engines
google:
  proxies:
    - mobile_rotating_pool_1
    - mobile_rotating_pool_2
    - mobile_rotating_pool_3
  rotation: aggressive  # Rotate per request
  failover: residential_fallback
  
bing:
  proxies:
    - cloudflare_warp
    - residential_rotating
  rotation: per_query
  
# Independent indexes (lower risk)
brave:
  proxies: null  # Direct, no proxy needed
  
mojeek:
  proxies: null  # Direct, lower blocking rate
  
# Archive/Historical (no blocking)
wayback_machine:
  proxies: null  # Direct, excellent rate limits
  timeout: 20    # Searching archives takes longer
  
archive_org:
  proxies: null  # Direct, no proxy needed
  timeout: 20
  
# Specialized search
github:
  proxies: null  # Low rate limit
  
stackoverflow:
  proxies: null  # Developer-friendly
  
arxiv:
  proxies: null  # Academic, no blocking
  
# Privacy/Alternative
startpage:
  proxies: cloudflare_warp  # Optional for extra privacy
  
qwant:
  proxies: null  # No blocking issues
```

---

## Proxy Pool Manager Implementation

**Features for production SearXNG:**

```python
class ProxyManager:
    """Manages multi-tiered proxy strategy"""
    
    def __init__(self):
        self.proxy_pools = {
            'china_residential': ProxyPool(...),
            'russia_residential': ProxyPool(...),
            'korea_residential': ProxyPool(...),
            'mobile_rotating': ProxyPool(...),
            'cloudflare_warp': WarpConnector(),
            'tor_socks5': TorConnector(),
        }
        
    def get_proxy_for_engine(self, engine_name):
        """Select optimal proxy for engine"""
        engine_config = ENGINE_PROXY_MAP.get(engine_name)
        if not engine_config:
            return None  # Direct connection
        
        # Try proxies in priority order
        for proxy_pool_name in engine_config['proxies']:
            pool = self.proxy_pools[proxy_pool_name]
            proxy = pool.get_healthy_proxy()
            if proxy:
                return proxy
        
        # Failover
        return self.proxy_pools[engine_config['failover']].get_proxy()
    
    def health_check(self):
        """Monitor all proxy pools"""
        for pool in self.proxy_pools.values():
            pool.test_connections()
            
    def rotate_proxy(self, engine_name):
        """Rotate to next proxy"""
        pool = self.get_proxy_pool_for_engine(engine_name)
        return pool.get_next_proxy()
    
    def mark_failed(self, proxy, engine_name):
        """Track failing proxies"""
        pool = self.get_proxy_pool_for_engine(engine_name)
        pool.mark_failed(proxy)
        # Replace if too many failures
        if pool.failure_rate() > 0.2:
            pool.replace_proxies()
```

---

## Additional SearXNG Features

**Worth implementing for production deployment:**

1. **Proxy reputation scoring** - Track success rates per proxy
2. **Circuit breaker for bad proxies** - Disable failing proxies automatically
3. **CAPTCHA detection** - Identify when blocked, rotate proxy
4. **Exponential backoff** - Graceful retry strategy
5. **Health monitoring dashboard** - Visual proxy status
6. **Proxy usage metrics** - Track proxy performance
7. **Automatic proxy replacement** - Replace failing proxies
8. **Per-engine timeout tuning** - Based on proxy latency
9. **Connection pooling per proxy** - Reduce overhead
10. **Sticky session management** - Maintain IP for specific queries

---

## Implementation Priority

### Phase 1: Foundation (Immediate)
1. **Brave Search** - Independent index, no rate limiting
2. **GitHub + Stack Overflow** - Essential for developers
3. **Semantic Scholar + arXiv** - Academic excellence
4. **Internet Archive / Wayback Machine** ⭐ - Historical + dead links recovery
5. **OpenCorporates + Wikidata** - Company discovery
6. **Yandex + Baidu** - Critical regional coverage

**Result:** Core 16 engines, 85% of value

### Phase 2: Enhancement (Week 2)
1. **Mojeek** - Independent diversity
2. **Startpage + Qwant** - Privacy options
3. **Japanese + Korean** - Additional regional
4. **Developer packages** - npm, PyPI, crates
5. **Image search** - Wikimedia Commons

**Result:** Expand to 25-30 engines, add regional depth

### Phase 3: Optimization (Week 3-4)
1. **Proxy setup** - SOCKS5/Cloudflare WARP
2. **Performance tuning** - HTTP/2, caching, pooling
3. **Health checks** - Auto-disable failing engines
4. **Rate limit monitoring** - Track and adjust
5. **Marginalia integration** - When SearXNG plugin available

**Result:** 35-40 engines, production-hardened

### Phase 4: Monitoring (Ongoing)
1. **Weekly engine health checks**
2. **Monthly performance analysis**
3. **Quarterly update review**
4. **Remove consistently slow engines**
5. **Add new high-value engines as discovered**

---

## Expected Results

### Coverage
```
Before (naive approach):
  - 100+ engines, 60% working
  - Duplicate results from clones
  - Inconsistent quality
  
After (strategic approach):
  - 35-40 engines, 95%+ working
  - Diverse independent sources
  - Optimized for quality
```

### Performance
```
Response time improvements:
  - HTTP/2: +20% faster
  - Connection pooling: +15% faster
  - Response caching: +90% faster (cached queries)
  - Health checks: Eliminate slow engines
  
Goal: Sub-5 second responses for most queries
```

### Resilience
```
Independent indexes (Brave, Mojeek):
  - No Google/Bing dependency
  
Regional engines (Yandex, Baidu, Naver):
  - Handle non-English content natively
  
Specialized search (GitHub, Scholar, etc.):
  - Best-in-class for specific domains
  
Fallback layers:
  - If Brave fails → Mojeek
  - If primary regional fails → Alternative
```

### Maintainability
```
Fewer engines = easier maintenance
- 40 vs 100+ = 60% fewer rate limit issues
- Easier to monitor
- Faster to identify problems
- Sustainable long-term
```

---

## Configuration Template

```yaml
# Strategic SearXNG Configuration
# ~35-40 carefully selected engines

engines:
  # OFFLINE (No network dependency)
  - name: saudi_companies_db
    disabled: false
    
  # === TIER 1: INDEPENDENT INDEXES ===
  - name: brave
    disabled: false
    timeout: 8
    
  - name: mojeek
    disabled: false
    timeout: 10
    
  # === TIER 2: REGIONAL/LANGUAGE ===
  - name: baidu
    disabled: false
    timeout: 10
    language: zh
    
  - name: sogou
    disabled: false
    timeout: 10
    language: zh
    
  - name: yandex
    disabled: false
    timeout: 8
    language: ru
    
  - name: naver
    disabled: false
    timeout: 10
    language: ko
    
  # ... (continue with selection from above)
  
  # === TIER 3: PRIVACY ===
  - name: startpage
    disabled: false
    timeout: 8
    
  # === TIER 4: SPECIALIZED ===
  - name: github
    disabled: false
    timeout: 8
    
  - name: stackoverflow
    disabled: false
    timeout: 8
    
  - name: semantic_scholar
    disabled: false
    timeout: 10
    
  - name: opencorporates
    disabled: false
    timeout: 10
    
  # === TIER 5: STANDARD (with limits) ===
  - name: google
    disabled: false
    timeout: 10
    rate_limit: 0.5
    
  - name: bing
    disabled: false
    timeout: 8

# Performance optimization
outgoing:
  use_http2: true
  use_http3: true
  compression: brotli
  request_timeout: 10
  max_request_timeout: 20
  connection_pool_size: 100
```

---

## Success Metrics

After implementing:

1. ✅ **Coverage**: Can find English, Chinese, Russian, Korean, Japanese content
2. ✅ **Quality**: Results are diverse, from independent sources
3. ✅ **Speed**: <5 seconds for 95% of queries
4. ✅ **Reliability**: 95%+ engine uptime
5. ✅ **Maintainability**: Single engineer can maintain indefinitely
6. ✅ **Resilience**: No single-source dependencies (no Google-only fallback)

---

## Conclusion

**This strategic approach is vastly superior to "enable everything":**

- **Better coverage** through diversity, not quantity
- **Better performance** through optimization, not bloat
- **Better maintainability** through careful selection
- **Better resilience** through independent sources
- **Better results** for users through quality curation

**Focus on depth, not breadth.**
