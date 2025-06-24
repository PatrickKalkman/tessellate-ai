/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  images: {
    unoptimized: true,
  },
  basePath: '',
  trailingSlash: true,
  webpack: (config, { isServer }) => {
    if (!isServer) {
      // Client-side configuration
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        path: false,
        canvas: false,
      };
    } else {
      // Server-side configuration - externalize canvas
      config.externals = [...(config.externals || []), 'canvas'];
    }
    
    return config;
  },
}

module.exports = nextConfig