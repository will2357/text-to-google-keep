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

function loadInitialPage() {
  const fallback = {
    component: "Home",
    props: { flash: [], oauth_ready: false, errors: {} },
    url: window.location.pathname,
    version: null,
    encryptHistory: false,
    clearHistory: false,
  }
  const root = document.getElementById("app")
  if (!root) return fallback
  const raw = root?.getAttribute("data-page")
  if (raw) {
    try {
      const parsed = JSON.parse(raw) as Record<string, unknown>
      if (parsed && typeof parsed.component === "string") {
        return parsed
      }
    } catch {
      // Fall through to default page payload.
    }
  }
  root.setAttribute("data-page", JSON.stringify(fallback))
  return fallback
}

function renderBootError(message: string) {
  const root = document.getElementById("app")
  if (!root) return
  root.innerHTML = ""
  const box = document.createElement("pre")
  box.textContent = `App failed to start:\n\n${message}`
  box.style.whiteSpace = "pre-wrap"
  box.style.fontFamily = "ui-monospace, SFMono-Regular, Menlo, monospace"
  box.style.padding = "1rem"
  box.style.margin = "1rem"
  box.style.borderRadius = "0.5rem"
  box.style.background = "#2a0f14"
  box.style.color = "#ffd7df"
  box.style.border = "1px solid #5f1f2a"
  root.appendChild(box)
}

window.addEventListener("error", (event) => {
  if (event.error instanceof Error) {
    renderBootError(event.error.stack ?? event.error.message)
  } else if (event.message) {
    renderBootError(String(event.message))
  }
})

window.addEventListener("unhandledrejection", (event) => {
  const reason = event.reason
  if (reason instanceof Error) {
    renderBootError(reason.stack ?? reason.message)
  } else {
    renderBootError(String(reason))
  }
})

createInertiaApp({
  page: loadInitialPage() as any,
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
}).catch((error) => {
  if (error instanceof Error) {
    renderBootError(error.stack ?? error.message)
  } else {
    renderBootError(String(error))
  }
})
