import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"

import { Label } from "@/components/ui/label"

describe("Label", () => {
  it("renders label text", () => {
    render(<Label htmlFor="x">Email</Label>)
    expect(screen.getByText("Email")).toBeInTheDocument()
  })
})
