import type { NextConfig } from "next"
import { fileURLToPath } from "node:url"
import { dirname } from "node:path"

const __dirname = dirname(fileURLToPath(import.meta.url))

const config: NextConfig = {
  reactStrictMode: true,
  output: "standalone",
  // Explicitly root file tracing at this package. The repo also contains
  // sibling packages (e.g. /backend) with their own lockfiles; pinning the
  // root here keeps the Docker build context self-contained to /frontend and
  // yields a standalone server.js at the root of the trace tree.
  outputFileTracingRoot: __dirname,
}

export default config
