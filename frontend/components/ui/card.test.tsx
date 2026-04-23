import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"

import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"

describe("Card", () => {
  it("renders title, description, and content", () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Header</CardTitle>
          <CardDescription>Desc</CardDescription>
        </CardHeader>
        <CardContent>Body</CardContent>
        <CardFooter>Footer</CardFooter>
      </Card>,
    )
    expect(screen.getByText("Header")).toBeInTheDocument()
    expect(screen.getByText("Desc")).toBeInTheDocument()
    expect(screen.getByText("Body")).toBeInTheDocument()
    expect(screen.getByText("Footer")).toBeInTheDocument()
  })
})
