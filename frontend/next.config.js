/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "https://ismat110-ai-employee-vault-ismat-platinum.hf.space",
  },
};

module.exports = nextConfig;
