# Remote Source Fetching Security

Remote IIIF/image ingestion is an SSRF boundary.

Production requirements:
1. Accept only HTTP/HTTPS.
2. Resolve DNS in a controlled fetch service.
3. Reject private, loopback, link-local, multicast, reserved and metadata-service ranges before and after redirects.
4. Limit redirects, response size, content type and time.
5. Prefer institution/domain allowlists for automated ingestion.
6. Never send application credentials or internal headers to source hosts.
7. Record the final source URI and checksum in provenance.
8. Treat SVG/XML as untrusted input and parse with hardened settings where applicable.
