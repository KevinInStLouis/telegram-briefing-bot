/**
 * @jsxImportSource https://esm.sh/react@18.2.0
 */
import { blob } from "https://esm.town/v/std/blob";
import { readFile, serveFile } from "https://esm.town/v/std/utils@85-main/index.ts";
import { Hono } from "npm:hono";
import { type Memory } from "../shared/types.ts";
import { createMemory, deleteMemory, getAllMemories, updateMemory } from "./database/queries.ts";

const app = new Hono();

// Unwrap Hono errors to see original error details
app.onError((err, c) => {
  console.error("Error in Hono route:", err);
  // Optionally re-throw or return a custom error response
  // throw err;
  return c.json({ error: "Internal Server Error", details: err.message }, 500);
});

// --- API Routes for Memories ---

// GET /api/memories - Retrieve all memories
app.get("/api/memories", async (c) => {
  const memories = await getAllMemories();
  return c.json(memories);
});

// POST /api/memories - Create a new memory
app.post("/api/memories", async (c) => {
  const body = await c.req.json<Omit<Memory, "id">>();
  if (!body.text) {
    return c.json({ error: "Memory text cannot be empty" }, 400);
  }
  const newMemory = await createMemory(body);
  return c.json(newMemory, 201);
});

// PUT /api/memories/:id - Update an existing memory
app.put("/api/memories/:id", async (c) => {
  const id = c.req.param("id");
  const body = await c.req.json<Partial<Omit<Memory, "id">>>();

  if (Object.keys(body).length === 0) {
    return c.json({ error: "No update fields provided" }, 400);
  }

  try {
    await updateMemory(id, body);
    return c.json({ success: true });
  } catch (error) {
    // Handle cases like memory not found, if needed
    console.error("Error updating memory:", error);
    return c.json(
      { error: "Failed to update memory", details: error.message },
      500,
    );
  }
});

// DELETE /api/memories/:id - Delete a memory
app.delete("/api/memories/:id", async (c) => {
  const id = c.req.param("id");
  try {
    await deleteMemory(id);
    return c.json({ success: true });
  } catch (error) {
    console.error("Error deleting memory:", error);
    return c.json(
      { error: "Failed to delete memory", details: error.message },
      500,
    );
  }
});

// --- Blob Image Serving Routes ---

// GET /api/images/:filename - Serve images from blob storage
app.get("/api/images/:filename", async (c) => {
  const filename = c.req.param("filename");

  try {
    // Get image data from blob storage
    const imageData = await blob.get(filename);

    if (!imageData) {
      return c.json({ error: "Image not found" }, 404);
    }

    // Determine content type based on file extension
    let contentType = "application/octet-stream"; // Default
    if (filename.endsWith(".jpg") || filename.endsWith(".jpeg")) {
      contentType = "image/jpeg";
    } else if (filename.endsWith(".png")) {
      contentType = "image/png";
    } else if (filename.endsWith(".gif")) {
      contentType = "image/gif";
    } else if (filename.endsWith(".svg")) {
      contentType = "image/svg+xml";
    }

    // Return the image with appropriate headers
    return new Response(imageData, {
      headers: {
        "Content-Type": contentType,
        "Cache-Control": "public, max-age=3600", // Cache for 1 hour
      },
    });
  } catch (error) {
    console.error(`Error serving image ${filename}:`, error);
    return c.json(
      { error: "Failed to load image", details: error.message },
      500,
    );
  }
});

// --- Static File Serving ---

// Serve index.html at the root /
app.get("/", async (c) => {
  let html = await readFile("/dashboard/frontend/index.html", import.meta.url);
  // Inject view source link
  const viewSourceLink = import.meta.url.replace("esm.town", "val.town");
  const viewSourceTag =
    `<a href="${viewSourceLink}" target="_top" style="position: fixed; bottom: 10px; right: 10px; font-family: sans-serif; font-size: 12px; text-decoration: none; color: #888;">View Source</a>`;
  html = html.replace("</body>", `${viewSourceTag}</body>`);
  return c.html(html);
});

// Serve all /frontend files (except index.html) under /public
app.get("/public/*", (c) =>
  serveFile(
    c.req.path.replace("/public", "/dashboard/frontend"),
    import.meta.url,
  ));

// HTTP vals expect an exported "fetch handler"
export default app.fetch;
