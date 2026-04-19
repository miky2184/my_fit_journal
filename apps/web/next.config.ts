import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  transpilePackages: ['@mfj/types', '@mfj/validators'],
}

export default nextConfig
