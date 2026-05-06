/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://dclaw-crisis-backend:8137/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
