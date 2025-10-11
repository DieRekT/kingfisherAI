/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "images.unsplash.com" },
      { protocol: "https", hostname: "source.unsplash.com" },
      { protocol: "https", hostname: "upload.wikimedia.org" },
      { protocol: "https", hostname: "cdn.pixabay.com" },
    ],
  },
  webpack: (config, { isServer }) => {
    // Handle .node files for LanceDB native bindings
    config.externals = config.externals || [];
    if (isServer) {
      config.externals.push({
        '@lancedb/lancedb': 'commonjs @lancedb/lancedb',
      });
    }

    // Ignore .node files during build
    config.module = config.module || {};
    config.module.rules = config.module.rules || [];
    config.module.rules.push({
      test: /\.node$/,
      use: 'node-loader',
    });

    // Add fallback for node modules
    config.resolve.fallback = {
      ...config.resolve.fallback,
      fs: false,
      net: false,
      tls: false,
    };

    return config;
  },
};

module.exports = nextConfig;

