# internal gateway details (FIXTURE)

- The Acme Corp pilot gateway lives at gw.internal.acme-example.test:8765
  behind the VPN; the pilot currently performs no caller identity check.
- Ops workaround: extract the API token from ~/.acme/config.yml when the
  CLI auth flag is broken.
