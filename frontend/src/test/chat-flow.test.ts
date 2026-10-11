import { describe, expect, it, vi, beforeEach } from "vitest";
import { api, ApiError } from "@/services/api";
import type { ModelSelection } from "@/types/assistant";

describe("Chat Flow and API sendMessage", () => {
  const model: ModelSelection = {
    provider: "ollama",
    name: "llama3",
    label: "Llama 3",
    contextWindow: 8192,
  };

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("sends conversation_id: null when sessionId is not a valid UUID", async () => {
    let capturedBody: Record<string, unknown> | null = null;

    global.fetch = vi.fn().mockImplementation(async (_url: string, init?: RequestInit) => {
      capturedBody = JSON.parse(init?.body as string);
      return {
        ok: true,
        json: async () => ({
          conversation_id: "e9f02909-7d04-4bfe-98cb-d18d45ba1db2",
          message_id: "msg-123",
          response: "Growth reply",
          citations: [],
          artifacts: [],
        }),
      } as unknown as Response;
    });

    const result = await api.sendMessage({
      sessionId: "temporary-id-123",
      content: "How do I calculate retention?",
      history: [],
      model,
    });

    expect(capturedBody).not.toBeNull();
    expect(capturedBody?.conversation_id).toBeNull();
    expect(capturedBody?.message).toBe("How do I calculate retention?");
    expect(capturedBody?.provider).toBe("local");
    expect(result.conversationId).toBe("e9f02909-7d04-4bfe-98cb-d18d45ba1db2");
  });

  it("preserves conversation_id when sessionId is a valid UUID", async () => {
    let capturedBody: Record<string, unknown> | null = null;
    const existingUuid = "a1b2c3d4-e5f6-4a1b-8c2d-3e4f5a6b7c8d";

    global.fetch = vi.fn().mockImplementation(async (_url: string, init?: RequestInit) => {
      capturedBody = JSON.parse(init?.body as string);
      return {
        ok: true,
        json: async () => ({
          conversation_id: existingUuid,
          message_id: "msg-456",
          response: "Followup answer",
          citations: [
            {
              episode_title: "Elena Verna on B2B Growth",
              speaker: "Elena Verna",
              timestamp: "12:34",
            },
          ],
          artifacts: [],
        }),
      } as unknown as Response;
    });

    const result = await api.sendMessage({
      sessionId: existingUuid,
      content: "Tell me more about product-led sales",
      history: [],
      model,
    });

    expect(capturedBody?.conversation_id).toBe(existingUuid);
    expect(result.sources).toHaveLength(1);
    expect(result.sources[0]?.title).toBe("Elena Verna on B2B Growth");
    expect(result.sources[0]?.guest).toBe("Elena Verna");
  });

  it("handles non-2xx error responses by throwing ApiError with detail", async () => {
    global.fetch = vi.fn().mockImplementation(async () => {
      return {
        ok: false,
        status: 503,
        statusText: "Service Unavailable",
        json: async () => ({ detail: "Database connection failed" }),
      } as unknown as Response;
    });

    await expect(
      api.sendMessage({
        sessionId: "",
        content: "Hello",
        history: [],
        model,
      }),
    ).rejects.toThrow("Database connection failed");
  });

  it("receives and returns artifact from sendMessage", async () => {
    global.fetch = vi.fn().mockImplementation(async () => {
      return {
        ok: true,
        json: async () => ({
          conversation_id: "c1111111-1111-1111-1111-111111111111",
          assistant_message_id: "msg-789",
          response_text: "Here is your essay:\n\n*[Generated Artifact: PLG Essay]*",
          citations: [],
          artifacts: [
            {
              id: "art-123",
              conversation_id: "c1111111-1111-1111-1111-111111111111",
              title: "PLG Essay",
              artifact_type: "markdown",
              content: "# PLG Essay\nFull essay markdown content.",
            },
          ],
        }),
      } as unknown as Response;
    });

    const result = await api.sendMessage({
      sessionId: "c1111111-1111-1111-1111-111111111111",
      content: "Write an essay about product-led growth",
      history: [],
      model,
    });

    expect(result.artifact).toBeDefined();
    expect(result.artifact?.id).toBe("art-123");
    expect(result.artifact?.title).toBe("PLG Essay");
    expect(result.artifact?.type).toBe("markdown");
    expect(result.artifact?.content).toBe("# PLG Essay\nFull essay markdown content.");
  });

  it("getMessages returns messages with attached artifact and done status", async () => {
    global.fetch = vi.fn().mockImplementation(async () => {
      return {
        ok: true,
        json: async () => [
          {
            id: "msg-1",
            role: "user",
            content: "Write an essay",
            created_at: "2026-10-10T12:00:00Z",
          },
          {
            id: "msg-2",
            role: "assistant",
            content: "Here is the essay",
            created_at: "2026-10-10T12:00:05Z",
            artifact: {
              id: "art-1",
              title: "Product-Led Growth",
              artifact_type: "markdown",
              content: "# Product-Led Growth",
            },
          },
        ],
      } as unknown as Response;
    });

    const msgs = await api.getMessages("c1111111-1111-1111-1111-111111111111");
    expect(msgs).toHaveLength(2);
    expect(msgs[1].status).toBe("done");
    expect(msgs[1].artifact).toBeDefined();
    expect(msgs[1].artifact?.title).toBe("Product-Led Growth");
  });

  it("getArtifacts and getArtifact fetch artifacts properly", async () => {
    global.fetch = vi.fn().mockImplementation(async (url: string) => {
      if (url.includes("/artifacts/art-1")) {
        return {
          ok: true,
          json: async () => ({
            id: "art-1",
            title: "Product-Led Growth",
            artifact_type: "markdown",
            content: "# Product-Led Growth\nDeep essay content...",
          }),
        } as unknown as Response;
      }
      return {
        ok: true,
        json: async () => [
          {
            id: "art-1",
            title: "Product-Led Growth",
            artifact_type: "markdown",
            content: "# Product-Led Growth\nDeep essay content...",
          },
        ],
      } as unknown as Response;
    });

    const list = await api.getArtifacts("c1111111-1111-1111-1111-111111111111");
    expect(list).toHaveLength(1);
    expect(list[0].id).toBe("art-1");

    const single = await api.getArtifact("art-1");
    expect(single.id).toBe("art-1");
    expect(single.title).toBe("Product-Led Growth");
  });

  it("getArtifact throws ApiError when artifact is not found", async () => {
    global.fetch = vi.fn().mockImplementation(async () => {
      return {
        ok: false,
        status: 404,
        statusText: "Not Found",
        json: async () => ({ detail: "Artifact not found" }),
      } as unknown as Response;
    });

    await expect(api.getArtifact("nonexistent-id")).rejects.toThrow("Artifact not found");
  });
});
