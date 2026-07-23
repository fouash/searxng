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

#### Internet Archive ⭐⭐⭐⭐☆
```yaml
- name: wayback_machine
  disabled: false
  timeout: 15
  categories: archive
  # Historical website versions
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

## Proxy Strategy

### DO Use:
- ✅ **Cloudflare WARP** - Low latency, easy to deploy
- ✅ **SOCKS5 rotating** - Better than HTTP for engine resistance
- ✅ **Residential proxies** (paid) - Highest success rate
- ✅ **Tor SOCKS5** - Good for IP-rate-limited engines

### DON'T Use:
- ❌ **Free public proxies** - Slow, unreliable, blocked
- ❌ **Simple HTTP proxies** - Easily detected and blocked
- ❌ **Single fixed proxy** - Obvious fingerprint

### Recommended Setup:
```
Per-engine proxy assignment:

High-risk engines (rate limited):
  - Google → SOCKS5 rotating
  - Bing → Cloudflare WARP
  
Independent indexes (lower risk):
  - Brave → Direct (no proxy needed)
  - Mojeek → Direct
  
Regional engines:
  - Baidu → SOCKS5 China-based
  - Yandex → Direct or Tor
```

---

## Implementation Priority

### Phase 1: Foundation (Immediate)
1. **Brave Search** - Independent index, no rate limiting
2. **GitHub + Stack Overflow** - Essential for developers
3. **Semantic Scholar + arXiv** - Academic excellence
4. **OpenCorporates + Wikidata** - Company discovery
5. **Yandex + Baidu** - Critical regional coverage

**Result:** Core 15 engines, 80% of value

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
