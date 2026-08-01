/** @type {import('next').NextConfig} */
const path = require('path');
const rootPkg = require(path.join(__dirname, '..', 'package.json'));

const nextConfig = {
  output: 'export',
  distDir: 'out',
  images: { unoptimized: true },
  env: {
    APP_VERSION: rootPkg.version,
  },
};

module.exports = nextConfig;
