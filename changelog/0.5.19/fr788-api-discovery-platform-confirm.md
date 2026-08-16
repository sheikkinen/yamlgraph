---
type: feat
scope: examples
req: REQ-YG-589
---
- **FR-788 API Discovery Platform-Confirm Step**: Agent graph that confirms platform family candidates (CKAN, PxWeb, OData, OpenAPI, WordPress REST, JSON-stat) against family-specific substance predicates via the shared `curl_probe` tool — proving real data was returned, not just a 200 status — returning exactly one `PlatformConfirmation` result. Live positive smoke against CKAN's public demo (`demo.ckan.org`) and negative smoke against `example.com` both verified. (REQ-YG-589)
