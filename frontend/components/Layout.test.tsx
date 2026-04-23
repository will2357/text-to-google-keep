import { render, screen } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"

import Layout from "@/components/Layout"

const pageProps = { oauth_ready: true }

vi.mock("@inertiajs/react", () => ({
  Link: ({ href, className, children }: any) => (
    <a href={href} className={className}>
      {children}
    </a>
  ),
  usePage: () => ({ props: pageProps }),
}))

describe("Layout", () => {
  it("renders nav, children, and oauth button", () => {
    pageProps.oauth_ready = true
    render(
      <Layout>
        <div>Child content</div>
      </Layout>,
    )
    expect(screen.getByText("text-to-google-keep")).toBeInTheDocument()
    expect(screen.getByText("Child content")).toBeInTheDocument()
    expect(screen.getByRole("link", { name: "Sign in with Google" })).toHaveAttribute("href", "/oauth/start/")
  })

  it("hides oauth button when not ready", () => {
    pageProps.oauth_ready = false
    render(
      <Layout>
        <div>Child content</div>
      </Layout>,
    )
    expect(screen.queryByRole("link", { name: "Sign in with Google" })).not.toBeInTheDocument()
  })
})
