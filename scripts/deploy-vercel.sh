#!/usr/bin/env bash
set -e

echo "============================================"
echo "  DClaw Crisis — Vercel Deployment Script"
echo "============================================"
echo ""

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: Run this script from the frontend/ directory"
    exit 1
fi

# Check if vercel CLI is available
if ! command -v npx &> /dev/null; then
    echo "❌ Error: npx is not available. Install Node.js first."
    exit 1
fi

echo "1️⃣  Checking Vercel CLI..."
npx vercel --version

echo ""
echo "2️⃣  Checking login status..."
if npx vercel whoami &> /dev/null; then
    echo "✅ Already logged in as: $(npx vercel whoami 2>/dev/null)"
else
    echo "🔐 You need to log in to Vercel first."
    echo "   Running: npx vercel login"
    npx vercel login
fi

echo ""
echo "3️⃣  Linking project..."
npx vercel link --yes

echo ""
echo "4️⃣  Building..."
npx vercel build

echo ""
echo "5️⃣  Deploying..."
npx vercel --prod

echo ""
echo "============================================"
echo "  ✅ Deployment complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo "  1. Set NEXT_PUBLIC_API_URL in Vercel dashboard"
echo "  2. Deploy your backend (Railway/Render/Fly)"
echo "  3. Update CORS origins in backend for production"
echo ""
