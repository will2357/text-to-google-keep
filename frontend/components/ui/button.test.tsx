import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"

import { Button } from "@/components/ui/button"

describe("Button", () => {
  it("renders default button", () => {
    render(<Button>Save</Button>)
    expect(screen.getByRole("button", { name: "Save" })).toBeInTheDocument()
  })

  it("renders as child when requested", () => {
    render(
      <Button asChild>
        <a href="/x">Go</a>
      </Button>,
    )
    expect(screen.getByRole("link", { name: "Go" })).toHaveAttribute("href", "/x")
  })
})
