import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"

import { Input } from "@/components/ui/input"

describe("Input", () => {
  it("forwards standard input props", () => {
    render(<Input aria-label="Email" defaultValue="x@example.com" />)
    expect(screen.getByLabelText("Email")).toHaveValue("x@example.com")
  })
})
