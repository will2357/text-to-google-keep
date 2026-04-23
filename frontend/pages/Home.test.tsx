import { fireEvent, render, screen } from "@testing-library/react"
import { beforeEach, describe, expect, it, vi } from "vitest"

import Home from "@/pages/Home"

const setData = vi.fn()
const post = vi.fn()
const formState = {
  processing: false,
}

vi.mock("@inertiajs/react", () => ({
  Head: ({ title }: { title: string }) => <span data-testid="head">{title}</span>,
  useForm: () => ({
    data: {
      email: "",
      content: "",
      password: "",
      master_token: "",
      labels: "",
      use_oauth: false,
      reset: false,
      blank_lines: false,
      file: null,
    },
    processing: formState.processing,
    setData,
    post,
  }),
}))

describe("Home page", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("shows processing label when submitting", () => {
    formState.processing = true
    render(<Home flash={[]} oauth_ready={true} />)
    expect(screen.getByRole("button", { name: "Importing…" })).toBeDisabled()
    formState.processing = false
  })

  it("renders flash messages and oauth warning", () => {
    render(
      <Home
        flash={[
          { level: "error", text: "bad" },
          { level: "success", text: "ok" },
        ]}
        oauth_ready={false}
      />,
    )
    expect(screen.getByText("bad")).toBeInTheDocument()
    expect(screen.getByText("ok")).toBeInTheDocument()
    expect(screen.getByText(/GOOGLE_KEEP_CLIENT_SECRETS/)).toBeInTheDocument()
  })

  it("posts form submit and updates checkbox fields", () => {
    render(<Home flash={[]} oauth_ready={true} />)
    fireEvent.click(screen.getByLabelText(/Use Google OAuth/))
    expect(setData).toHaveBeenCalledWith("use_oauth", true)
    fireEvent.change(screen.getByLabelText("Email"), { target: { value: "you@example.com" } })
    expect(setData).toHaveBeenCalledWith("email", "you@example.com")
    fireEvent.change(screen.getByLabelText(/Password or app password/), { target: { value: "pw" } })
    expect(setData).toHaveBeenCalledWith("password", "pw")
    fireEvent.change(screen.getByLabelText(/Master token/), { target: { value: "tok" } })
    expect(setData).toHaveBeenCalledWith("master_token", "tok")
    fireEvent.change(screen.getByLabelText(/Lines to import/), { target: { value: "line1" } })
    expect(setData).toHaveBeenCalledWith("content", "line1")
    fireEvent.change(screen.getByLabelText(/Labels/), { target: { value: "A,B" } })
    expect(setData).toHaveBeenCalledWith("labels", "A,B")
    fireEvent.click(screen.getByLabelText(/Clear saved token/))
    expect(setData).toHaveBeenCalledWith("reset", true)
    fireEvent.click(screen.getByLabelText(/Import blank lines/))
    expect(setData).toHaveBeenCalledWith("blank_lines", true)
    const fileInput = screen.getByLabelText(/Or UTF-8 file/) as HTMLInputElement
    const file = new File(["hello"], "a.txt", { type: "text/plain" })
    fireEvent.change(fileInput, { target: { files: [file] } })
    expect(setData).toHaveBeenCalledWith("file", file)
    const form = document.querySelector("form")
    expect(form).toBeTruthy()
    fireEvent.submit(form!)
    expect(post).toHaveBeenCalledWith("/import/", { forceFormData: true, preserveScroll: true })
  })
})
