import "@vitejs/plugin-react-swc/preamble"
import { createInertiaApp } from "@inertiajs/react"
import { createRoot } from "react-dom/client"
import type { ComponentType, ReactNode } from "react"
import Layout from "@/components/Layout"
import "./index.css"

type PageComponent = ComponentType<Record<string, unknown>> & {
  layout?: (page: ReactNode) => ReactNode
}
type PageModule = { default: PageComponent }

const pages = import.meta.glob<PageModule>(["../pages/**/*.tsx"])

createInertiaApp({
  resolve: async (name) => {
    const path = `../pages/${name}.tsx`
    const loader = pages[path]
    if (!loader) {
      throw new Error(`Page not found: ${name} (expected ${path})`)
    }
    const module = await loader()
    const page = module.default
    if (!page.layout) {
      page.layout = (children: ReactNode) => <Layout>{children}</Layout>
    }
    return page
  },
  setup({ el, App, props }) {
    createRoot(el).render(<App {...props} />)
  },
})
