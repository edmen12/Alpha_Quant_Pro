import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'export',
  // API Proxy for development mode (npm run dev)
  // Note: rewrites only work in dev mode, not in static export
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ];
  },
};

export default nextConfig;
