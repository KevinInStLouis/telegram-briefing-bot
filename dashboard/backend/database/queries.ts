import { sqlite } from "https://esm.town/v/stevekrouse/sqlite";
import { type Memory } from "../../shared/types.ts";

// toggle the commented out table name to switch between the demo and production tables
// const tableName = "memories";
const tableName = "memories_demo";

export async function getAllMemories(): Promise<Memory[]> {
  const result = await sqlite.execute(
    `SELECT id, date, text, createdBy, createdDate, tags FROM ${tableName}
     ORDER BY createdDate DESC`
  );

  // Ensure correct typing, especially for potential null values
  return result.rows.map((row) => ({
    id: row.id as string,
    date: row.date as string | null,
    text: row.text as string,
    createdBy: row.createdBy as string | null,
    createdDate: row.createdDate as number | null,
    tags: row.tags as string | null,
  })) as Memory[];
}

export async function createMemory(
  memory: Omit<Memory, "id">
): Promise<Memory> {
  // Use nanoid like in getWeather.ts
  const { nanoid } = await import("https://esm.sh/nanoid@5.0.5");
  const newId = nanoid(10); // Generate a shorter ID like in getWeather
  const createdDate = memory.createdDate ?? Date.now(); // Default to now if not provided

  await sqlite.execute(
    `INSERT INTO ${tableName} (id, date, text, createdBy, createdDate, tags)
     VALUES (?, ?, ?, ?, ?, ?)`,
    [
      newId,
      memory.date,
      memory.text,
      memory.createdBy || "dashboard", // Default creator
      createdDate,
      memory.tags,
    ]
  );

  return {
    ...memory,
    id: newId,
    createdDate,
  };
}

export async function updateMemory(
  id: string,
  memory: Partial<Omit<Memory, "id">>
): Promise<void> {
  const fields = Object.keys(memory).filter((key) => key !== "id");
  const values = Object.values(memory);

  if (fields.length === 0) {
    throw new Error("No fields provided for update");
  }

  const setClause = fields.map((field) => `${field} = ?`).join(", ");

  await sqlite.execute(`UPDATE ${tableName} SET ${setClause} WHERE id = ?`, [
    ...values,
    id,
  ]);
}

export async function deleteMemory(id: string): Promise<void> {
  await sqlite.execute(`DELETE FROM ${tableName} WHERE id = ?`, [id]);
}

