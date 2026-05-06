# Installation

## Via DPanel

1. Open DPanel at `https://panel.yourdomain.com`
2. Find **DClaw Crisis** in the app grid
3. Click **Install**
4. The DClaw Operator will provision:
   - Namespace: `dclaw-crisis`
   - Frontend deployment (Next.js)
   - Backend deployment (FastAPI)
   - PostgreSQL database (CloudNativePG)
   - Ingress with TLS

## Via kubectl

```bash
# Apply the DClawApp CRD
kubectl apply -f - <<EOF
apiVersion: platform.dclaw.io/v1
kind: DClawApp
metadata:
  name: crisis
spec:
  appId: crisis
  appName: DClaw Crisis
  version: 0.1.0
  category: operations
  enabled: true
  frontend:
    image: ghcr.io/dclawstack/dclaw-crisis:latest
    replicas: 2
  backend:
    image: ghcr.io/dclawstack/dclaw-crisis-backend:latest
    replicas: 2
  database:
    enabled: true
    storage: 10Gi
  ingress:
    enabled: true
    host: crisis.yourdomain.com
    tls: true
EOF
```

## Verify

```bash
kubectl get pods -n dclaw-crisis
kubectl get ingress -n dclaw-crisis
```
