---
type: feat
scope: examples
req: REQ-YG-587
---
- **FR-786 API Discovery Page-Analysis Step**: Agent graph that inspects HTML page source via the shared `fetch_page` tool, extracting embedded API URLs (script bodies, `data-api-url` attributes, explicit paths) and fingerprinting platforms (CKAN, PxWeb, SwaggerUI, OData, Liferay, JSF, WordPress REST, EntryScape) from a `data_files`-backed catalog, distinguishing API-bearing portal pages from SPA shells requiring browser-sniff. (REQ-YG-587)
