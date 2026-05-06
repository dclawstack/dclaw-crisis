# Troubleshooting

Common issues and solutions for DClaw Crisis.

## Quick Diagnostics

```bash
# Check app pods
kubectl get pods -n dclaw-crisis

# Check logs
kubectl logs -n dclaw-crisis deployment/dclaw-crisis-backend

# Check database
kubectl get clusters -n dclaw-crisis
```

## Sections

- [Common Issues](./common-issues)
- [FAQ](./faq)
